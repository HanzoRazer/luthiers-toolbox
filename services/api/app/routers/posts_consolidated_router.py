"""
Consolidated Posts Router - Post-processor definition management.

Consolidates:
- posts_router.py (simple list/replace)
- post_router.py (full CRUD with validation)

Note: cam_post_v155_router.py (G-code generation) is NOT included here.
It belongs to CAM subsystem, not post definition management.

Endpoints:
  CRUD:
    - GET / - List all posts (builtin + custom)
    - GET /{post_id} - Get single post
    - POST / - Create custom post
    - PUT /{post_id} - Update custom post
    - DELETE /{post_id} - Delete custom post
    - POST /validate - Validate post config without saving

  Utilities:
    - GET /tokens/list - List available tokens
    - PUT /replace-all - Replace all posts (legacy)
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, validator


router = APIRouter(tags=["posts"])


# ============================================================================
# Configuration
# ============================================================================

DATA_DIR = Path(__file__).parent.parent / "data" / "posts"
CUSTOM_POSTS_FILE = DATA_DIR / "custom_posts.json"
LEGACY_POSTS_PATH = os.environ.get(
    "TB_POSTS_PATH",
    str(Path(__file__).parent.parent / "data" / "posts.json")
)
BUILTIN_POST_IDS = ["GRBL", "Mach4", "LinuxCNC", "PathPilot", "MASSO"]


def _ensure_posts_dir() -> None:
    """Create posts directory on first write (Docker compatibility)."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Models
# ============================================================================

class LineNumbers(BaseModel):
    """Line numbering configuration for G-code output."""
    enabled: bool = False
    start: int = 10
    step: int = 10
    prefix: str = "N"


class PostMetadata(BaseModel):
    """Post-processor metadata."""
    controller_family: Optional[str] = None
    gcode_dialect: Optional[str] = None
    supports_arcs: bool = True
    max_line_length: int = 255
    comment_style: str = "parentheses"  # or "semicolon"
    has_tool_changer: bool = False


class PostConfig(BaseModel):
    """Complete post-processor configuration."""
    id: str = Field(..., max_length=32, pattern=r'^[A-Za-z0-9_]+$')
    name: str = Field(default="", max_length=100)
    title: Optional[str] = None  # Legacy compatibility
    description: str = Field(default="", max_length=500)
    controller: Optional[str] = None  # Legacy compatibility
    builtin: bool = False
    header: List[str] = Field(default_factory=list)
    footer: List[str] = Field(default_factory=list)
    line_numbers: Optional[LineNumbers] = None
    percent_wrapper: Optional[bool] = False
    program_number_from: Optional[str] = None
    tokens: Dict[str, Any] = Field(default_factory=dict)
    metadata: Optional[PostMetadata] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @validator('id')
    def validate_id(cls, v, values):
        """Ensure custom IDs don't conflict with builtins."""
        if values.get('builtin', False):
            return v
        if any(v.upper().startswith(prefix) for prefix in BUILTIN_POST_IDS):
            pass  # Allow for now, will check in endpoint
        return v


class PostCreateIn(BaseModel):
    """Input for creating new post."""
    id: str = Field(..., max_length=32, pattern=r'^[A-Z0-9_]+$')
    name: str = Field(..., max_length=100)
    description: str = Field(default="", max_length=500)
    header: List[str] = Field(..., min_length=1)
    footer: List[str] = Field(..., min_length=1)
    tokens: Dict[str, str] = Field(default_factory=dict)
    metadata: Optional[PostMetadata] = None


class PostUpdateIn(BaseModel):
    """Input for updating existing post (partial)."""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    header: Optional[List[str]] = Field(None, min_length=1)
    footer: Optional[List[str]] = Field(None, min_length=1)
    tokens: Optional[Dict[str, str]] = None
    metadata: Optional[PostMetadata] = None


class PostListItem(BaseModel):
    """Post summary for list view."""
    id: str
    name: str
    builtin: bool
    description: str


class ValidationResult(BaseModel):
    """Validation result."""
    valid: bool
    warnings: List[str] = []
    errors: List[str] = []


