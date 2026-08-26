"""Read-only evidence adapters for the Grounding Agent.

Every adapter here exposes read operations only. There is intentionally no
write adapter and no generic command runner (D1).
"""

from .filesystem import FileSystemAdapter
from .git_repo import GitRepoAdapter
from .github_api import (
    GitHubAdapter,
    GitHubAuthError,
    GitHubNotFound,
    GitHubUnavailable,
    HttpResponse,
)

__all__ = [
    "FileSystemAdapter",
    "GitRepoAdapter",
    "GitHubAdapter",
    "GitHubAuthError",
    "GitHubNotFound",
    "GitHubUnavailable",
    "HttpResponse",
]
