# Standard Package imports
from bson import ObjectId
from fastapi import FastAPI
from typing import List

# Project imports

## UTILS
from main import db_client
from utils.logging_utils import get_logger

## SERIALIZERS
from api_serializers.novel_serializer import NovelSerializer, BaseResponseSerializer, NovelDataSerializer, TranslatedChapterSerializer


api_logger = get_logger("api")
app = FastAPI()


#### ROUTES
@app.get("/")
async def landing_page():
    api_logger.info("Landing page hit")
    return {"message": "Welcome"}


@app.get("/library", response_model=BaseResponseSerializer)
async def library():
    api_logger.info("Library page hit")
    novels = db_client.novels.find()
    novels_list = [NovelSerializer(**novel) for novel in novels]
    return BaseResponseSerializer(data=novels_list)


@app.get("/novel/{novel_id}", response_model=BaseResponseSerializer)
async def novel(novel_id: str):
    api_logger.info(f"Novel page hit for {novel_id}")
    novel_data: dict = db_client.novels.find_one({"_id": ObjectId(novel_id)}) or {}
    if not novel_data:
        return BaseResponseSerializer(data=None, ref_code=404)
    chapters_data = db_client.translated_chapters.find({"novel_id": ObjectId(novel_id)})
    
    response_data = NovelDataSerializer(
        novel=NovelSerializer(**novel_data),
        chapters=[TranslatedChapterSerializer(**chapter) for chapter in chapters_data]
    )

    return BaseResponseSerializer(data=response_data, ref_code=200)