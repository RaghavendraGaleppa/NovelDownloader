from bson import ObjectId
from fastapi import HTTPException
from pymongo.database import Database
from api_serializers.novel_serializer import TranslatedChapterSerializer
from typing import List, Optional




def get_paginated_results(db_client: Database, collection_name: str, query: Optional[dict]=None, limit: int=10, last_id: Optional[str]=None) -> List[TranslatedChapterSerializer]:
    
    if query is None:
        query = {}

    if last_id is not None:
        query["_id"] = {"$gt": ObjectId(last_id)}

    data = db_client[collection_name].find(query).sort("_id", 1).limit(limit)
    if not data:
        raise HTTPException(status_code=404, detail="No more results")
    return [TranslatedChapterSerializer(**doc) for doc in data]
    
