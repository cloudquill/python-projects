from config import logger, location, subscription_id
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
from modules import (
    create_publicip_params, 
    create_nic_params,
    create_server_params, 
    run_command_params,
    validate_group_name
)
from azure.core.exceptions import (
    ResourceExistsError, 
    HttpResponseError, 
    ResourceNotFoundError
)


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
        try:
            self.create_subnet(subnet_name, group_name, vnet_name, nsg_info.id)
        except UnboundLocalError as e:
            logger.error(f"Empty nsg_info variable: {str(e)}")    

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
        except ResourceNotFoundError:
            logger.error(f"Resource Group {group_name} not found.")

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
        logger.info("Creating resoure group")

        # Check if resource group exists and prompts the user for a name change, 
        # if neccessary. Although an existing resource group can be used, it is 
        # just to ensure the user knows about it.
        if self.rss_client.resource_groups.check_existence(group_name):
            logger.error(f"The resource group {group_name} already exists.")
            
            choice = input("Press Y to change group name or any other key to continue: ")
            if choice.lower() == "y":
                group_name = validate_group_name("")
                logger.info("Group name changed.")
                self.create_resource_group(group_name)
        else:
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
            logger.error(f"Possible conflicting address space error: {str(e)}")
            SystemExit(1)
    
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
            logger.error(f"Possible conflicting address space error: {str(e)}")
            SystemExit(1)
    

class Server():
    """Create a Windows server

    Methods:
        create_webserver(): Create the webserver instance & its dependencies
        create_publicip_address(): Create public IP address resource
        create_nic(): Create a server's NIC interface
        install_iis(): Install the IIS feature on Windows servers
        print_webserver_ip_address(): Print the webserver's IP address
    """
    def __init__(self, token_credential):
        """Initiate the Server class properties

        Args:
            token_credential (DefaultAzureCredential): Instance of the DefaultAzureCredential class
        """
        self.net_client = NetworkManagementClient(token_credential, subscription_id)
        self.compute_client = ComputeManagementClient(token_credential, subscription_id)

    def create_webserver(self, group_name, vnet_name, subnet_name,
                         webserver_name, server_number=0):
        """Create the webserver instance & its dependencies

        Args:
            group_name (str): Name of the resource group
            webserver_name (str): Prefix for webserver's name
            vnet_name (str): Name of the VNet
            subnet_name (str): Name of the subnet
            server_number (int, optional): Suffix for webserver's name. Defaults to 0.
        """
        webserver_name_suffix = f"{webserver_name}{server_number}"
        publicip_name = f"{webserver_name_suffix}_ip"
        interface_name = f"{webserver_name_suffix}_interface"

        publicip_info = self.create_publicip_address(publicip_name, group_name)

        try:
            self.create_nic(interface_name, group_name, vnet_name, 
                            subnet_name, webserver_name_suffix, publicip_name)

            logger.info(f"Creating {webserver_name_suffix} instance")
            vm_info = self.compute_client.virtual_machines.begin_create_or_update(
                group_name,
                webserver_name_suffix,
                create_server_params(group_name, webserver_name_suffix, interface_name, True)
            ).result()
        except ResourceNotFoundError as e:
            logger.error(f"There may have been an error creating a webserver's dependent resource: {str(e)}")
            SystemExit(1)

        logger.info(f"{webserver_name_suffix} deployment status: {vm_info.provisioning_state}")

        # Install and setup the webserver (IIS) feature
        self.install_iis(group_name, webserver_name_suffix)

        self.print_webserver_ip_address(webserver_name_suffix, publicip_info)    

    def create_publicip_address(self, publicip_name, group_name):
        """Create public IP address resource

        Args:
            publicip_name (str): Name of Public IP resource
            group_name (str): Name of resource group

        Returns:
            JSON: JSON data of Public IP resource
        """
        # Likely Public IP Count Limit reached error
        try:
            publicip_info = self.net_client.public_ip_addresses.begin_create_or_update(
                group_name,
                publicip_name,
                create_publicip_params()
            ).result()
            logger.info(f"{publicip_name} created successfully.")

            return publicip_info
        except HttpResponseError as e:
            logger.error(f"Public IP count limit may have been reached: {str(e)}")
    
    def create_nic(self, interface_name, group_name, vnet_name, subnet_name, 
                   server_name, publicip_name=''):
        """Create a server's NIC interface

        Args:
            interface_name (str): Name of NIC interface
            group_name (str): Name of resource group
            vnet_name (str): Name of VNet
            subnet_name (str): Name of subnet
            server_name (str): Name of server
            publicip_name (str, optional): Name of Public IP resource. Defaults to ''
        """
        
        logger.info(f"Creating {server_name}'s NIC interface")
        self.net_client.network_interfaces.begin_create_or_update(
            group_name,
            interface_name,
            create_nic_params(group_name, vnet_name, subnet_name, publicip_name)
        )
        logger.info(f"NIC {interface_name} created successfully.")
    
    def install_iis(self, group_name, webserver_name):
        """Install the IIS feature on Windows servers

        Args:
            group_name (_type_): Name of resource group
            webserver_name (str): Name of webserver
        """
        logger.info(f"Setting up IIS on {webserver_name}")
        
        self.compute_client.virtual_machines.begin_run_command(
            group_name,
            webserver_name,
            run_command_params()
        )
    
    def print_webserver_ip_address(self, server_name, publicip_info):
        """Print the webserver's IP address

        Args:
            server_name (str): Name of server
            publicip_info (JSON): JSON data of Public IP resource
        """
        print(f'\n\nLogin information for {server_name}')
        print('-------------------------------------------')
        print(f'Public IP      - {publicip_info.ip_address}\n')    


