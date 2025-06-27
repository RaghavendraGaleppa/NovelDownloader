from pymongo import MongoClient
from pymongo.database import Database
from pymongo.server_api import ServerApi
from urllib.parse import quote_plus
from utils.logging_utils import get_logger

logger = get_logger()


def get_db_client(host: str, port: int, username: str, pwd: str, db_name: str, db_auth_source: str, ping: bool = True) -> Database:
    """
    Just return a pymongo client. Make sure to pass username and pwd in quote_plus.
    Also make sure to ping before returning the client based on the ping param
    """
    username = quote_plus(username)
    pwd = quote_plus(pwd)
    client = MongoClient(
        f"mongodb://{username}:{pwd}@{host}:{port}/?authSource={db_auth_source}",
        server_api=ServerApi("1")
    )

    # Switch to the database
    db: Database = client[db_name]
    logger.info(f"Connected to the database {db_name}")
    # Ping the server
    if ping:
        client.admin.command("ping")
        logger.info("Pinged the server")
    return db