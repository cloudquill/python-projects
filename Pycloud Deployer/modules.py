def create_publicip_parameters(location):
    return {
        'sku': {
            'name': 'Standard'
        },
        'location': location,
        'public_ip_allocation_method': 'Static'
    }

def create_nic_parameters(location, subscription_id, group_name, subnet_name, server_number=''):
    if server_number == '':
        publicip_name = 'dbserver_publicip'
    else:
        publicip_name = f'webserver{server_number}_publicip'

    return {
        'location': location,
        'ip_configurations': [{
            'name': 'MyIpConfig',
            'subnet': {
                'id': f"/subscriptions/{subscription_id}/resourceGroups/{group_name}/providers/Microsoft.Network/virtualNetworks/{group_name}_network/subnets/{subnet_name}"
            },
            'public_ip_address': {
                'id': f"/subscriptions/{subscription_id}/resourceGroups/{group_name}/providers/Microsoft.Network/publicIPAddresses/{publicip_name}"
            }
        }]
    }

def create_webserver_parameters(location, subscription_id, group_name, interface_name):
    return {
        'location': location,
        'hardware_profile': {
            'vm_size': 'Standard_B1s'
        },
        'storage_profile': {
            'image_reference': {
                'sku': '2019-Datacenter',
                'publisher': 'MicrosoftWindowsServer',
                'version': 'latest',
                'offer': 'WindowsServer'
            },
            'os_disk': {
                'caching': 'ReadWrite',
                'managed_disk': {
                    'storage_account_type': 'Standard_LRS'
                },
                'create_option': 'FromImage'
            }
        },
        'os_profile': {
            'admin_username': 'testuser',
            'computer_name': 'Azureuser',
            'admin_password': 'Azureuser123',
            'windows_configuration': {
                'enable_automatic_updates': True
            }
        },
        'network_profile': {
            'network_interfaces': [{
                "id": "/subscriptions/" + subscription_id + "/resourceGroups/" + group_name + "/providers/Microsoft.Network/networkInterfaces/" + interface_name + "",
                "primary": True
            }]
        }
    }

def create_dbserver_parameters(location, subscription_id, group_name, interface_name):
    return {
        'location': location,
        'hardware_profile': {
            'vm_size': 'Standard_B1s'
        },
        'storage_profile': {
            'image_reference': {
                'sku': 'sqldev-gen2',
                'publisher': 'MicrosoftSQLServer',
                'version': 'latest',
                'offer': 'sql2019-ws2019'
            },
            'os_disk': {
                'caching': 'ReadWrite',
                'managed_disk': {
                    'storage_account_type': 'Standard_LRS'
                },
                'create_option': 'FromImage'
            }
        },
        'os_profile': {
            'admin_username': 'testuser',
            'computer_name': 'Azureuser',
            'admin_password': 'Azureuser123',
            'windows_configuration': {
                'enable_automatic_updates': True
            }
        },
        'network_profile': {
            'network_interfaces': [{
                "id": "/subscriptions/" + subscription_id + "/resourceGroups/" + group_name + "/providers/Microsoft.Network/networkInterfaces/" + interface_name + "",
                "primary": True
            }]
        }
    }

def run_command_parameters():
    return {
        'commandId': 'RunPowerShellScript',
        'script': [
            "Install-WindowsFeature -name Web-Server -IncludeManagementTools",
            "Remove-item 'C:\\inetpub\\wwwroot\\iisstart.htm'", 
            "Add-Content -Path 'C:\\inetpub\\wwwroot\\iisstart.htm' -Value $('Hello World from ' + $env:computername)"
        ]
    }

def backpool_publicip_addresses_parameter(subscription_id, group_name, number_of_backpool_servers):
    items = []
    for server_number in range(number_of_backpool_servers):
        item = f"{{'id': f'/subscriptions/{subscription_id}/resourceGroups/{group_name}/providers/Microsoft.Network/publicIPAddresses/webserver{server_number}_publicip'}}"
        items.append(item)

    result = ', '.join(items)
    return result