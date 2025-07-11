### This file contains the serializers for the data from novel collection
from pydantic import BaseModel, Field
from bson import ObjectId
from datetime import datetime
from typing import Any, List


class NovelSerializer(BaseModel):
    id: ObjectId = Field(alias="_id", serialization_alias="id")
    novel_name: str = Field(serialization_alias="name")
    added_datetime: datetime = Field(exclude=True)
    folder_path: str = Field(exclude=True)
    raw_chapters_available: int = Field(exclude=True)
    translated_chapters_available: int = Field(serialization_alias="chapters_available")

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        

class TranslatedChapterSerializer(BaseModel):
    id: ObjectId = Field(alias="_id", serialization_alias="id")
    novel_id: ObjectId = Field(serialization_alias="novel_id")
    raw_chapter_id: ObjectId = Field(exclude=True)
    chapter_number: int = Field(serialization_alias="chapter_number")
    title: str = Field(serialization_alias="title")
    pickup_epoch: float = Field(exclude=True)
    status: str = Field(exclude=True)
    n_tries: int = Field(exclude=True)
    end_epoch: float = Field(exclude=True)
    provider: str = Field(exclude=True)
    saved_at: str = Field(exclude=True)
    time_taken_epoch: float = Field(exclude=True)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        

class NovelDataSerializer(BaseModel):
    novel: NovelSerializer
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

        
class BaseResponseSerializer(BaseModel):
    data: Any
    ref_code: int = 200

    class Config:
        json_encoders = {ObjectId: str}