from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
from modules import (
    create_dbserver_parameters, 
    create_publicip_parameters, 
    create_nic_parameters, 
    create_webserver_parameters, 
    run_command_parameters
)

class WebServer():
    def __init__(self, subscription_id, token_credential, deployment_name) -> None:
        """Initiate the WebServer class properties
        """

        # Creating management clients
        self.rss_client = ResourceManagementClient(token_credential, subscription_id)
        self.net_client = NetworkManagementClient(token_credential, subscription_id)
        self.compute_client = ComputeManagementClient(token_credential, subscription_id)

        # Declare instance variables which serve as global variables within the class
        self.location = "southafricanorth"
        self.subnet_name = "subnet0"
        self.group_name = deployment_name
        self.subscription_id = subscription_id
        self.network_name = f"{self.group_name}_network"
        self.nsg_name = f"{self.group_name}_nsg"

    def create_webserver(self, server_number):
        """Create the webserver instance with its dependencies.
        """

        interface_name = f"webserver{server_number}_interface"
        publicip_name = f"webserver{server_number}_publicip"
        vm_name = f"{self.group_name}_webserver{server_number}"

        if server_number == 0:
            # Creating resource group
            print("Creating resoure group")
            self.rss_client.resource_groups.create_or_update(
                self.group_name, {'location': self.location})
            
            # Creating the subnet's NSG group
            print("Creating NSG group")
            nsg_info = self.net_client.network_security_groups.begin_create_or_update(
                self.group_name,
                self.nsg_name,
                {
                    "location": self.location,
                    "securityRules": [{
                        "name": "lb-HTTP-rule",
                        "protocol": "Tcp",
                        "sourcePortRange": "*",
                        "destinationPortRange": "80",
                        "sourceAddressPrefix": "*",
                        "destinationAddressPrefix": "*",
                        "access": "Allow",
                        "priority": 100,
                        "direction": "Inbound"
                    },
                    {
                        "name": "RDP-access-rule",
                        "protocol": "Tcp",
                        "sourcePortRange": "*",
                        "destinationPortRange": "3389",
                        "sourceAddressPrefix": "*",
                        "destinationAddressPrefix": "*",
                        "access": "Allow",
                        "priority": 110,
                        "direction": "Inbound"
                    }]
                }
            ).result()

            # Creating VNet
            print("Creating VNet")
            self.net_client.virtual_networks.begin_create_or_update(
                self.group_name,
                self.network_name,
                {
                    'location': self.location,
                    'address_space': {
                        'address_prefixes': ['10.0.0.0/16']
                    }
                }
            ).wait()

            # Creating subnet within VNet
            print("Creating subnet within VNet")
            self.net_client.subnets.begin_create_or_update(
               self.group_name,
               self.network_name,
               self.subnet_name,
               {
                   'address_prefix': '10.0.0.0/24',
                   "networkSecurityGroup": {
                       "id": nsg_info.id
                    }
                }
            ).wait()

        # Creating websever's public IP address
        print(f"Creating webserver{server_number}'s IP address")
        publicip_info = self.net_client.public_ip_addresses.begin_create_or_update(
            self.group_name,
            publicip_name,
            create_publicip_parameters(self.location)
        ).result()
        
        # Creating webserver's NIC interface
        print(f"Creating webserver{server_number}'s NIC interface")
        self.net_client.network_interfaces.begin_create_or_update(
            self.group_name,
            interface_name,
            create_nic_parameters(self.location, self.subscription_id, self.group_name, self.subnet_name, server_number)
        )

        # Creating Webserver
        print(f"Creating webserver{server_number} instance")
        vm_info = self.compute_client.virtual_machines.begin_create_or_update(
            self.group_name,
            vm_name,
            create_webserver_parameters(self.location, self.subscription_id, self.group_name, interface_name)
        ).result()

        # Print out webserver deployment status
        print(f"Webserver{server_number} deployment status: {vm_info.provisioning_state}")

        # Install and setup the webserver (IIS) feature
        print(f"Setting up IIS on webserver{server_number}")
        self.compute_client.virtual_machines.begin_run_command(
            self.group_name,
            vm_name,
            run_command_parameters()
        ).wait()

        # Print webserver's login information
        self.get_login_info_for_webserver(server_number, publicip_info)
    
    def add_webserver_to_lb_backend_pool(self, number_of_backpool_servers):
        """ Updates a webserver's NIC to add the webserver to the backend pool of the load balancer
        """
        backend_address_pools = [{
            "id": f"/subscriptions/{self.subscription_id}/resourceGroups/{self.group_name}/providers/Microsoft.Network/loadBalancers/{self.group_name}_lb/backendAddressPools/{self.group_name}_lb_addr_pool"
        }]
        
        for server_number in range(number_of_backpool_servers):
            nic_parameters = create_nic_parameters(self.location, self.subscription_id, self.group_name, self.subnet_name, server_number)
            nic_parameters['ip_configurations'][0]['load_balancer_backend_address_pools'] = backend_address_pools

            self.net_client.network_interfaces.begin_create_or_update(
                self.group_name,
                f'webserver{server_number}_interface',
                nic_parameters
            )

            print(f"Added webserver{server_number} to backend pool")
    
    def get_login_info_for_webserver(self, server_number, publicip_info):
        """Print on the console the connection information for a given VM.
        """
        print(f'\n\nLogin information for webserver{server_number}')
        print('-------------------------------------------')
        print(f'Public IP      - {publicip_info.ip_address}')
        print('Username       - Azureuser')
        print('Password       - Azureuser123\n\n')

        return [[f"webserver{server_number}", f"{publicip_info.ip_address}", "Azureuser", "Azureuser123"]]
        


