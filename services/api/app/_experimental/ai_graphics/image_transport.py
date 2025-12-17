#!/usr/bin/env python3
"""
Image Transport Layer — HTTP/SDK for Image Generation APIs

GOVERNANCE CONTRACT:
    Transport returns: tuple[bytes, Dict[str, Any]]
    Transport method: generate_image_bytes()
    
This module handles RAW HTTP calls only. No business logic.
Provider layer (providers.py) handles normalization.

Author: Luthier's ToolBox
Date: December 17, 2025
"""

from __future__ import annotations

import os
import time
import logging
import base64
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional, Any, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class ImageTransportConfig:
    """Configuration for image transport clients."""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout_seconds: int = 120
    max_retries: int = 3
    retry_delay_seconds: float = 1.0


# =============================================================================
# ABSTRACT TRANSPORT
# =============================================================================

class ImageTransport(ABC):
    """
    Abstract base for image generation transport.
    
    GOVERNANCE: Returns tuple[bytes, dict], nothing else.
    """
    
    def __init__(self, config: Optional[ImageTransportConfig] = None):
        self.config = config or ImageTransportConfig()
    
    @abstractmethod
    def generate_image_bytes(
        self,
        *,
        prompt: str,
        size: str = "1024x1024",
        format: str = "png",
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Generate image and return raw bytes.
        
        Returns:
            tuple[bytes, dict]: (image_bytes, metadata)
            
        Raises:
            RuntimeError: On generation failure
        """
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if service is reachable."""
        pass
    
    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if client has required configuration."""
        pass


# =============================================================================
# OPENAI / DALL-E TRANSPORT
# =============================================================================

class OpenAIImageTransport(ImageTransport):
    """
    Transport for OpenAI DALL-E API.
    
    Returns raw image bytes from DALL-E generation.
    """
    
    def __init__(self, config: Optional[ImageTransportConfig] = None):
        super().__init__(config)
        self._client = None
        
        if not self.config.api_key:
            self.config.api_key = os.environ.get("OPENAI_API_KEY")
    
    @property
    def is_configured(self) -> bool:
        return bool(self.config.api_key)
    
    def _get_client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            try:
                import openai
                self._client = openai.OpenAI(api_key=self.config.api_key)
            except ImportError:
                raise RuntimeError("openai package not installed: pip install openai")
        return self._client
    
    def health_check(self) -> bool:
        """Check OpenAI API connectivity."""
        if not self.is_configured:
            return False
        try:
            client = self._get_client()
            client.models.list()
            return True
        except Exception:
            return False
    
    def generate_image_bytes(
        self,
        *,
        prompt: str,
        size: str = "1024x1024",
        format: str = "png",
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bytes, Dict[str, Any]]:
        """Generate image via DALL-E, return bytes."""
        
        if not self.is_configured:
            raise RuntimeError("OPENAI_API_KEY not configured")
        
        options = options or {}
        model = model or "dall-e-3"
        
        # Map size to DALL-E supported sizes
        dalle_size = self._map_size(size)
        
        # Map quality
        quality = options.get("quality", "standard")
        dalle_quality = "hd" if quality in ("hd", "ultra") else "standard"
        
        client = self._get_client()
        
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                # Request b64_json for direct bytes
                response = client.images.generate(
                    model=model,
                    prompt=prompt,
                    size=dalle_size,
                    quality=dalle_quality,
                    response_format="b64_json",
                    n=1,
                )
                
                # Decode base64 to bytes
                b64_data = response.data[0].b64_json
                image_bytes = base64.b64decode(b64_data)
                
                metadata = {
                    "model": model,
                    "revised_prompt": response.data[0].revised_prompt,
                    "size": dalle_size,
                    "quality": dalle_quality,
                }
                
                return image_bytes, metadata
                
            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    logger.warning(f"DALL-E attempt {attempt + 1} failed: {e}")
                    time.sleep(self.config.retry_delay_seconds)
        
        raise RuntimeError(f"DALL-E generation failed after {self.config.max_retries} attempts: {last_error}")
    
    def _map_size(self, size: str) -> str:
        """Map size string to DALL-E supported sizes."""
        # DALL-E 3 supports: 1024x1024, 1792x1024, 1024x1792
        if "x" in size:
            w, h = size.split("x")
            w, h = int(w), int(h)
            if w == h:
                return "1024x1024"
            elif w > h:
                return "1792x1024"
            else:
                return "1024x1792"
        return "1024x1024"


# =============================================================================
# STABLE DIFFUSION TRANSPORT
# =============================================================================

class StableDiffusionTransport(ImageTransport):
    """
    Transport for Stable Diffusion APIs (Automatic1111, ComfyUI).
    
    Returns raw image bytes from SD generation.
    """
    
    def __init__(self, config: Optional[ImageTransportConfig] = None):
        super().__init__(config)
        
        if not self.config.base_url:
            self.config.base_url = os.environ.get("SD_API_URL", "http://localhost:7860")
    
    @property
    def is_configured(self) -> bool:
        return bool(self.config.base_url)
    
    def health_check(self) -> bool:
        """Check SD API connectivity."""
        try:
            import requests
            resp = requests.get(
                f"{self.config.base_url}/sdapi/v1/options",
                timeout=5
            )
            return resp.status_code == 200
        except Exception:
            return False
    
    def generate_image_bytes(
        self,
        *,
        prompt: str,
        size: str = "1024x1024",
        format: str = "png",
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bytes, Dict[str, Any]]:
        """Generate image via SD API, return bytes."""
        import requests
        
        options = options or {}
        
        # Parse size
        if "x" in size:
            width, height = map(int, size.split("x"))
        else:
            width, height = 1024, 1024
        
        # Map quality to steps
        quality = options.get("quality", "standard")
        steps_map = {"draft": 15, "standard": 25, "hd": 35, "ultra": 50}
        steps = steps_map.get(quality, 25)
        
        # Build payload
        payload = {
            "prompt": prompt,
            "negative_prompt": options.get("negative_prompt", ""),
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": options.get("cfg_scale", 7.5),
            "sampler_name": options.get("sampler", "DPM++ 2M Karras"),
            "seed": options.get("seed", -1),
        }
        
        # Add LoRA if specified
        if options.get("lora_name"):
            lora_weight = options.get("lora_weight", 0.8)
            payload["prompt"] = f"<lora:{options['lora_name']}:{lora_weight}> {prompt}"
        
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                resp = requests.post(
                    f"{self.config.base_url}/sdapi/v1/txt2img",
                    json=payload,
                    timeout=self.config.timeout_seconds,
                )
                resp.raise_for_status()
                
                data = resp.json()
                
                # SD returns base64 images
                if not data.get("images"):
                    raise RuntimeError("No images in SD response")
                
                image_bytes = base64.b64decode(data["images"][0])
                
                metadata = {
                    "model": model or "sd",
                    "seed": data.get("info", {}).get("seed"),
                    "size": size,
                }
                
                return image_bytes, metadata
                
            except requests.exceptions.Timeout:
                last_error = f"Timeout after {self.config.timeout_seconds}s"
            except requests.exceptions.ConnectionError:
                last_error = f"Connection failed to {self.config.base_url}"
            except Exception as e:
                last_error = str(e)
            
            if attempt < self.config.max_retries - 1:
                logger.warning(f"SD attempt {attempt + 1} failed: {last_error}")
                time.sleep(self.config.retry_delay_seconds)
        
        raise RuntimeError(f"SD generation failed after {self.config.max_retries} attempts: {last_error}")


# =============================================================================
# STUB TRANSPORT (Testing)
# =============================================================================

class StubImageTransport(ImageTransport):
    """
    Stub transport for testing without real API calls.
    Returns deterministic placeholder bytes.
    """
    
    def __init__(self, config: Optional[ImageTransportConfig] = None):
        super().__init__(config)
        self.call_count = 0
        self.last_prompt: Optional[str] = None
    
    @property
    def is_configured(self) -> bool:
        return True
    
    def health_check(self) -> bool:
        return True
    
    def generate_image_bytes(
        self,
        *,
        prompt: str,
        size: str = "1024x1024",
        format: str = "png",
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bytes, Dict[str, Any]]:
        """Generate placeholder image bytes."""
        import hashlib
        
        self.call_count += 1
        self.last_prompt = prompt
        
        # Create minimal valid PNG (1x1 pixel)
        # This is a real PNG that image libraries can read
        png_header = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D,  # IHDR length
            0x49, 0x48, 0x44, 0x52,  # IHDR
            0x00, 0x00, 0x00, 0x01,  # width: 1
            0x00, 0x00, 0x00, 0x01,  # height: 1
            0x08, 0x02,              # 8-bit RGB
            0x00, 0x00, 0x00,        # compression, filter, interlace
            0x90, 0x77, 0x53, 0xDE,  # CRC
            0x00, 0x00, 0x00, 0x0C,  # IDAT length
            0x49, 0x44, 0x41, 0x54,  # IDAT
            0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0xFF, 0x00,  # compressed data
            0x05, 0xFE, 0x02, 0xFE,  # CRC
            0x00, 0x00, 0x00, 0x00,  # IEND length
            0x49, 0x45, 0x4E, 0x44,  # IEND
            0xAE, 0x42, 0x60, 0x82,  # CRC
        ])
        
        # Hash prompt for deterministic "variation"
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
        
        metadata = {
            "model": "stub",
            "prompt_hash": prompt_hash,
            "size": size,
            "stub": True,
        }
        
        return png_header, metadata


# =============================================================================
# FACTORY
# =============================================================================

def get_image_transport(provider: str = "stub") -> ImageTransport:
    """
    Get image transport by provider name.
    
    Args:
        provider: "openai", "dalle", "sd", "stable_diffusion", "stub"
    
    Returns:
        Configured ImageTransport instance
    """
    provider = provider.lower()
    
    if provider in ("openai", "dalle", "dall-e", "dalle3"):
        return OpenAIImageTransport()
    elif provider in ("sd", "stable_diffusion", "sdxl", "sd15"):
        return StableDiffusionTransport()
    else:
        return StubImageTransport()
