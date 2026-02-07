# services/api/app/post_injection_dropin.py
# Patch N 0.3 — PostInjection (Drop-in, single file)
# Patch N.12 — Tool context injection
from __future__ import annotations
from typing import Callable, Dict, Any, List, Optional
from datetime import datetime
import os, json

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Patch N.12 — Tool table utilities
try:
    from .util.tool_table import tool_context
except ImportError:  # WP-1: narrowed from except Exception
    def tool_context(mid, tnum):
        return {}

# -----------------------------
# Config
# -----------------------------
TB_POST_INJECTION = os.environ.get("TB_POST_INJECTION", "auto").lower()  # auto|off|force
TB_POST_DEFAULT   = os.environ.get("TB_POST_DEFAULT", "")                # e.g., "grbl"
TB_POSTS_PATH     = os.environ.get("TB_POSTS_PATH", "services/api/app/data/posts.json") # posts.json location

# -----------------------------
# Minimal post utils (inline)
# -----------------------------
def _load_posts() -> List[Dict[str, Any]]:
    try:
        with open(TB_POSTS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Support both array format and {posts: [...]} format
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "posts" in data:
                return data["posts"]
            return []
    except FileNotFoundError:
        return []
    except (json.JSONDecodeError, ValueError) as e:  # WP-1: narrowed from except Exception
        # Keep CAM alive even if posts file is broken
        print(f"[post_injection_dropin] posts load failed: {e}")
        return []

def _find_post(post_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if not post_id:
        return None
    for p in _load_posts():
        if (p.get("id") or p.get("name")) == post_id:
            return p
    return None

def _build_tokens(*, units: str = "mm", program: str = "ToolBox", extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
    t = {
        "DATE": datetime.now().strftime("%Y-%m-%d"),
        "UNITS": (units or "mm").upper(),
        "PROGRAM": program,
    }
    if extra:
        for k, v in extra.items():
            if v is not None:
                t[k] = v
    return t

def _expand_lines(lines: List[str] | None, tokens: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    for ln in (lines or []):
        s = ln
        for k, v in tokens.items():
            s = s.replace("{"+k+"}", str(v))
        out.append(s)
    return out

def inject_header_footer(nc_text: str, post_id: str, *, tokens: Dict[str, Any]) -> str:
    """Wrap raw NC with header/footer expanded for the given post id."""
    post = _find_post(post_id)
    if not post:
        return nc_text if nc_text.endswith("\n") else (nc_text + "\n")
    
    # Patch N.12 — Merge tool context if machine_id + TOOL present
    try:
        tc = tool_context(tokens.get("machine_id"), tokens.get("TOOL"))
        if tc:
            # Merge tool context tokens (only non-None values)
            for k, v in tc.items():
                if v is not None:
                    tokens[k] = v
    except (KeyError, TypeError, AttributeError):  # WP-1: narrowed from except Exception
        pass
    
    header = _expand_lines(post.get("header"), tokens)
    footer = _expand_lines(post.get("footer"), tokens)
    parts: List[str] = []
    if header: parts.append("\n".join(header))
    parts.append(nc_text.rstrip())
    if footer: parts.append("\n".join(footer))
    return "\n\n".join(parts) + "\n"

# -----------------------------
# Lightweight router helpers
# -----------------------------
def build_post_context(**kwargs) -> Dict[str, Any]:
    """
    Collects post context for middleware.
    Common keys:
      post, post_mode ('auto'|'off'|'force'), units,
      TOOL, DIAM, FEED_XY, RPM, SAFE_Z, WORK_OFFSET, PROGRAM_NO, machine_id, etc.
    """
    ctx: Dict[str, Any] = {}
    for k, v in kwargs.items():
        if v is not None:
            ctx[k] = v
    return ctx

def set_post_headers(response: Response, ctx: Dict[str, Any]) -> None:
    """Routers call this once per response to hint the middleware."""
    response.headers["X-TB-Post-Context"] = json.dumps(ctx)

# -----------------------------
# Middleware (centralized)
# -----------------------------
class PostInjectionMiddleware(BaseHTTPMiddleware):
    """
    Wraps any `text/plain` response under /cam/* or /vcarve/* with post header/footer.
    Mode:
      - auto  : inject only if a post is provided (request/ctx or TB_POST_DEFAULT with post_mode='force')
      - off   : never inject
      - force : always inject using request/ctx post, or TB_POST_DEFAULT if absent
    """
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Only operate on text/plain payloads from CAM/VCarve paths
        ctype = (response.headers.get("content-type") or "").lower()
        if "text/plain" not in ctype:
            return response
        path = request.url.path
        if not (path.startswith("/cam") or path.startswith("/vcarve") or path.startswith("/api/cam") or path.startswith("/api/vcarve")):
            return response

        # Pull context (router sets it) and decide post & mode
        ctx_raw = response.headers.pop("X-TB-Post-Context", None)
        ctx: Dict[str, Any] = {}
        if ctx_raw:
            try: ctx = json.loads(ctx_raw)
            except (json.JSONDecodeError, ValueError): ctx = {}  # WP-1: narrowed from except Exception

        # Calculate effective mode and post
        mode  = str(ctx.get("post_mode") or TB_POST_INJECTION).lower()
        units = ctx.get("units", "mm")
        post_id = ctx.get("post")

        if mode == "off":
            return response
        if mode == "force":
            if not post_id:
                post_id = TB_POST_DEFAULT or post_id
        elif mode == "auto":
            # only inject if a post is present
            if not post_id:
                return response
        else:
            # Unknown mode → behave like 'auto'
            if not post_id:
                return response

        # Build tokens (rich) - Patch N.12: include machine_id for tool context
        extra = {
            "TOOL": ctx.get("TOOL"),
            "DIAM": ctx.get("DIAM"),
            "FEED_XY": ctx.get("FEED_XY"),
            "RPM": ctx.get("RPM"),
            "SAFE_Z": ctx.get("SAFE_Z"),
            "WORK_OFFSET": ctx.get("WORK_OFFSET"),
            "PROGRAM_NO": ctx.get("PROGRAM_NO"),
            "machine_id": ctx.get("machine_id"),  # Patch N.12
        }
        tokens = _build_tokens(units=units, program="ToolBox", extra=extra)

        # Read body into a string
        body_bytes = b""
        async for chunk in response.body_iterator:
            body_bytes += chunk
        try:
            nc_text = body_bytes.decode("utf-8", errors="ignore")
        except (UnicodeDecodeError, AttributeError):  # WP-1: narrowed from except Exception
            return response

        wrapped = inject_header_footer(nc_text, post_id, tokens=tokens)
        new = Response(content=wrapped, media_type="text/plain; charset=utf-8", status_code=response.status_code)

        # Preserve a couple of helpful headers if present
        for k in ("x-cam-summary", "x-request-id"):
            if k in response.headers:
                new.headers[k] = response.headers[k]
        return new

# -----------------------------
# Install helper
# -----------------------------
def install_post_middleware(app) -> None:
    """
    Call this in services/api/app/main.py once after constructing FastAPI(app).
    Example:
        from .post_injection_dropin import install_post_middleware
        install_post_middleware(app)
    """
    app.add_middleware(PostInjectionMiddleware)
