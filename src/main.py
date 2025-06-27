# Standard Package imports
import os
from dotenv import load_dotenv

# Project imports
from utils.logging_utils import get_logger

load_dotenv()


#### SETUP THE LOGGER
MAIN_LOGGER_NAME = os.environ["MAIN_LOGGER_NAME"]
logger = get_logger(MAIN_LOGGER_NAME)
logger.info("Starting the application")

#### GET THE DB CLIENT
DB_HOST = os.environ["MONGO_HOST"]
DB_PORT = int(os.environ["MONGO_PORT"])
DB_USERNAME = os.environ["MONGO_USERNAME"]
DB_PWD = os.environ["MONGO_PASSWORD"]
DB_NAME = os.environ["MONGO_DB_NAME"]
DB_AUTH_SOURCE = os.environ["MONGO_AUTH_SOURCE"]

from utils.db_utils import get_db_client
db_client = get_db_client(DB_HOST, DB_PORT, DB_USERNAME, DB_PWD, DB_NAME, DB_AUTH_SOURCE)

