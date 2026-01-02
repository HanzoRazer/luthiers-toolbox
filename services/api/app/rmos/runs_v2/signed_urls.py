"""
Signed URL utilities for RMOS attachments.

Provides HMAC-based URL signing with expiry for secure, stateless attachment access.
No secrets in the browser - frontend mints a signed URL via authenticated endpoint,
then uses the signed URL directly.

Unified signing module (Decision B): All RMOS signing uses this module.
Hierarchical scopes (Decision B): download ⊇ head (download token valid for HEAD).

Env vars:
  RMOS_SIGNED_URL_SECRET - Primary signing secret (required for signed URLs)
  RMOS_ACOUSTICS_SIGNING_SECRET - Legacy alias, falls back to primary if not set
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time
from dataclasses import dataclass
from typing import Literal, Optional

# Scope hierarchy: download implies head access
Scope = Literal["download", "head"]
SCOPE_HIERARCHY = {"download": {"download", "head"}, "head": {"head"}}


@dataclass(frozen=True)
class SignedUrlParams:
    expires: int
    sig: str
    scope: Scope = "download"
    download: bool = False
    filename: Optional[str] = None


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(s: str) -> bytes:
    # restore padding
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + pad).encode("ascii"))


def _get_secret() -> bytes:
    """
    Secret used to sign URLs. MUST be set in environment.

    Checks RMOS_SIGNED_URL_SECRET first, then legacy RMOS_ACOUSTICS_SIGNING_SECRET.
    """
    sec = os.getenv("RMOS_SIGNED_URL_SECRET", "").strip()
    if not sec:
        # Fallback to legacy env var for backward compatibility
        sec = os.getenv("RMOS_ACOUSTICS_SIGNING_SECRET", "").strip()
    if not sec:
        raise RuntimeError("RMOS_SIGNED_URL_SECRET (or RMOS_ACOUSTICS_SIGNING_SECRET) is not set")
    return sec.encode("utf-8")


def _canon_bool(b: bool) -> str:
    return "1" if b else "0"


def _canon_filename(filename: Optional[str]) -> str:
    if not filename:
        return ""
    # keep it simple: strip newlines, avoid quotes
    f = filename.replace("\n", " ").replace("\r", " ").replace('"', "'").strip()
    return f


def sign_attachment_request(
    *,
    method: str,
    path: str,
    sha256: str,
    expires: int,
    scope: Scope = "download",
    download: bool = False,
    filename: Optional[str] = None,
) -> str:
    """
    Returns a base64url signature string.

    We sign the *full request path* (including router prefix) so verification is unambiguous.

    Payload format (line-delimited):
      METHOD
      PATH
      EXPIRES
      SHA256
      SCOPE
      DOWNLOAD(0/1)
      FILENAME(optional)

    Scope is included in signature to prevent token replay across endpoints.
    """
    secret = _get_secret()
    payload = "\n".join(
        [
            method.upper(),
            path,
            str(int(expires)),
            sha256.lower(),
            scope,  # Added: scope binding
            _canon_bool(download),
            _canon_filename(filename),
        ]
    ).encode("utf-8")

    mac = hmac.new(secret, payload, hashlib.sha256).digest()
    return _b64url(mac)


def verify_attachment_request(
    *,
    method: str,
    path: str,
    sha256: str,
    expires: int,
    sig: str,
    scope: Scope = "download",
    required_scope: Optional[Scope] = None,
    download: bool = False,
    filename: Optional[str] = None,
    now_epoch: Optional[int] = None,
) -> bool:
    """
    Verify signature + expiry + scope. Constant-time compare.

    Args:
        scope: The scope the token was signed with
        required_scope: The scope required for this operation (defaults to scope)

    Hierarchical scope check (Decision B):
        - download token is valid for both download and head
        - head token is valid only for head
    """
    now = int(now_epoch if now_epoch is not None else time.time())
    if int(expires) < now:
        return False

    # Hierarchical scope check
    if required_scope is not None:
        allowed_scopes = SCOPE_HIERARCHY.get(scope, {scope})
        if required_scope not in allowed_scopes:
            return False

    expected = sign_attachment_request(
        method=method,
        path=path,
        sha256=sha256,
        expires=int(expires),
        scope=scope,
        download=download,
        filename=filename,
    )

    return hmac.compare_digest(expected, sig)


def make_signed_query(
    *,
    method: str,
    path: str,
    sha256: str,
    ttl_seconds: int = 300,
    scope: Scope = "download",
    download: bool = False,
    filename: Optional[str] = None,
    now_epoch: Optional[int] = None,
) -> SignedUrlParams:
    """
    Build signed query params for an attachment request.
    """
    now = int(now_epoch if now_epoch is not None else time.time())
    exp = now + int(ttl_seconds)
    sig = sign_attachment_request(
        method=method,
        path=path,
        sha256=sha256,
        expires=exp,
        scope=scope,
        download=download,
        filename=filename,
    )
    return SignedUrlParams(expires=exp, sig=sig, scope=scope, download=download, filename=filename)
