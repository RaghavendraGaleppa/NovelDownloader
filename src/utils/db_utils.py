# Standard Package Imports
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.server_api import ServerApi
from urllib.parse import quote_plus
import time
from threading import Lock
from typing import Optional

# Local Imports
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


def get_raw_chapter_for_translation(db: Database, novel_id: str, lock: Lock) -> Optional[dict]:
    """
    Get a raw chapter for translation.
    This function is thread-safe.
    It will pick a chapter that has not been picked up yet or has been picked up for more than 10 minutes.
    """
    with lock:
        ten_minutes_ago = time.time() - 600
        query = {
            "novel_id": novel_id,
            "$or": [
                {"picked_up_at": {"$exists": False}},
                {"picked_up_at": {"$lt": ten_minutes_ago}}
            ]
        }
        chapter = db.raw_chapters.find_one_and_update(
            query,
            {"$set": {"picked_up_at": time.time()}},
            return_document=True
        )
        return chapter