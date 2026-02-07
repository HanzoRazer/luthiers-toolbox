"""
Post-Processor CRUD Router (N.0)
Manages custom CNC post-processor configurations.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, validator

router = APIRouter(prefix="/api/posts", tags=["posts", "N0"])

# Data directory
DATA_DIR = Path(__file__).parent.parent / "data" / "posts"
CUSTOM_POSTS_FILE = DATA_DIR / "custom_posts.json"
BUILTIN_POST_IDS = ["GRBL", "Mach4", "LinuxCNC", "PathPilot", "MASSO"]


def _ensure_posts_dir() -> None:
    """Create posts directory on first write (Docker compatibility)."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Schemas
# ============================================================================

class PostMetadata(BaseModel):
    """Post-processor metadata"""
    controller_family: Optional[str] = None
    gcode_dialect: Optional[str] = None
    supports_arcs: bool = True
    max_line_length: int = 255
    comment_style: str = "parentheses"  # or "semicolon"
    has_tool_changer: bool = False


class PostConfig(BaseModel):
    """Complete post-processor configuration"""
    id: str = Field(..., max_length=32, pattern=r'^[A-Za-z0-9_]+$')  # Allow mixed case
    name: str = Field(..., max_length=100)
    description: str = Field(default="", max_length=500)
    builtin: bool = False
    header: List[str] = Field(..., min_items=1)
    footer: List[str] = Field(..., min_items=1)
    tokens: Dict[str, str] = Field(default_factory=dict)
    metadata: Optional[PostMetadata] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @validator('id')
    def validate_id(cls, v, values):
        """Ensure ID doesn't conflict with builtins (skip for builtin posts)"""
        # Skip validation for builtin posts
        if values.get('builtin', False):
            return v
        # Enforce uppercase for custom posts
        if not v.isupper() and not all(c in '0123456789_' for c in v.replace('_', '')):
            raise ValueError("Custom post IDs must be uppercase letters, numbers, and underscores")
        # Check reserved prefixes
        if any(v.startswith(prefix) for prefix in BUILTIN_POST_IDS):
            raise ValueError(f"Post ID cannot start with reserved prefixes: {BUILTIN_POST_IDS}")
        return v


class PostCreateIn(BaseModel):
    """Input for creating new post"""
    id: str = Field(..., max_length=32, pattern=r'^[A-Z0-9_]+$')  # Custom posts must be uppercase
    name: str = Field(..., max_length=100)
    description: str = Field(default="", max_length=500)
    header: List[str] = Field(..., min_items=1)
    footer: List[str] = Field(..., min_items=1)
    tokens: Dict[str, str] = Field(default_factory=dict)
    metadata: Optional[PostMetadata] = None


class PostUpdateIn(BaseModel):
    """Input for updating existing post (partial)"""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    header: Optional[List[str]] = Field(None, min_items=1)
    footer: Optional[List[str]] = Field(None, min_items=1)
    tokens: Optional[Dict[str, str]] = None
    metadata: Optional[PostMetadata] = None


class PostListItem(BaseModel):
    """Post summary for list view"""
    id: str
    name: str
    builtin: bool
    description: str


class ValidationResult(BaseModel):
    """Validation result"""
    valid: bool
    warnings: List[str] = []
    errors: List[str] = []


# ============================================================================
# Storage Functions
# ============================================================================

def load_builtin_posts() -> List[PostConfig]:
    """Load all builtin post configurations from individual JSON files"""
    posts = []
    # Default names for builtin posts
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
                    # Use model_construct to bypass validators for builtin posts
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
            except (KeyError, ValueError, json.JSONDecodeError, OSError) as e:  # WP-1: narrowed from except Exception
                print(f"Warning: Could not load builtin post {post_id}: {e}")
    
    return posts


def load_custom_posts() -> List[PostConfig]:
    """Load custom posts from custom_posts.json"""
    if not CUSTOM_POSTS_FILE.exists():
        return []
    
    with open(CUSTOM_POSTS_FILE, 'r') as f:
        data = json.load(f)
        return [PostConfig(**post) for post in data.get('posts', [])]


