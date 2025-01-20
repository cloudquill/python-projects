import os
from dotenv import load_dotenv

import cohere
from azure.cosmos import CosmosClient

load_dotenv()

cohere_api_key = os.getenv("COHERE_API_KEY")
co = cohere.ClientV2(f"{cohere_api_key}")

url = os.getenv("ACCOUNT_URI")
key = os.getenv("ACCOUNT_KEY")
client = CosmosClient(url, {'masterKey': key})
database = client.get_database_client("movies")
container = database.get_container_client("movie-info")