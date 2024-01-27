import uuid

from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.core.exceptions import (
    AzureError,
    ResourceExistsError, 
    HttpResponseError, 
    ResourceNotFoundError
)

from server_class import Server, DBServer
from load_balancer_class import LoadBalancer
from config import logger, location, subscription_id
from modules import validate_group_name


class Infrastructure:
    """Set up the support infrastructure and deploy the resources, retrieve
    information about the deployment and tear down a deployment

    Methods:
        create_infrastructure(): Create the support infrastructure.
        info(): Display infrastructure information
        delete(): Delete a deployment
        tier2(): Deploy a tier 2 infrastructure of webservers and dbservers
        tier3(): Deploy a 3-tier infrastructure of webservers, dbservers and load balancers
        create_resource_group(): Create resource group
        create_nsg_group(): Create NSG group
        create_vnet(): Create a VNet
        create_subnet(): Create a subnet
    """
    def __init__(self, token_credential):
        """Initiate the class properties

        Args:
            token_credential (DefaultAzureCredential): Instance of the DefaultAzureCredential class
        """
        self.rss_client = ResourceManagementClient(token_credential, subscription_id)
        self.net_client = NetworkManagementClient(token_credential, subscription_id)
        self.compute_client = ComputeManagementClient(token_credential, subscription_id)

        self.webserver_provisioner = Server(token_credential)
        self.dbserver_provisioner = DBServer(token_credential)
        self.lb_provisioner = LoadBalancer(token_credential)
    
    def create_infrastructure(self, group_name, vnet_name, subnet_name, 
                              nsg_name, isTier2):
        """Create the support infrastructure

        Args:
            group_name (str): Name of the resource group
            vnet_name (str): Name of the VNet
            subnet_name (str): Name of the subnet
            nsg_name (str): Name of the NSG group
        """
        self.create_vnet(vnet_name, group_name)

        nsg_info = self.create_nsg_group(nsg_name, group_name, isTier2)

        # Likely error if there was a problem deploying the NSG and nothing was 
        # returned to the nsg_info variable
        if nsg_info:
            self.create_subnet(subnet_name, group_name, vnet_name, nsg_info.id)
        else:
            raise AzureError("Could not retrieve NSG information, hence cannot create subnet")

    def info(self, group_name):
        """Display infrastructure information

        Args:
            group_name (str): Name of resource group
        """
        try:
            # Check what tier it is by determining the presence of a load balancer
            check_lb = list(self.net_client.load_balancers.list(group_name))
            tier = 2 if not check_lb else 3

            # Retrieve data objects of all VMs and extract their names into a list
            vms_obj_list = list(self.compute_client.virtual_machines.list(group_name))
            vm_names = []
            for i in vms_obj_list:
                vm_names.append(i.name)
            
            # Retrieve data objects of all Public IP resources and extract both names
            # and IP addresses. The last three characters of each name "_ip" are spliced
            # off which leaves the names of the compute devices that own the resource
            # (due to name construction)
            public_ip_obj_list = list(self.net_client.public_ip_addresses.list(group_name))
            ip_names_and_address = []
            for i in public_ip_obj_list:
                item = (i.name[0:-3], i.ip_address)
                ip_names_and_address.append(item)

            print("Infrastructure details")
            print('-------------------------')
            print(f"Tier: {tier}")

            # The IP resource names are each compared to names in the VMs list and printed 
            # out with their associated IP addresses. This avoids printing out the the load
            # balancer resource and IP address
            for name, ip in ip_names_and_address:
                if name in vm_names:
                    print(name, ":", ip)
        except ResourceNotFoundError as e:
            logger.error(f"Resource Group {group_name} not found.")
        except HttpResponseError as e:
            logger.error(f"Unexpected response from Azure: {str(e)}")

    def delete(self, group_name):
        """Delete a deployment

        Args:
            group_name (str): Name of the resource group
        """
        try:
            logger.info(f"Deleting {group_name}...")
            self.rss_client.resource_groups.begin_delete(group_name).wait()
            logger.info("Deployment deleted successfully.")
        except ResourceNotFoundError:
            logger.error(f"Resource Group {group_name} not found.")

    def tier2(self, group_name, vnet_name, subnet_name, 
              nsg_name, webserver_name, dbserver_name):
        """Deploy a tier 2 infrastructure of webservers and dbservers
        
        Args:
            group_name (str): Name of the resource group
            vnet_name (str): Name of the VNet
            subnet_name (str): Name of the subnet
            nsg_name (str): Name of the NSG group
            webserver_name (str): Prefix for webserver's name
            dbserver_name (str): Name of DBserver
        """
        self.create_infrastructure(group_name, vnet_name, 
                                   subnet_name, nsg_name, True)

        self.webserver_provisioner.create_webserver(group_name, vnet_name,
                                                    subnet_name, webserver_name)

        self.dbserver_provisioner.create_dbserver(group_name, vnet_name, 
                                                  subnet_name, dbserver_name) 

    def tier3(self, group_name, vnet_name, subnet_name, nsg_name,
              webserver_name, dbserver_name, number_of_webservers):
        """Deploy a 3-tier infrastructure of webservers, dbservers and load balancers
        
        Args:
            group_name (str): Name of the resource group
            vnet_name (str): Name of the VNet
            subnet_name (str): Name of the subnet
            nsg_name (str): Name of the NSG group
            webserver_name (str): Prefix for webserver's name
            dbserver_name (str): Name of DBserver
            number_of_webservers (int): Number of webservers to deploy
        """
        self.create_infrastructure(group_name, vnet_name, 
                                    subnet_name, nsg_name, False)

        # Rather than taking name inputs for each server, add server numbers to the
        # webserver name to differentiate them
        for server_number in range(number_of_webservers):
            self.webserver_provisioner.create_webserver(group_name, vnet_name, subnet_name,
                                                        webserver_name, server_number)
        
        self.dbserver_provisioner.create_dbserver(group_name, vnet_name, 
                                                  subnet_name, dbserver_name)

        self.lb_provisioner.create_lb(group_name)

        self.lb_provisioner.add_webserver_to_backend(group_name, vnet_name, subnet_name,
                                                     webserver_name, number_of_webservers)

    def create_resource_group(self, group_name):
        """Create resource group

        Args:
            group_name (str): Name of resource group
        
        Returns:
            Resource group name
        """
        logger.info("Creating resource group")

        # Check if resource group name exists. If it does, a unique ID is added
        # to the name. This method is then recalled.
        if self.rss_client.resource_groups.check_existence(group_name):
            logger.info(f"The resource group {group_name} already exists.")

            # uuid generates random 128-bit values consisting of alphanumeric 
            # characters and '-'. It is used to generate unique ids to be attached 
            # to existing group names. [:5] extracts the first five characters.
            group_name = f"{group_name}-{str(uuid.uuid4())[:5]}"
            logger.info(f"Changed group name to {group_name}")
            self.create_resource_group(group_name)
        
        group_name = validate_group_name(group_name)
        self.rss_client.resource_groups.create_or_update(
            group_name, {'location': location})
        
        logger.info(f"Resource group {group_name} created successfully")
        return group_name

    def create_nsg_group(self, nsg_name, group_name, isTier2):
        """Create NSG group

        Args:
            nsg_name (str): Name of NSG group
            group_name (str): Name of resource group
            isTier2 (bool): if tier 2 or 3 infrastructure

        Returns:
            JSON: JSON data of NSG group
        """
        lb_http_rule = {
            "name": "lb-HTTP-rule",
            "protocol": "Tcp",
            "sourcePortRange": "*",
            "destinationPortRange": "80",
            "sourceAddressPrefix": "*",
            "destinationAddressPrefix": "*",
            "access": "Allow",
            "priority": 100,
            "direction": "Inbound"
        }

        rdp_access_rule = {
            "name": "RDP-access-rule",
            "protocol": "Tcp",
            "sourcePortRange": "*",
            "destinationPortRange": "3389",
            "sourceAddressPrefix": "*",
            "destinationAddressPrefix": "*",
            "access": "Allow",
            "priority": 110,
            "direction": "Inbound"
        }

        try:
            logger.info("Creating NSG group")
            
            # Creates the group with only the rdp-access rule if Tier 2 but otherwise adds
            # the lb-http-rule for traffic to flow from load balancer to webservers.
            nsg_info = self.net_client.network_security_groups.begin_create_or_update(
                group_name, 
                nsg_name,
                {
                    "location": location,
                    "securityRules": 
                        [rdp_access_rule] if isTier2 else [rdp_access_rule, lb_http_rule]
                }).result()
            
            logger.info("NSG created successfully.")
            return nsg_info
        except HttpResponseError as e:
            logger.error("NSG information could not be created.")
            raise AzureError from e
 
    def create_vnet(self, vnet_name, group_name):
        """Create a VNet

        Args:
            vnet_name (str): Name of the VNet
            group_name (str): Name of resource group
        """
        logger.info("Creating VNet")

        try:
            self.net_client.virtual_networks.begin_create_or_update(
                group_name,
                vnet_name,
                {
                    'location': location,
                    'address_space': {
                        'address_prefixes': ['10.0.0.0/16']
                    }
                }
            ).wait()

            logger.info("VNet created successfuly")
        except (ResourceExistsError, HttpResponseError) as e:
            logger.error(f"Possible conflicting address space error.")
            raise AzureError from e
    
    def create_subnet(self, subnet_name, group_name, vnet_name, nsg_id):
        """Create a subnet

        Args:
            subnet_name (str): Name of subnet
            group_name (str): Name of resource group
            vnet_name (str): Name of VNet
            nsg_id (str): NSG resource ID
        """
        logger.info("Creating subnet within VNet")

        try:
            self.net_client.subnets.begin_create_or_update(
                group_name,
                vnet_name,
                subnet_name,
                {
                    'address_prefix': '10.0.0.0/24',
                "networkSecurityGroup": {
                    "id": nsg_id
                    }
                }
            ).wait()

            logger.info(f"Subnet {subnet_name} created successfully.")
        except (ResourceExistsError, HttpResponseError) as e:
            logger.error(f"Possible conflicting address space error.")
            raise AzureError from e