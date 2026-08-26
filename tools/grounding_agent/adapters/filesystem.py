"""Read-only filesystem adapter.

Only path existence checks are provided. Crucially, a local filesystem check is
never treated as proof of repository presence: repository-file claims are
answered by the Git/GitHub adapters at a named ref instead (see the engine).
"""

from __future__ import annotations

import os


class FileSystemAdapter:
    """Read-only path existence checks."""

    def local_path_exists(self, path: str) -> bool:
        """Whether ``path`` exists in the current local environment.

        The scope of this answer is the local environment only; the engine
        labels the result ``scope=LOCAL_ENVIRONMENT`` and phrases an absence as
        "not present in current environment" rather than "does not exist".
        """
        return os.path.exists(os.path.expanduser(path))

    def repo_path_exists(self, root: str, path: str) -> bool:
        """Whether ``path`` exists within the working tree rooted at ``root``.

        This is a working-tree check and is not ref-aware. Prefer the Git/ref
        adapter when a claim names a specific ref.
        """
        return os.path.exists(os.path.join(root, path))
