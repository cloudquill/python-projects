import argparse

from azure.identity import DefaultAzureCredential
from azure.core.exceptions import (
    AzureError, 
    ClientAuthenticationError, 
    ServiceRequestError
)

from config import logger, subscription_id
from infra_class import Infrastructure
from modules import (
    get_nsg_name, 
    get_server_name, 
    get_vnet_or_subnet_name
)

token_credential = DefaultAzureCredential()
infras_provisioner = Infrastructure(token_credential)

parser = argparse.ArgumentParser(prog="Pycloud Deployer", 
                                 description="A Python CLI tool that deploys a 2 or 3 tier infrastructure to Azure.")

# parent_parser lets us define common options for our subcommands.
parent_parser = argparse.ArgumentParser(add_help=False)
parent_parser.add_argument("--deployment-name", required=True, 
                           help="Deployment name")

# This lets us split up this program's functionality into sub-commands 
# such as setup, info and teardown. If a sub-command such as setup or
# info was entered, this sub-command would be stored and can be accessed
# in the attribute named 'command'.
subparsers = parser.add_subparsers(dest='command')

# Setting up the subcommands with their options. The parent parameter
# attaches the --deployment-name option to each subcommand.
setup_parser = subparsers.add_parser("setup", parents=[parent_parser], 
                                     help="Deploys the infrastructure")
setup_parser.add_argument("--tier", required=True, type=int, 
                          choices=[2,3], help="Specify the type of infrastructure")
setup_parser.add_argument("--webservers", type=int, default=1,
                          choices=range(1, 4), help="Specify the number of webservers to be deployed")

info_parser = subparsers.add_parser("info", parents=[parent_parser], 
                                    help="Retrieve infrastructure information")

teardown_parser = subparsers.add_parser("teardown", parents=[parent_parser], 
                                        help="Remove an entire infrastructure")

# We parse and can now interact with the different parts of the cli command 
# with 'args'.
args = parser.parse_args()

try:
    if args.command == 'setup':
        group_name = infras_provisioner.create_resource_group(args.deployment_name)
        vnet_name = get_vnet_or_subnet_name(True)
        subnet_name = get_vnet_or_subnet_name(False)
        nsg_name = get_nsg_name()
        webserver_name = get_server_name(True)
        dbserver_name = get_server_name(False)

        if args.tier == 2:
            infras_provisioner.tier2(group_name, vnet_name, subnet_name, nsg_name, 
                                     webserver_name, dbserver_name)
        else: 
            if args.webservers < 3:
                infras_provisioner.tier3(group_name, vnet_name, subnet_name, nsg_name, 
                                         webserver_name, dbserver_name,args.webservers)
            else: 
                print("You cannot create more than 2 webservers in a tier 3 infrastructure.")
    elif args.command == 'info':
        infras_provisioner.info(args.deployment_name)
    elif args.command == 'teardown':
        infras_provisioner.delete(args.deployment_name)
except ClientAuthenticationError as e:
    logger.critical(f"Authentication to subscription {subscription_id} failed: {str(e)}")
except ServiceRequestError as e:
    logger.error(f"There seems to be connectivity problems: {str(e)}")
except AzureError as e:
    logger.error(f"Azure error: {str(e)}")
except Exception as e:
    logger.error(f"An error occured: {str(e)}")