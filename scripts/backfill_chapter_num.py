import sys
sys.path.append("src")

from main import db_client


def backfill_chapter_num():
    translated_chapters = db_client.translated_chapters.find()
    for record in translated_chapters:
        if "chapter_number" not in record:
            raw_chapter_record = db_client.raw_chapters.find_one({"_id": record["raw_chapter_id"]})
            if raw_chapter_record:
                db_client.translated_chapters.update_one({"_id": record["_id"]}, {"$set": {"chapter_number": raw_chapter_record["chapter_number"]}})


if __name__ == "__main__":
    backfill_chapter_num()