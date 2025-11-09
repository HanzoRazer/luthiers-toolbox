# services/api/app/routers/posts_router.py
"""
Patch N.14 - Post-Processor Template Editor
API endpoints for reading and updating post-processor definitions
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os, json

POSTS_PATH = os.environ.get("TB_POSTS_PATH", "services/api/app/data/posts.json")

router = APIRouter(prefix="/posts", tags=["posts"])


class LineNumbers(BaseModel):
    """Line numbering configuration for G-code output"""
    enabled: bool = False
    start: int = 10
    step: int = 10
    prefix: str = "N"


class PostDef(BaseModel):
    """Post-processor definition model"""
    id: str  # Unique identifier (e.g., "grbl", "mach3")
    title: str  # Human-readable name
    controller: str  # Controller type/family
    line_numbers: Optional[LineNumbers] = LineNumbers()
    header: List[str] = []  # Header template lines
    footer: List[str] = []  # Footer template lines
    percent_wrapper: Optional[bool] = False  # Wrap with % for some controllers
    program_number_from: Optional[str] = None  # Token for program number
    tokens: Dict[str, Any] = {}  # Custom token definitions


def _load_posts() -> List[Dict[str, Any]]:
    """Load post-processor definitions from JSON file"""
    try:
        with open(POSTS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Support both array format and {posts: [...]} format
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "posts" in data:
                return data["posts"]
            return []
    except FileNotFoundError:
        return []


def _save_posts(arr: List[Dict[str, Any]]):
    """Save post-processor definitions to JSON file"""
    os.makedirs(os.path.dirname(POSTS_PATH), exist_ok=True)
    with open(POSTS_PATH, "w", encoding="utf-8") as f:
        json.dump(arr, f, indent=2, ensure_ascii=False)


@router.get("", response_model=List[PostDef])
def list_posts():
    """
    List all post-processor definitions
    
    Returns:
        Array of post-processor definitions with templates
    """
    posts = _load_posts()
    return posts


@router.put("", response_model=dict)
def replace_posts(posts: List[PostDef]):
    """
    Replace all post-processor definitions
    
    Validates for duplicate IDs before saving.
    
    Args:
        posts: Complete array of post-processor definitions
    
    Returns:
        Success status and count of saved posts
    
    Raises:
        HTTPException: 400 if duplicate IDs found
    """
    seen = set()
    arr = []
    
    for p in posts:
        if p.id in seen:
            raise HTTPException(400, f"Duplicate post id: {p.id}")
        seen.add(p.id)
        arr.append(p.dict())
    
    _save_posts(arr)
    return {"ok": True, "count": len(arr)}
