Here’s the **OpenAIProvider contract** (clean, authoritative) exactly as we’ve been using it — plus the surrounding `AiImageResult` + `AiImageProvider` interface so you can drop it into `services/api/app/_experimental/ai_graphics/services/providers.py` without drift.

---

## Canonical contract

### Data class

```py
from dataclasses import dataclass

@dataclass
class AiImageResult:
    """Result from image generation."""
    image_bytes: bytes
    format: str = "png"
    prompt_used: str = ""
    model: str = ""
```

### Provider interface

```py
from typing import Protocol, Optional, Dict, Any

class AiImageProvider(Protocol):
    def generate_image(
        self,
        prompt: str,
        *,
        size: str = "1024x1024",
        format: str = "png",
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> AiImageResult: ...
```

### ✅ OpenAIProvider (contract + implementation stub)

This is the key part you were missing:

```py
class OpenAIProvider:
    """
    OpenAI-backed provider using the transport layer in llm_client.py.

    HARD RULE:
    - providers.py owns normalization + provider selection
    - llm_client.py owns HTTP transport only
    """

    def __init__(self, llm_client: Any):
        self.client = llm_client

    def generate_image(
        self,
        prompt: str,
        *,
        size: str = "1024x1024",
        format: str = "png",
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> AiImageResult:
        prompt_used = (prompt or "").strip()
        if not prompt_used:
            raise ValueError("prompt is required")

        # Transport contract (one-way dependency):
        #   bytes_out, meta = client.generate_image_bytes(
        #       prompt=..., size=..., format=..., model=..., options=...
        #   )
        bytes_out, meta = self.client.generate_image_bytes(
            prompt=prompt_used,
            size=size,
            format=format,
            model=model,
            options=options or {},
        )

        if not isinstance(bytes_out, (bytes, bytearray)):
            raise RuntimeError(
                "llm_client.generate_image_bytes must return raw bytes as first value"
            )

        used_model = ""
        if isinstance(meta, dict):
            used_model = str(meta.get("model") or "")

        return AiImageResult(
            image_bytes=bytes(bytes_out),
            format=format,
            prompt_used=prompt_used,
            model=used_model or (model or ""),
        )
```

---

## And the required transport method signature (in `llm_client.py`)

For the contract above, your `LLMClient` must have:

```py
def generate_image_bytes(
    self,
    *,
    prompt: str,
    size: str = "1024x1024",
    format: str = "png",
    model: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
) -> tuple[bytes, Dict[str, Any]]:
    ...
```

(That’s the method we patched in.)

---

If you want, paste your current `providers.py` header (top ~60 lines) and I’ll tell you exactly where to insert this so you don’t create a second `AiImageResult` or a second provider registry again.




