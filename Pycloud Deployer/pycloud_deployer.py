import os
import argparse
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from infra_classes import WebServer, DBServer, LoadBalancer

# Load variables in .env file into ENVIRONMENT
if os.environ.get('Environment') == 'development':
    print("Loading environment variables from .env file")
    load_dotenv(".env")

# Obtain subscription ID
subscription_id = os.environ.get('SUBSCRIPTION_ID')

# Acquire a credential object
token_credential = DefaultAzureCredential()

parser = argparse.ArgumentParser(
                    prog="Pycloud Deployer", 
                    description="A Python CLI tool that facilitates the deployment of a 2 or 3 tier infrastructure to Azure.")

# This lets us split up this program's functionality into sub-commands such as setup, info and teardown.
# If a sub-command such as setup or info was entered, this sub-command would be stored and can be accessed in the attribute named 'command'
subparsers = parser.add_subparsers(dest='command')

# Setting up the 'setup' subcommand with its options
setup_parser = subparsers.add_parser("setup", help="Deploys the infrastructure")
setup_parser.add_argument("-d","--deployment-name", required=True, help="Name of the deployment")
setup_parser.add_argument("-t","--tier", required=True, type=int, choices=[2,3], help="Specify the type of infrastructure")
setup_parser.add_argument("--webservers", type=int, default=1, help="Specify the number of webservers to be deployed")

# Setting up the 'info' subcommand with its options
info_parser = subparsers.add_parser("info", help="Retrieve information about the infrastructure")
info_parser.add_argument("-d","--deployment-name", help="Name of the deployment")

# Setting up the 'teardown' subcommand with its options
teardown_parser = subparsers.add_parser("teardown", help="Remove the entire deployed infrastructure")
teardown_parser.add_argument("-d","--deployment-name", help="Name of the deployment")

# We parse and can now interact with the different parts of the cli command with 'args'
args = parser.parse_args()

# This obtains and stores the deployment name
deployment_name = args.deployment_name

webserver_provisioner = WebServer(subscription_id, token_credential, deployment_name)
dbserver_provisioner = DBServer(subscription_id, token_credential, deployment_name)
lb_provisioner = LoadBalancer(subscription_id, token_credential, deployment_name)

if args.command == 'setup':
    if args.tier == 2:
        # Create a webserver
        webserver_provisioner.create_webserver(0)

        # Create a database server
        dbserver_provisioner.create_dbserver()

    elif args.tier == 3:
        # Create webserver(s)
        for server_number in range(args.webservers):
            webserver_provisioner.create_webserver(server_number)
        
        # Create database server
        # dbserver_provisioner.create_dbserver()

        # Create Load Balancer
        lb_provisioner.create_lb()

        # Add webserver(s) to backend pool of load balancer
        webserver_provisioner.add_webserver_to_lb_backend_pool(args.webservers)

elif args.command == 'teardown':
    webserver_provisioner.rss_client.resource_groups.begin_delete(deployment_name)