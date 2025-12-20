### This file contains the serializers for the data from novel collection
from pydantic import BaseModel, Field
from bson import ObjectId
from datetime import datetime
from typing import Any, List, Optional


class NovelListItemSerializer(BaseModel):
    """Serializer for novel list items with chapter counts."""
    id: str = Field(serialization_alias="id")
    name: str = Field(serialization_alias="name")
    raw_chapters_count: int = Field(default=0, serialization_alias="raw_chapters_count")
    translated_chapters_count: int = Field(default=0, serialization_alias="translated_chapters_count")

    class Config:
        arbitrary_types_allowed = True


class ChapterTOCItemSerializer(BaseModel):
    """Serializer for table of contents chapter items."""
    chapter_number: int
    title: Optional[str] = None
    is_translated: bool = False

    class Config:
        arbitrary_types_allowed = True


class NovelInfoSerializer(BaseModel):
    """Serializer for detailed novel information with TOC."""
    id: str
    name: str
    raw_chapters_count: int = 0
    translated_chapters_count: int = 0
    table_of_contents: List[ChapterTOCItemSerializer] = []

    class Config:
        arbitrary_types_allowed = True


class ChapterContentSerializer(BaseModel):
    """Serializer for chapter content."""
    novel_id: str
    chapter_number: int
    title: Optional[str] = None
    content: str
    provider: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


class BaseResponseSerializer(BaseModel):
    """Base response wrapper for all API responses."""
    success: bool = True
    data: Any = None
    error: Optional[str] = None
    ref_code: int = 200

    class Config:
        json_encoders = {ObjectId: str}


# Legacy serializers for backwards compatibility
class NovelSerializer(BaseModel):
    id: ObjectId = Field(alias="_id", serialization_alias="id")
    novel_name: str = Field(serialization_alias="name")
    added_datetime: datetime = Field(exclude=True)
    folder_path: str = Field(exclude=True)
    raw_chapters_available: int = Field(default=0, exclude=True)
    translated_chapters_available: int = Field(default=0, serialization_alias="chapters_available")

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