def save_custom_posts(posts: List[PostConfig]):
    """Save custom posts to custom_posts.json"""
    _ensure_posts_dir()  # Create directory on first write
    
    data = {
        'version': '1.0',
        'posts': [post.dict() for post in posts]
    }
    
    with open(CUSTOM_POSTS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def load_all_posts() -> List[PostConfig]:
    """Load all posts (builtin + custom)"""
    return load_builtin_posts() + load_custom_posts()


def find_post(post_id: str) -> Optional[PostConfig]:
    """Find post by ID"""
    for post in load_all_posts():
        if post.id == post_id:
            return post
    return None


def is_builtin(post_id: str) -> bool:
    """Check if post is builtin"""
    return any(post_id.startswith(prefix) for prefix in BUILTIN_POST_IDS)


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/", response_model=Dict[str, List[PostListItem]])
def list_posts() -> Dict[str, List[PostListItem]]:
    """List all posts (builtin + custom)"""
    posts = load_all_posts()
    items = [
        PostListItem(
            id=post.id,
            name=post.name,
            builtin=post.builtin,
            description=post.description
        )
        for post in posts
    ]
    return {"posts": items}


@router.get("/{post_id}", response_model=PostConfig)
def get_post(post_id: str) -> PostConfig:
    """Get single post configuration"""
    post = find_post(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post '{post_id}' not found"
        )
    return post


@router.post("/", response_model=Dict[str, Any])
def create_post(body: PostCreateIn) -> Dict[str, Any]:
    """Create new custom post"""
    # Check if ID already exists
    if find_post(body.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Post '{body.id}' already exists"
        )
    
    # Check reserved prefixes
    if any(body.id.startswith(prefix) for prefix in BUILTIN_POST_IDS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Post ID cannot start with reserved prefixes: {BUILTIN_POST_IDS}"
        )
    
    # Create new post
    now = datetime.utcnow().isoformat() + 'Z'
    post = PostConfig(
        **body.dict(),
        builtin=False,
        created_at=now,
        updated_at=now
    )
    
    # Save to custom posts
    custom_posts = load_custom_posts()
    custom_posts.append(post)
    save_custom_posts(custom_posts)
    
    return {
        "id": post.id,
        "name": post.name,
        "builtin": False,
        "created_at": now
    }


@router.put("/{post_id}", response_model=Dict[str, Any])
def update_post(post_id: str, body: PostUpdateIn) -> Dict[str, Any]:
    """Update existing custom post"""
    # Find post
    post = find_post(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post '{post_id}' not found"
        )
    
    # Check builtin protection
    if post.builtin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot edit builtin post '{post_id}'"
        )
    
    # Update fields
    update_data = body.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(post, key, value)
    
    post.updated_at = datetime.utcnow().isoformat() + 'Z'
    
    # Save custom posts
    custom_posts = load_custom_posts()
    for i, p in enumerate(custom_posts):
        if p.id == post_id:
            custom_posts[i] = post
            break
    save_custom_posts(custom_posts)
    
    return {
        "id": post.id,
        "updated_at": post.updated_at
    }


@router.delete("/{post_id}", response_model=Dict[str, Any])
def delete_post(post_id: str) -> Dict[str, Any]:
    """Delete custom post"""
    # Find post
    post = find_post(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post '{post_id}' not found"
        )
    
    # Check builtin protection
    if post.builtin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot delete builtin post '{post_id}'"
        )
    
    # Remove from custom posts
    custom_posts = load_custom_posts()
    custom_posts = [p for p in custom_posts if p.id != post_id]
    save_custom_posts(custom_posts)
    
    return {
        "id": post_id,
        "deleted": True
    }


@router.post("/validate", response_model=ValidationResult)
def validate_post(body: PostCreateIn) -> ValidationResult:
    """Validate post configuration without saving"""
    errors = []
    warnings = []
    
    # Check ID conflicts
    if find_post(body.id):
        errors.append(f"Post ID '{body.id}' already exists")
    
    # Check reserved prefixes
    if any(body.id.startswith(prefix) for prefix in BUILTIN_POST_IDS):
        errors.append(f"Post ID cannot start with reserved prefixes: {BUILTIN_POST_IDS}")
    
    # Check header/footer not empty
    if not body.header:
        errors.append("Header cannot be empty")
    if not body.footer:
        errors.append("Footer cannot be empty")
    
    # Check line lengths
    for i, line in enumerate(body.header):
        if len(line) > 255:
            warnings.append(f"Header line {i+1} exceeds 255 characters")
    for i, line in enumerate(body.footer):
        if len(line) > 255:
            warnings.append(f"Footer line {i+1} exceeds 255 characters")
    
    return ValidationResult(
        valid=len(errors) == 0,
        warnings=warnings,
        errors=errors
    )


@router.get("/tokens/list", response_model=Dict[str, str])
def list_tokens() -> Dict[str, str]:
    """List all available tokens with descriptions"""
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