class DBServer(Server):
    """Create a Windows SQL server

    Args:
        Server (class): parent class

    Methods:
        create_dbserver(): Create the dbserver instance & its dependencies
    """
    def __init__(self, token_credential):
        """Initiates the DBServer class

        Args:
            token_credential (DefaultAzureCredential): Instance of the DefaultAzureCredential class
        """
        # Inherits the management clients and methods from Server class
        super().__init__(token_credential)
    
    def create_dbserver(self, group_name, vnet_name, subnet_name, dbserver_name):
        """Create the dbserver instance & its dependencies

        Args:
            group_name (str): Name of the resource group
            vnet_name (str): Name of the VNet
            subnet_name (str): Name of the subnet
            dbserver_name (str): Prefix for dbserver's name
        """
        interface_name = f'{dbserver_name}_interface'

        try:
            self.create_nic(interface_name, group_name, vnet_name, 
                            subnet_name, dbserver_name)

            logger.info("Creating the Database server instance")
            vm_info = self.compute_client.virtual_machines.begin_create_or_update(
                group_name,
                dbserver_name,
                create_server_params(group_name, dbserver_name, interface_name, False)
            ).result()

            logger.info(f"Database server deployment status: {vm_info.provisioning_state}")
        except ResourceNotFoundError as e:
            logger.error(f"There may have been an error creating the dbserver's resource: {str(e)}")
            SystemExit(1)


