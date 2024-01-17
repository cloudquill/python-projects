import os
import logging
from dotenv import load_dotenv

logger =  logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(levelname)s - %(asctime)s - %(message)s')

# Configure console log output with desired format (formatter)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Configure file log output to app.log with desired format
file_handler = logging.FileHandler('app.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

logger.info("Loading environment variables from .env file")
try:
    # Load variables in .env file into ENVIRONMENT
    load_dotenv(".env")
    logger.info(".env file loaded successfully.")
except FileNotFoundError:
    logger.critical("The file '.env' could not be found.\n Terminating script...")
    SystemExit(1)

subscription_id = os.environ.get('SUBSCRIPTION_ID')
location = os.environ.get('LOCATION')