class DBServer(WebServer):
    def __init__(self, subscription_id, token_credential, deployment_name):
        """Initiate the DBServer class properties
        """        
        # Inherits properties from WebServer class
        super().__init__(subscription_id, token_credential, deployment_name)
    
    def create_dbserver(self):
        """Create the dbserver instance with its dependencies.
        """

        interface_name = 'dbserver_interface'
        vm_name = f"{self.group_name}_dbserver"
        publicip_name = "dbserver_publicip"

        # Creating dbserver's IP address
        print("Creating dbserver's IP address")
        self.net_client.public_ip_addresses.begin_create_or_update(
            self.group_name,
            publicip_name,
            create_publicip_parameters(self.location)
        ).wait()

        # Creating the dbserver's NIC interface
        print("Creating the dbserver's NIC interface")
        self.net_client.network_interfaces.begin_create_or_update(
            self.group_name,
            interface_name,
            create_nic_parameters(self.location, self.subscription_id, self.group_name, self.subnet_name)
        )

        # Creating the Database Server
        print("Creating the Database server instance")
        vm_info = self.compute_client.virtual_machines.begin_create_or_update(
            self.group_name,
            vm_name,
            create_dbserver_parameters(self.location, self.subscription_id, self.group_name, interface_name)
        ).result()

        print(f"Database server deployment status: {vm_info.provisioning_state}")

class LoadBalancer(WebServer):
    def __init__(self, subscription_id, token_credential, deployment_name):
        super().__init__(subscription_id, token_credential, deployment_name)
    
    def create_lb(self):
        lb_name = f"{self.group_name}_lb"
        pip_name = f"{lb_name}_publicip"
        fip_name = f"{lb_name}_frontendip_name"
        address_pool_name = f"{lb_name}_addr_pool"
        probe_name = "lb_healthprobe"
        lb_rule_name = f"{lb_name}_rule"


        pub_ip_info = self.net_client.public_ip_addresses.begin_create_or_update(
            self.group_name,
            pip_name,
            create_publicip_parameters(self.location)
        ).result()

        frontend_ip_configs = [{
            'name': fip_name,
            'private_ip_allocation_method': 'Dynamic',
            'public_ip_address': {
                'id': pub_ip_info.id
            }
        }]

        backend_address_pools = [{
        'name': address_pool_name}]

        probes = [{
            'name': probe_name,
            'protocol': 'Tcp',
            'port': 80,
            'interval_in_seconds': 5,
            'number_of_probes': 1,
            #'request_path': '/'
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
                'id': f'/subscriptions/{self.subscription_id}/resourceGroups/{self.group_name}/providers/Microsoft.Network/loadBalancers/{lb_name}/frontendIPConfigurations/{fip_name}'
            },
            'backend_address_pool': {
                'id': f'/subscriptions/{self.subscription_id}/resourceGroups/{self.group_name}/providers/Microsoft.Network/loadBalancers/{lb_name}/backendAddressPools/{address_pool_name}'
            },
            'probe': {
                'id': f'/subscriptions/{self.subscription_id}/resourceGroups/{self.group_name}/providers/Microsoft.Network/loadBalancers/{lb_name}/probes/{probe_name}'
            }
        }]


        lb_creation_result = self.net_client.load_balancers.begin_create_or_update(
            self.group_name,
            lb_name,
            {
                'sku': {
                    'name': 'Standard'
                },
                'location': self.location,
                'frontend_ip_configurations': frontend_ip_configs,
                'backend_address_pools': backend_address_pools,
                'probes': probes,
                'load_balancing_rules': load_balancing_rules
            }
        ).result()

        print(f'Creating LB: {lb_creation_result.provisioning_state}')