import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Define log format
formatter = logging.Formatter('%(levelname)s - %(asctime)s - %(message)s')

# Configure log file outputs with desired format and log level
handler = logging.FileHandler("app.log")
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Configure log outputs to console with desired format and log level
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

# Define the minimum level that logger accepts
logger.setLevel(logging.INFO)

if os.path.exists(".env"):
    logger.info("Loading environment variables from .env file")
    
    # Load variables in .env file into ENVIRONMENT
    load_dotenv(".env")
    logger.info(".env file loaded successfully.")
else:
    logger.critical("The file '.env' could not be found.")
    raise SystemExit(1)

# If set, set log level from environment variable or continue with 
# default.
env_log_level = os.environ.get("LOG_LEVEL")
log_level = getattr(logger, env_log_level, logging.INFO)
logger.setLevel(log_level)

subscription_id = os.environ.get('SUBSCRIPTION_ID')
location = os.environ.get('LOCATION')
if not (subscription_id and location):
    logger.critical("The subscription ID or Location was not set.")
    raise SystemExit(1)

# Define the minimum and maximum range for a resource's name for
# uniformity. The limitation is the range for a VNet's name.
min_name_limit = 2
max_name_limit = 64