# ============================================================================
# Storage Functions
# ============================================================================

def load_builtin_posts() -> List[PostConfig]:
    """Load all builtin post configurations."""
    posts = []
    default_names = {
        "GRBL": "GRBL 1.1",
        "Mach4": "Mach4",
        "LinuxCNC": "LinuxCNC",
        "PathPilot": "PathPilot",
        "MASSO": "MASSO G3"
    }

    for post_id in BUILTIN_POST_IDS:
        file_path = DATA_DIR / f"{post_id.lower()}.json"
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    post = PostConfig.model_construct(
                        id=post_id,
                        name=data.get('name', default_names.get(post_id, post_id)),
                        description=data.get('description', f'Built-in post-processor for {post_id}'),
                        builtin=True,
                        header=data.get('header', []),
                        footer=data.get('footer', []),
                        tokens=data.get('tokens', {}),
                        metadata=PostMetadata(**data.get('metadata', {})) if 'metadata' in data else None
                    )
                    posts.append(post)
            except (OSError, json.JSONDecodeError, KeyError, ValueError):  # WP-1: skip unloadable post files
                pass  # Skip files that can't be loaded

    return posts


def load_custom_posts() -> List[PostConfig]:
    """Load custom posts from custom_posts.json."""
    if not CUSTOM_POSTS_FILE.exists():
        return []

    try:
        with open(CUSTOM_POSTS_FILE, 'r') as f:
            data = json.load(f)
            return [PostConfig(**post) for post in data.get('posts', [])]
    except (OSError, json.JSONDecodeError, KeyError, ValueError):  # WP-1: fallback on corrupt custom posts
        return []


def save_custom_posts(posts: List[PostConfig]) -> None:
    """Save custom posts to custom_posts.json."""
    _ensure_posts_dir()
    data = {
        'version': '1.0',
        'posts': [post.model_dump() for post in posts]
    }
    with open(CUSTOM_POSTS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def load_legacy_posts() -> List[Dict[str, Any]]:
    """Load posts from legacy posts.json format."""
    try:
        with open(LEGACY_POSTS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "posts" in data:
                return data["posts"]
            return []
    except FileNotFoundError:
        return []


def save_legacy_posts(posts: List[Dict[str, Any]]) -> None:
    """Save posts to legacy posts.json format."""
    os.makedirs(os.path.dirname(LEGACY_POSTS_PATH), exist_ok=True)
    with open(LEGACY_POSTS_PATH, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)


def load_all_posts() -> List[PostConfig]:
    """Load all posts (builtin + custom)."""
    return load_builtin_posts() + load_custom_posts()


def find_post(post_id: str) -> Optional[PostConfig]:
    """Find post by ID."""
    for post in load_all_posts():
        if post.id == post_id:
            return post
    return None


# ============================================================================
# CRUD Endpoints
# ============================================================================

@router.get("/", response_model=Dict[str, List[PostListItem]])
def list_posts() -> Dict[str, List[PostListItem]]:
    """List all posts (builtin + custom)."""
    posts = load_all_posts()
    items = [
        PostListItem(
            id=post.id,
            name=post.name or post.title or post.id,
            builtin=post.builtin,
            description=post.description
        )
        for post in posts
    ]
    return {"posts": items}


@router.get("/{post_id}", response_model=PostConfig)
def get_post(post_id: str) -> PostConfig:
    """Get single post configuration."""
    post = find_post(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post '{post_id}' not found"
        )
    return post


@router.post("/", response_model=Dict[str, Any])
def create_post(body: PostCreateIn) -> Dict[str, Any]:
    """Create new custom post."""
    if find_post(body.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Post '{body.id}' already exists"
        )

    if any(body.id.startswith(prefix) for prefix in BUILTIN_POST_IDS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Post ID cannot start with reserved prefixes: {BUILTIN_POST_IDS}"
        )

    now = datetime.utcnow().isoformat() + 'Z'
    post = PostConfig(
        **body.model_dump(),
        builtin=False,
        created_at=now,
        updated_at=now
    )

    custom_posts = load_custom_posts()
    custom_posts.append(post)
    save_custom_posts(custom_posts)

    return {"id": post.id, "name": post.name, "builtin": False, "created_at": now}


@router.put("/{post_id}", response_model=Dict[str, Any])
def update_post(post_id: str, body: PostUpdateIn) -> Dict[str, Any]:
    """Update existing custom post."""
    post = find_post(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post '{post_id}' not found"
        )

    if post.builtin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot edit builtin post '{post_id}'"
        )

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(post, key, value)

    post.updated_at = datetime.utcnow().isoformat() + 'Z'

    custom_posts = load_custom_posts()
    for i, p in enumerate(custom_posts):
        if p.id == post_id:
            custom_posts[i] = post
            break
    save_custom_posts(custom_posts)

    return {"id": post.id, "updated_at": post.updated_at}


@router.delete("/{post_id}", response_model=Dict[str, Any])
def delete_post(post_id: str) -> Dict[str, Any]:
    """Delete custom post."""
    post = find_post(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post '{post_id}' not found"
        )

    if post.builtin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot delete builtin post '{post_id}'"
        )

    custom_posts = load_custom_posts()
    custom_posts = [p for p in custom_posts if p.id != post_id]
    save_custom_posts(custom_posts)

    return {"id": post_id, "deleted": True}


