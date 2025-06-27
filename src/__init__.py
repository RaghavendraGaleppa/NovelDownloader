from dotenv import load_dotenv
from utils.logging_utils import get_logger
import os
load_dotenv()



#### SETUP THE LOGGER
MAIN_LOGGER_NAME = os.environ["MAIN_LOGGER_NAME"]
logger = get_logger(MAIN_LOGGER_NAME)
logger.info("Starting the application")

#### GET THE DB CLIENT
DB_HOST = os.environ["DB_HOST"]
DB_PORT = int(os.environ["DB_PORT"])
DB_USERNAME = os.environ["DB_USERNAME"]
DB_PWD = os.environ["DB_PWD"]
DB_NAME = os.environ["DB_NAME"]
DB_AUTH_SOURCE = os.environ["DB_AUTH_SOURCE"]

from utils.db_utils import get_db_client
db_client = get_db_client(DB_HOST, DB_PORT, DB_USERNAME, DB_PWD, DB_NAME, DB_AUTH_SOURCE)

