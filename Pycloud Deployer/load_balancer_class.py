from azure.core.exceptions import AzureError, HttpResponseError

from server_class import Server
from config import logger, location, subscription_id
from modules import create_nic_params


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

        pub_ip_info = self.create_publicip_address(lb_ip_name, group_name)

        if pub_ip_info:
            frontend_ip_configs = [{
                'name': fip_name,
                'private_ip_allocation_method': 'Dynamic',
                'public_ip_address': {
                    'id': pub_ip_info.id
                }
            }]
        else:
            raise AzureError("Could not retrieve Public IP address information for LB")

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
        # Retrieve LB backpool address ID
        address_pool_id = self.net_client.load_balancer_backend_address_pools.get(
            group_name, 
            f"{group_name}_lb", 
            f"{group_name}_lb_addr_pool").id
        
        if address_pool_id:
            backend_address_pools = [{
                "id": address_pool_id
            }]
        else:
            raise AzureError("Could not retrieve LB backpool address ID.")
        
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

                logger.info(f"Added {unique_webserver_name} to backend pool")
            except HttpResponseError as e:
                logger.error(f"Error adding {unique_webserver_name} to backend.")
                raise AzureError from e