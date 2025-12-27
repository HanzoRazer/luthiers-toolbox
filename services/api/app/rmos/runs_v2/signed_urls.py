"""
Signed URL utilities for RMOS attachments.

Provides HMAC-based URL signing with expiry for secure, stateless attachment access.
No secrets in the browser - frontend mints a signed URL via authenticated endpoint,
then uses the signed URL directly.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SignedUrlParams:
    expires: int
    sig: str
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
    """
    sec = os.getenv("RMOS_SIGNED_URL_SECRET", "").strip()
    if not sec:
        raise RuntimeError("RMOS_SIGNED_URL_SECRET is not set")
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
      DOWNLOAD(0/1)
      FILENAME(optional)
    """
    secret = _get_secret()
    payload = "\n".join(
        [
            method.upper(),
            path,
            str(int(expires)),
            sha256.lower(),
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
    download: bool = False,
    filename: Optional[str] = None,
    now_epoch: Optional[int] = None,
) -> bool:
    """
    Verify signature + expiry. Constant-time compare.
    """
    now = int(now_epoch if now_epoch is not None else time.time())
    if int(expires) < now:
        return False

    expected = sign_attachment_request(
        method=method,
        path=path,
        sha256=sha256,
        expires=int(expires),
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
        download=download,
        filename=filename,
    )
    return SignedUrlParams(expires=exp, sig=sig, download=download, filename=filename)