@router.post("/validate", response_model=ValidationResult)
def validate_post(body: PostCreateIn) -> ValidationResult:
    """Validate post configuration without saving."""
    errors = []
    warnings = []

    if find_post(body.id):
        errors.append(f"Post ID '{body.id}' already exists")

    if any(body.id.startswith(prefix) for prefix in BUILTIN_POST_IDS):
        errors.append(f"Post ID cannot start with reserved prefixes: {BUILTIN_POST_IDS}")

    if not body.header:
        errors.append("Header cannot be empty")
    if not body.footer:
        errors.append("Footer cannot be empty")

    for i, line in enumerate(body.header):
        if len(line) > 255:
            warnings.append(f"Header line {i+1} exceeds 255 characters")
    for i, line in enumerate(body.footer):
        if len(line) > 255:
            warnings.append(f"Footer line {i+1} exceeds 255 characters")

    return ValidationResult(valid=len(errors) == 0, warnings=warnings, errors=errors)


# ============================================================================
# Utility Endpoints
# ============================================================================

@router.get("/tokens/list", response_model=Dict[str, str])
def list_tokens() -> Dict[str, str]:
    """List all available tokens with descriptions."""
    return {
        'POST_ID': 'Post-processor identifier',
        'UNITS': 'Units (mm or inch)',
        'DATE': 'ISO 8601 timestamp',
        'TOOL_DIAMETER': 'Tool diameter',
        'TOOL_NUMBER': 'Tool number (for tool changers)',
        'MATERIAL': 'Material name',
        'MACHINE_ID': 'Machine profile ID',
        'FEED_XY': 'Cutting feed rate',
        'FEED_Z': 'Plunge feed rate',
        'SPINDLE_RPM': 'Spindle speed',
    }


# ============================================================================
# Legacy Endpoints
# ============================================================================

@router.get("/all", response_model=List[Dict[str, Any]])
def list_posts_legacy() -> List[Dict[str, Any]]:
    """
    Legacy endpoint - list all posts as flat array.
    Use GET / for structured response.
    """
    return [p.model_dump() for p in load_all_posts()]


@router.put("/replace-all", response_model=Dict[str, Any])
def replace_posts_legacy(posts: List[PostConfig]) -> Dict[str, Any]:
    """
    Legacy endpoint - replace all posts.
    Validates for duplicate IDs before saving.
    """
    seen = set()
    arr = []

    for p in posts:
        if p.id in seen:
            raise HTTPException(400, f"Duplicate post id: {p.id}")
        seen.add(p.id)
        arr.append(p.model_dump())

    save_legacy_posts(arr)
    return {"ok": True, "count": len(arr)}
