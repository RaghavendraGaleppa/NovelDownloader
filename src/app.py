# Standard Package imports
from bson import ObjectId
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os

# Project imports

## UTILS
from main import db_client
from utils.logging_utils import get_logger

## SERIALIZERS
from api_serializers.novel_serializer import (
    NovelListItemSerializer,
    NovelInfoSerializer,
    ChapterTOCItemSerializer,
    ChapterContentSerializer,
    BaseResponseSerializer,
    # Legacy
    NovelSerializer,
    NovelDataSerializer,
    TranslatedChapterSerializer
)


api_logger = get_logger("api")
app = FastAPI(
    title="Novel Reader API",
    description="API for reading translated Chinese novels",
    version="1.0.0"
)

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#### ROUTES

@app.get("/")
async def landing_page():
    """Welcome endpoint."""
    api_logger.info("Landing page hit")
    return {"message": "Welcome to the Novel Reader API", "version": "1.0.0"}


@app.get("/novels", response_model=BaseResponseSerializer)
async def list_novels():
    """
    List all available novels sorted alphabetically.
    
    Returns each novel with:
    - id: Novel identifier
    - name: Novel title
    - raw_chapters_count: Number of scraped (raw) chapters
    - translated_chapters_count: Number of translated chapters
    """
    api_logger.info("Novels list endpoint hit")
    
    try:
        # Fetch all novels sorted by name (case-insensitive)
        novels_cursor = db_client.novels.find({}).sort("novel_name", 1)
        
        novels_list = []
        for novel in novels_cursor:
            novel_item = NovelListItemSerializer(
                id=str(novel["_id"]),
                name=novel.get("novel_name", "Unknown"),
                raw_chapters_count=novel.get("raw_chapters_available", 0),
                translated_chapters_count=novel.get("translated_chapters_available", 0)
            )
            novels_list.append(novel_item)
        
        return BaseResponseSerializer(
            success=True,
            data=[n.model_dump(by_alias=True) for n in novels_list],
            ref_code=200
        )
    
    except Exception as e:
        api_logger.error(f"Error fetching novels: {e}")
        return BaseResponseSerializer(
            success=False,
            error=str(e),
            ref_code=500
        )


@app.get("/novels/{novel_id}", response_model=BaseResponseSerializer)
async def get_novel_info(novel_id: str):
    """
    Get detailed information about a specific novel.
    
    Returns:
    - id: Novel identifier
    - name: Novel title
    - raw_chapters_count: Number of scraped (raw) chapters
    - translated_chapters_count: Number of translated chapters
    - table_of_contents: List of chapters with number, title, and translation status
    """
    api_logger.info(f"Novel info endpoint hit for {novel_id}")
    
    try:
        # Validate ObjectId
        try:
            novel_object_id = ObjectId(novel_id)
        except Exception:
            return BaseResponseSerializer(
                success=False,
                error="Invalid novel ID format",
                ref_code=400
            )
        
        # Fetch novel
        novel_doc = db_client.novels.find_one({"_id": novel_object_id})
        
        if not novel_doc:
            return BaseResponseSerializer(
                success=False,
                error="Novel not found",
                ref_code=404
            )
        
        # Fetch raw chapters for TOC (sorted by chapter number)
        raw_chapters_cursor = db_client.raw_chapters.find(
            {"novel_id": novel_object_id}
        ).sort("chapter_number", 1)
        
        # Fetch translated chapter numbers for this novel (completed only)
        translated_chapters_cursor = db_client.translated_chapters.find(
            {"novel_id": novel_object_id, "status": "completed"},
            {"chapter_number": 1, "title": 1}
        )
        
        # Build a set of translated chapter numbers and a map of titles
        translated_info = {}
        for tc in translated_chapters_cursor:
            chapter_num = tc.get("chapter_number")
            if chapter_num is not None:
                translated_info[chapter_num] = tc.get("title")
        
        # Build table of contents
        toc = []
        for raw_chapter in raw_chapters_cursor:
            chapter_num = raw_chapter.get("chapter_number")
            if chapter_num is None:
                continue
            
            # Use translated title if available, otherwise use raw title
            is_translated = chapter_num in translated_info
            title = translated_info.get(chapter_num) if is_translated else raw_chapter.get("title")
            
            toc_item = ChapterTOCItemSerializer(
                chapter_number=chapter_num,
                title=title,
                is_translated=is_translated
            )
            toc.append(toc_item)
        
        # Build response
        novel_info = NovelInfoSerializer(
            id=str(novel_doc["_id"]),
            name=novel_doc.get("novel_name", "Unknown"),
            raw_chapters_count=novel_doc.get("raw_chapters_available", 0),
            translated_chapters_count=novel_doc.get("translated_chapters_available", 0),
            table_of_contents=toc
        )
        
        return BaseResponseSerializer(
            success=True,
            data=novel_info.model_dump(by_alias=True),
            ref_code=200
        )
    
    except Exception as e:
        api_logger.error(f"Error fetching novel info: {e}")
        return BaseResponseSerializer(
            success=False,
            error=str(e),
            ref_code=500
        )