class LoadBalancer(Server):
    """Set up a load balancer and add backend servers

    Args:
        Server (class): parent class

    Methods:
        create_lb(): Create a LB
        add_webserver_to_backend(): Add webservers to LB backend pool

    """
    def __init__(self, token_credential):
        """Initiates the Load Balancer class

        Args:
            token_credential (DefaultAzureCredential): Instance of the DefaultAzureCredential class
        """
        # Inherits the management clients and methods from Server class
        super().__init__(token_credential)
    
    def create_lb(self, group_name):
        """Create a LB

        Args:
            group_name (str): Name of resource group
        """
        lb_name = f"{group_name}_lb"
        lb_ip_name = f"{lb_name}_ip"
        fip_name = f"{lb_name}_fip"
        address_pool_name = f"{lb_name}_addr_pool"
        probe_name = "lb_healthprobe"
        lb_rule_name = f"{lb_name}_rule"

        backend_address_pools = [{
            'name': address_pool_name}]

        probes = [{
            'name': probe_name,
            'protocol': 'Tcp',
            'port': 80,
            'interval_in_seconds': 5,
            'number_of_probes': 2
        }]

        load_balancing_rules = [{
            'name': lb_rule_name,
            'protocol': 'tcp',
            'frontend_port': 80,
            'backend_port': 80,
            'idle_timeout_in_minutes': 4,
            'enable_floating_ip': False,
            'load_distribution': 'Default',
            'frontend_ip_configuration': {
                'id': f'/subscriptions/{subscription_id}/resourceGroups/{group_name}/providers/Microsoft.Network/loadBalancers/{lb_name}/frontendIPConfigurations/{fip_name}'
            },
            'backend_address_pool': {
                'id': f'/subscriptions/{subscription_id}/resourceGroups/{group_name}/providers/Microsoft.Network/loadBalancers/{lb_name}/backendAddressPools/{address_pool_name}'
            },
            'probe': {
                'id': f'/subscriptions/{subscription_id}/resourceGroups/{group_name}/providers/Microsoft.Network/loadBalancers/{lb_name}/probes/{probe_name}'
            }
        }]

        try:
            pub_ip_info = self.create_publicip_address(lb_ip_name, group_name)

            frontend_ip_configs = [{
                'name': fip_name,
                'private_ip_allocation_method': 'Dynamic',
                'public_ip_address': {
                    'id': pub_ip_info.id
                }
            }]

            logger.info(f"Creating {lb_name} instance")
            lb_creation_result = self.net_client.load_balancers.begin_create_or_update(
                group_name,
                lb_name,
                {
                    'sku': {
                        'name': 'Standard'
                    },
                    'location': location,
                    'frontend_ip_configurations': frontend_ip_configs,
                    'backend_address_pools': backend_address_pools,
                    'probes': probes,
                    'load_balancing_rules': load_balancing_rules
                }
            ).result()

            logger.info(f'{lb_name} deployment status: {lb_creation_result.provisioning_state}')
        except ResourceNotFoundError as e:
            logger.error(f"There may have been an error creating the LB dependent resource: {str(e)}")
            SystemExit(1)
        except UnboundLocalError as e:
            logger.error(f"A LB variable was empty due to nothing being returned to it: {str(e)}")
            SystemExit(1)

    def add_webserver_to_backend(self, group_name, vnet_name, subnet_name, 
                                 webserver_name, number_of_backend_servers):
        """Add webservers to LB backend pool

        Args:
            group_name (str): Name of resource group
            vnet_name (str): Name of VNet
            subnet_name (str): Name of subnet
            webserver_name (str): Name of webserver
            number_of_backpool_servers (int): Total number of webservers deployed
        """
        try: 
            # Retrieve LB backpool address ID
            address_pool_id = self.net_client.load_balancer_backend_address_pools.get(
                group_name, 
                f"{group_name}_lb", 
                f"{group_name}_lb_addr_pool").id
            
            backend_address_pools = [{
                "id": address_pool_id
            }]
            
            # Insert the LB backpool address ID to each webserver's NIC and update 
            # the webserver to add it to the LB backend
            for server_number in range(number_of_backend_servers):
                unique_webserver_name = f"{webserver_name}{server_number}"
                interface_name = f"{unique_webserver_name}_interface"
                publicip_name = f"{unique_webserver_name}_ip"

                nic_params = create_nic_params(group_name, vnet_name, subnet_name, 
                                               publicip_name)
                ip_configs = nic_params["ip_configurations"][0]
                ip_configs['load_balancer_backend_address_pools'] = backend_address_pools

                logger.info(f"Adding {unique_webserver_name} to backend pool")

                try:
                    self.net_client.network_interfaces.begin_create_or_update(
                        group_name,
                        interface_name,
                        nic_params
                    )
                except HttpResponseError as e:
                    logger.error(f"Error adding {unique_webserver_name}: {str(e)}")

                logger.info(f"Added {unique_webserver_name} to backend pool")
        except ResourceNotFoundError as e:
            logger.error(f"A referenced resource was not found: {str(e)}")