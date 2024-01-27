from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.core.exceptions import (
    AzureError,
    HttpResponseError, 
    ResourceNotFoundError
)

from config import logger, subscription_id, location
from modules import create_nic_params, create_server_params


class Server:
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
        unique_webserver_name = f"{webserver_name}{server_number}"
        publicip_name = f"{unique_webserver_name}_ip"
        interface_name = f"{unique_webserver_name}_interface"

        publicip_info = self.create_publicip_address(publicip_name, group_name)

        try:
            self.create_nic(interface_name, group_name, vnet_name, 
                            subnet_name, unique_webserver_name, publicip_name)

            logger.info(f"Creating {unique_webserver_name} instance")
            vm_info = self.compute_client.virtual_machines.begin_create_or_update(
                group_name,
                unique_webserver_name,
                create_server_params(group_name, unique_webserver_name, interface_name, True)
            ).result()
        except ResourceNotFoundError as e:
            logger.error(f"There was an error creating a webserver's resource.")
            raise AzureError from e

        logger.info(f"{unique_webserver_name} deployment status: {vm_info.provisioning_state}")

        # Install and setup the webserver (IIS) feature
        self.install_iis(group_name, unique_webserver_name)

        self.print_webserver_ip_address(unique_webserver_name, publicip_info)    

    def create_publicip_address(self, publicip_name, group_name):
        """Create public IP address resource

        Args:
            publicip_name (str): Name of Public IP resource
            group_name (str): Name of resource group

        Returns:
            JSON: JSON data of Public IP resource
        """
        try:
            publicip_info = self.net_client.public_ip_addresses.begin_create_or_update(
                group_name,
                publicip_name,
                {
                    'sku': {
                        'name': 'Standard'
                    },
                    'location': location,
                    'public_ip_allocation_method': 'Static'
                }
            ).result()
            logger.info(f"{publicip_name} created successfully.")

            return publicip_info
        except HttpResponseError as e:
            logger.error(f"Public IP count limit may have been reached.")
            raise AzureError from e
    
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
            {
                'commandId': 'RunPowerShellScript',
                'script': [
                    "Install-WindowsFeature -name Web-Server -IncludeManagementTools",
                    "Remove-item 'C:\\inetpub\\wwwroot\\iisstart.htm'", 
                    "Add-Content -Path 'C:\\inetpub\\wwwroot\\iisstart.htm' \
                        -Value $('Hello World from ' + $env:computername)"
                ]
            }
        )
    
    def print_webserver_ip_address(self, server_name, publicip_info):
        """Print the webserver's IP address

        Args:
            server_name (str): Name of server
            publicip_info (JSON): JSON data of Public IP resource
        """
        if publicip_info:
            print(f'\n\nLogin information for {server_name}')
            print('-------------------------------------------')
            print(f'Public IP      - {publicip_info.ip_address}\n')
        else:
            logger.error(f"Cannot retrieve IP address for {server_name} at this time.")


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
            raise AzureError from e