@app.get("/novels/{novel_id}/chapters/{chapter_number}", response_model=BaseResponseSerializer)
async def get_chapter_content(novel_id: str, chapter_number: int):
    """
    Get the translated content for a specific chapter.
    
    Returns:
    - novel_id: Novel identifier
    - chapter_number: Chapter number
    - title: Chapter title
    - content: Full translated chapter text
    - provider: Translation provider used
    """
    api_logger.info(f"Chapter content endpoint hit for novel {novel_id}, chapter {chapter_number}")
    
    try:
        # Validate ObjectId
        try:
            novel_object_id = ObjectId(novel_id)
        except Exception:
            return BaseResponseSerializer(
                success=False,
                error="Invalid novel ID format",
                ref_code=400
            )
        
        # Check if novel exists
        novel_doc = db_client.novels.find_one({"_id": novel_object_id})
        if not novel_doc:
            return BaseResponseSerializer(
                success=False,
                error="Novel not found",
                ref_code=404
            )
        
        # Find the translated chapter
        translated_chapter = db_client.translated_chapters.find_one({
            "novel_id": novel_object_id,
            "chapter_number": chapter_number,
            "status": "completed"
        })
        
        if not translated_chapter:
            return BaseResponseSerializer(
                success=False,
                error=f"Chapter {chapter_number} not found or not yet translated",
                ref_code=404
            )
        
        # Read the chapter content from file
        saved_at = translated_chapter.get("saved_at")
        if not saved_at or not os.path.exists(saved_at):
            return BaseResponseSerializer(
                success=False,
                error=f"Chapter file not found at expected location",
                ref_code=404
            )
        
        try:
            with open(saved_at, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            api_logger.error(f"Error reading chapter file {saved_at}: {e}")
            return BaseResponseSerializer(
                success=False,
                error="Error reading chapter content",
                ref_code=500
            )
        
        # Build response
        chapter_content = ChapterContentSerializer(
            novel_id=novel_id,
            chapter_number=chapter_number,
            title=translated_chapter.get("title"),
            content=content,
            provider=translated_chapter.get("provider")
        )
        
        return BaseResponseSerializer(
            success=True,
            data=chapter_content.model_dump(by_alias=True),
            ref_code=200
        )
    
    except Exception as e:
        api_logger.error(f"Error fetching chapter content: {e}")
        return BaseResponseSerializer(
            success=False,
            error=str(e),
            ref_code=500
        )


# ==================== LEGACY ENDPOINTS ====================
# Keeping for backwards compatibility

@app.get("/library", response_model=BaseResponseSerializer)
async def library():
    """Legacy: List all novels."""
    api_logger.info("Library page hit (legacy)")
    novels = db_client.novels.find()
    novels_list = []
    for novel in novels:
        try:
            novels_list.append(NovelSerializer(**novel))
        except Exception as e:
            api_logger.warning(f"Skipping novel due to serialization error: {e}")
            continue
    return BaseResponseSerializer(data=novels_list)


@app.get("/novel/{novel_id}", response_model=BaseResponseSerializer)
async def novel(novel_id: str):
    """Legacy: Get novel info."""
    api_logger.info(f"Novel page hit for {novel_id} (legacy)")
    novel_data: dict = db_client.novels.find_one({"_id": ObjectId(novel_id)}) or {}
    if not novel_data:
        return BaseResponseSerializer(data=None, ref_code=404)
    
    response_data = NovelDataSerializer(
        novel=NovelSerializer(**novel_data),
    )

    return BaseResponseSerializer(data=response_data, ref_code=200)
