from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time
from dataclasses import dataclass
from typing import Optional


def _secret() -> bytes:
    s = os.getenv("RMOS_ACOUSTICS_SIGNING_SECRET", "").strip()
    if not s:
        raise RuntimeError("RMOS_ACOUSTICS_SIGNING_SECRET is not set")
    return s.encode("utf-8")


def _default_ttl_seconds() -> int:
    v = os.getenv("RMOS_ACOUSTICS_SIGNING_TTL_SECONDS", "").strip()
    if not v:
        return 300
    try:
        return max(30, int(v))
    except Exception:
        return 300


def _bind_ip_enabled() -> bool:
    return os.getenv("RMOS_ACOUSTICS_SIGNING_BIND_IP", "0").strip() in ("1", "true", "True", "yes", "YES")


def _urlsafe_b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _unurlsafe_b64(s: str) -> bytes:
    pad = "=" * ((4 - (len(s) % 4)) % 4)
    return base64.urlsafe_b64decode((s + pad).encode("utf-8"))


@dataclass(frozen=True)
class SignedAttachmentToken:
    sha256: str
    exp: int
    ext: str
    download: int
    ip: str  # may be "" if not bound
    sig: str

    def to_query(self) -> dict[str, str]:
        return {
            "exp": str(self.exp),
            "ext": self.ext,
            "dl": str(self.download),
            "ip": self.ip,
            "sig": self.sig,
        }


def _canonical_message(*, sha256: str, exp: int, ext: str, download: int, ip: str) -> bytes:
    # Keep stable field order.
    # ext is included so a signature cannot be reused for a different blob suffix.
    msg = f"sha256={sha256}&exp={exp}&ext={ext}&dl={download}&ip={ip}".encode("utf-8")
    return msg


def sign_attachment(
    *,
    sha256: str,
    ext: str,
    download: int = 1,
    ttl_seconds: Optional[int] = None,
    client_ip: str = "",
) -> SignedAttachmentToken:
    if ttl_seconds is None:
        ttl_seconds = _default_ttl_seconds()
    exp = int(time.time()) + int(ttl_seconds)

    ip = client_ip if _bind_ip_enabled() else ""

    msg = _canonical_message(sha256=sha256, exp=exp, ext=ext, download=download, ip=ip)
    mac = hmac.new(_secret(), msg, hashlib.sha256).digest()
    sig = _urlsafe_b64(mac)

    return SignedAttachmentToken(
        sha256=sha256,
        exp=exp,
        ext=ext,
        download=download,
        ip=ip,
        sig=sig,
    )


def verify_attachment(
    *,
    sha256: str,
    exp: int,
    ext: str,
    download: int,
    ip: str,
    sig: str,
    now: Optional[int] = None,
    client_ip: str = "",
) -> None:
    if now is None:
        now = int(time.time())
    if exp < now:
        raise ValueError("expired")

    expected_ip = client_ip if _bind_ip_enabled() else ""
    if expected_ip != (ip or ""):
        raise ValueError("ip_mismatch")

    msg = _canonical_message(sha256=sha256, exp=exp, ext=ext, download=download, ip=(ip or ""))
    mac = hmac.new(_secret(), msg, hashlib.sha256).digest()
    expected_sig = _urlsafe_b64(mac)

    # constant-time compare
    if not hmac.compare_digest(expected_sig, sig):
        raise ValueError("bad_sig")
