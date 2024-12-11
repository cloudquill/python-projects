import re
import getpass

from config import location, subscription_id, max_name_limit, min_name_limit


def validate_group_name(group_name):
    """Validate resource group name

    Args:
        group_name (str): Name of resource group

    Returns:
        str: Validated resource group name
    """
    while True:
        if not re.match(r'^[\w_()\-.]+$', group_name):
            print("Invalid deployment name. Group name can only contain include \
                  alphanumeric, underscore, parentheses, hyphen, period (except at end).")
        elif not (min_name_limit <= len(group_name) <= max_name_limit):
            print(f"A valid group name must be {min_name_limit}-{max_name_limit}\
                 character long.")
        else:
            return group_name
        
        group_name = input("Enter another group name: ")


def get_vnet_or_subnet_name(isVNet):
    """Validate the name of a subnet or VNet

    Args:
        isVNet (bool): Determine if it is a VNet or Subnet to be validated

    Returns:
        str: Name of either a Subnet or VNet
    """
    # The resource type is VNet if isVNet is True. Else it is set to Subnet.
    rss_type = "VNet" if isVNet else "Subnet"

    while True:
        name = input(f"Enter {rss_type} name: ")
        
        if not re.match(r'^[a-zA-Z0-9][\w\.-]*[a-zA-Z0-9_]$', name):
            print(f"Invalid {rss_type} name. Name must begin with a letter or number,\
                  end with a letter, number, or underscore, and may contain only letters, \
                  numbers, underscores, periods, or hyphens.")
        elif not (min_name_limit <= len(name) <= max_name_limit):
            print(f"A valid {rss_type} name must be {min_name_limit}-{max_name_limit}\
                 character long.")
        else:
            return name


def get_nsg_name():
    """Validates NSG group name

    Returns:
        str: Name of NSG group
    """
    while True:
        nsg_name = input("Enter NSG name: ")

        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_.-]*[a-zA-Z0-9_]$', nsg_name):
            print("Invalid NSG name. Name must begin with a letter or number, end \
                  with a letter, number, or underscore, and may contain only letters, \
                  numbers, underscores, periods, or hyphens.")
        elif not (min_name_limit <= len(nsg_name) <= max_name_limit):
            print(f"A valid nsg name must be {min_name_limit}-{max_name_limit}\
                 character long.")
        else:
            return nsg_name


def get_server_name(isWebServer):
    """Validates a server's name

    Args:
        isWebServer (bool): If it is a web or db server name to be validated

    Returns:
        str: Name of either the web or db server
    """
    vm_type = 'Webserver' if isWebServer else 'DBServer'

    while True:
        vm_name = input(f"Enter {vm_type} name: ")
        
        if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]$", vm_name):
            print(f"Invalid {vm_type} name. Name cannot contain whitespace or special \
                  characters except '-' but cannot begin or end with '-'")
        elif not (min_name_limit <= len(vm_name) <= max_name_limit):
            print(f"A valid {vm_type} name must be {min_name_limit}-{max_name_limit}\
                  character long.")
        else:
            return vm_name


def get_username(isWebServer):
    """Vaidates a login username

    Args:
        isWebServer (bool): If it is a web or db server name to be validated
    
    Returns:
        str: Login username
    """
    server_type = 'webserver' if isWebServer else 'dbserver'
    reserved_words = ['admin', 'root', 'superuser', "user"]

    while True:
        username = input(f"Enter a username for the {server_type}: ")

        if not (4 < len(username) < 64):
            print("Username must be between 4 and 64 characters.")
        elif not re.match(r"^[\w][\w-]+$", username):
            # \w is a shorthand character that represents alphanumeric characters and 
            # underscore
            print("Invalid username. Username must only contain letters, numbers, hyphens, \
                  and underscores and may not start with a hyphen or number.")
        elif any(word in username.lower() for word in reserved_words):
            print("Username cannot contain reserved words such as admin and user")
        else:
            return username


def get_password(isWebServer):
    """Validates a login password

    Args:
        isWebServer (bool): If it is a web or db server name to be validated

    Returns:
        str: Login password
    """
    server_type = 'webserver' if isWebServer else 'dbserver'

    password_requirements = ["[A-Z]", "[a-z]", "[0-9]", "[$+#!^%*\-=]"]

    while True:
        # getpass module hides user's password input.
        password = getpass.getpass(f"Enter a password for the {server_type}: ")

        # The search returns either True or False which are basically 1 and 0. 
        # The sum function adds to zero, if a starting number is not specified, 
        # these 1s or 0s as it iterates the list.
        matches_passed = sum(bool(re.search(pattern, password)) for pattern in 
                             password_requirements)

        if not (12 < len(password) < 72):
            print("Password must bebetween 12 and 72 characters long.")
        elif not matches_passed >= 3:
            print("Password must contain at least three of the following:\n1) One Uppercase\
                  \n2) One Lowercase\n3) One Number\n4) One Special character")
        else:
            confirm_password = getpass.getpass("Confirm password: ")

            if password == confirm_password:
                print("Passwords matched.")
                return password
            else:
                print("Passwords do not match. Please try again.")


def create_nic_params(group_name, vnet_name, subnet_name, publicip_name=''):
    """Forms a server's NIC parameter argument

    Args:
        group_name (str): Name of resource group
        vnet_name (str): VNet name
        subnet_name (str): Subnet name
        publicip_name (str, optional): Name of Public IP resource. Defaults to ''

    Returns:
        dictionary: Server's NIC properties
    """
    nic_params = {
        'location': location,
        'ip_configurations': [{
            'name': 'MyIpConfig',
            'subnet': {
                'id': f"/subscriptions/{subscription_id}/resourceGroups/{group_name}/providers/Microsoft.Network/virtualNetworks/{vnet_name}/subnets/{subnet_name}"
            },
            'public_ip_address': {
                'id': f"/subscriptions/{subscription_id}/resourceGroups/{group_name}/providers/Microsoft.Network/publicIPAddresses/{publicip_name}"
            }
        }]
    }
    
    if not publicip_name:
        del(nic_params['ip_configurations'][0]['public_ip_address'])
        
    return nic_params


def create_server_params(group_name, server_name, interface_name, isWebServer):
    """Form a webserver's parameter argument

    Args:
        group_name (str): Name of resource group
        server_name (str): Webserver's name
        interface_name (str): NIC interface name
        isWebServer (bool): If it is a web or db server parameter being formed

    Returns:
        dictionary: Server properties
    """
    username = get_username(isWebServer)
    password = get_password(isWebServer)

    if isWebServer:
        image_reference = {
            'sku': '2019-Datacenter', 
            'publisher': 'MicrosoftWindowsServer', 
            'version': 'latest', 
            'offer': 'WindowsServer'
        }
    else:
        image_reference = {
            'sku': 'sqldev-gen2', 
            'publisher': 'MicrosoftSQLServer', 
            'version': 'latest', 
            'offer': 'sql2019-ws2019'
        }

    return {
        'location': location,
        'hardware_profile': {
            'vm_size': 'Standard_B1s'
        },
        'storage_profile': {
            'image_reference': image_reference,
            'os_disk': {
                'caching': 'ReadWrite',
                'managed_disk': {
                    'storage_account_type': 'Standard_LRS'
                },
                'create_option': 'FromImage'
            }
        },
        'os_profile': {
            'admin_username': f"{username}",
            'computer_name': f"{server_name}",
            'admin_password': f"{password}",
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