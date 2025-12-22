"""
Art Studio SVG Generator

Prompt→SVG generation using ai.image_client directly (Option 2).
Cleaner separation from Vision service, less coupling.

Flow:
    1. Safety check via ai.safety
    2. Image generation via ai.transport.image_client
    3. Vectorization to SVG (potrace or vtracer)
    4. Audit logging via ai.observability
"""
from __future__ import annotations

import io
import subprocess
import tempfile
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

# AI Platform imports (canonical layer)
from app.ai.transport import get_image_client, ImageResponse
from app.ai.safety import assert_allowed, SafetyCategory
from app.ai.observability import audit_ai_call, get_request_id, set_request_id
from app.ai.cost import estimate_image_cost

from .styles import get_style_prompt_suffix

logger = logging.getLogger(__name__)


class VectorizeMethod(str, Enum):
    """Supported vectorization methods."""
    POTRACE = "potrace"      # Classic bitmap tracer
    VTRACER = "vtracer"      # Rust-based, better curves
    AUTOTRACE = "autotrace"  # Alternative tracer
    NONE = "none"            # Return PNG, no vectorization


@dataclass
class SVGGeneratorConfig:
    """Configuration for SVG generation."""
    provider: str = "openai"
    model: str = "dall-e-3"
    size: str = "1024x1024"
    quality: str = "standard"
    vectorize_method: VectorizeMethod = VectorizeMethod.POTRACE
    style: str = "line_art"

    # Vectorization options
    potrace_turdsize: int = 2      # Suppress speckles up to this size
    potrace_alphamax: float = 1.0  # Corner threshold
    potrace_opttolerance: float = 0.2  # Curve optimization

    # vtracer options
    vtracer_colormode: str = "binary"  # "color", "binary"
    vtracer_filter_speckle: int = 4

    # Output options
    optimize_svg: bool = True
    embed_metadata: bool = True


@dataclass
class SVGResult:
    """Result of SVG generation."""
    svg_content: str
    png_bytes: Optional[bytes] = None
    provider: str = ""
    model: str = ""
    revised_prompt: Optional[str] = None
    vectorize_method: str = ""
    cost_estimate_usd: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def svg_bytes(self) -> bytes:
        return self.svg_content.encode("utf-8")

    @property
    def size_bytes(self) -> int:
        return len(self.svg_content)


async def generate_svg_from_prompt(
    prompt: str,
    config: Optional[SVGGeneratorConfig] = None,
    include_png: bool = False,
) -> SVGResult:
    """
    Generate SVG from text prompt.

    Uses ai.image_client directly (Option 2 architecture).
    This provides cleaner separation from Vision service.

    Args:
        prompt: Text description of desired image
        config: Generation configuration
        include_png: If True, include original PNG bytes in result

    Returns:
        SVGResult with SVG content and metadata

    Raises:
        SafetyViolationError: If prompt violates safety policy
        ImageClientError: If image generation fails
        RuntimeError: If vectorization fails
    """
    config = config or SVGGeneratorConfig()

    # Ensure request ID exists
    if get_request_id() is None:
        set_request_id()

    # 1. Safety check
    safety_result = assert_allowed(
        prompt,
        category=SafetyCategory.GUITAR_PATTERN,
        request_id=get_request_id(),
    )

    # 2. Enhance prompt for SVG-friendly output
    style_suffix = get_style_prompt_suffix(config.style)
    enhanced_prompt = f"{prompt}, {style_suffix}"

    # 3. Cost estimation
    cost_estimate = estimate_image_cost(
        model=config.model,
        size=config.size,
        quality=config.quality,
    )

    # 4. Generate image via AI Platform
    image_client = get_image_client(provider=config.provider)
    image_response: ImageResponse = image_client.generate(
        prompt=enhanced_prompt,
        size=config.size,
        quality=config.quality,
        model=config.model,
    )

    # 5. Vectorize to SVG
    if config.vectorize_method == VectorizeMethod.NONE:
        # Return placeholder SVG with embedded PNG
        svg_content = _create_embedded_png_svg(
            image_response.image_bytes,
            config.size,
        )
    else:
        svg_content = _vectorize_to_svg(
            image_response.image_bytes,
            method=config.vectorize_method,
            config=config,
        )

    # 6. Optimize SVG if requested
    if config.optimize_svg and config.vectorize_method != VectorizeMethod.NONE:
        svg_content = _optimize_svg(svg_content)

    # 7. Embed metadata if requested
    if config.embed_metadata:
        svg_content = _embed_metadata(
            svg_content,
            prompt=prompt,
            provider=config.provider,
            model=config.model,
            revised_prompt=image_response.revised_prompt,
        )

    # 8. Audit log
    audit_ai_call(
        operation="image_to_svg",
        provider=config.provider,
        model=config.model,
        prompt=prompt,
        response_bytes=svg_content.encode(),
        revised_prompt=image_response.revised_prompt,
        cost_estimate_usd=cost_estimate.estimated_cost_usd,
        safety_level=safety_result.level.value,
        safety_category=safety_result.category.value,
        metadata={
            "vectorize_method": config.vectorize_method.value,
            "style": config.style,
            "size": config.size,
        },
    )

    return SVGResult(
        svg_content=svg_content,
        png_bytes=image_response.image_bytes if include_png else None,
        provider=config.provider,
        model=config.model,
        revised_prompt=image_response.revised_prompt,
        vectorize_method=config.vectorize_method.value,
        cost_estimate_usd=cost_estimate.estimated_cost_usd,
        metadata={
            "original_size": config.size,
            "style": config.style,
            "safety_level": safety_result.level.value,
            "image_sha256": image_response.sha256[:16],
        },
    )


def _vectorize_to_svg(
    png_bytes: bytes,
    method: VectorizeMethod,
    config: SVGGeneratorConfig,
) -> str:
    """
    Convert PNG bytes to SVG using specified method.

    Args:
        png_bytes: PNG image data
        method: Vectorization method
        config: Generator config with vectorization options

    Returns:
        SVG content as string
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        png_path = tmpdir / "input.png"
        svg_path = tmpdir / "output.svg"

        # Write PNG to temp file
        png_path.write_bytes(png_bytes)

        if method == VectorizeMethod.POTRACE:
            svg_content = _run_potrace(png_path, svg_path, config)
        elif method == VectorizeMethod.VTRACER:
            svg_content = _run_vtracer(png_path, svg_path, config)
        elif method == VectorizeMethod.AUTOTRACE:
            svg_content = _run_autotrace(png_path, svg_path, config)
        else:
            raise ValueError(f"Unknown vectorize method: {method}")

        return svg_content


def _run_potrace(
    png_path: Path,
    svg_path: Path,
    config: SVGGeneratorConfig,
) -> str:
    """Run potrace for vectorization."""
    # First convert PNG to PBM (potrace requires bitmap)
    pbm_path = png_path.with_suffix(".pbm")

    try:
        # Use ImageMagick or PIL to convert
        try:
            from PIL import Image
            img = Image.open(png_path).convert("1")  # 1-bit
            img.save(pbm_path, "PPM")
        except ImportError:
            # Fallback to ImageMagick
            subprocess.run(
                ["magick", "convert", str(png_path), "-threshold", "50%", str(pbm_path)],
                check=True,
                capture_output=True,
            )

        # Run potrace
        cmd = [
            "potrace",
            str(pbm_path),
            "-s",  # SVG output
            "-o", str(svg_path),
            "-t", str(config.potrace_turdsize),
            "-a", str(config.potrace_alphamax),
            "-O", str(config.potrace_opttolerance),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning(f"Potrace warning: {result.stderr}")

        if svg_path.exists():
            return svg_path.read_text()
        else:
            raise RuntimeError(f"Potrace failed to create SVG: {result.stderr}")

    except FileNotFoundError:
        # Potrace not installed - return fallback
        logger.warning("Potrace not found, using fallback SVG")
        return _create_fallback_svg(png_path, config.size)


def _run_vtracer(
    png_path: Path,
    svg_path: Path,
    config: SVGGeneratorConfig,
) -> str:
    """Run vtracer for vectorization."""
    try:
        cmd = [
            "vtracer",
            "--input", str(png_path),
            "--output", str(svg_path),
            "--colormode", config.vtracer_colormode,
            "--filter_speckle", str(config.vtracer_filter_speckle),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning(f"Vtracer warning: {result.stderr}")

        if svg_path.exists():
            return svg_path.read_text()
        else:
            raise RuntimeError(f"Vtracer failed: {result.stderr}")

    except FileNotFoundError:
        logger.warning("Vtracer not found, falling back to potrace")
        return _run_potrace(png_path, svg_path, config)


def _run_autotrace(
    png_path: Path,
    svg_path: Path,
    config: SVGGeneratorConfig,
) -> str:
    """Run autotrace for vectorization."""
    try:
        cmd = [
            "autotrace",
            "-output-file", str(svg_path),
            "-output-format", "svg",
            str(png_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if svg_path.exists():
            return svg_path.read_text()
        else:
            raise RuntimeError(f"Autotrace failed: {result.stderr}")

    except FileNotFoundError:
        logger.warning("Autotrace not found, falling back to potrace")
        return _run_potrace(png_path, svg_path, config)


def _create_fallback_svg(png_path: Path, size: str) -> str:
    """Create fallback SVG when no vectorizer is available."""
    w, h = map(int, size.split("x"))
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <rect width="100%" height="100%" fill="#f0f0f0"/>
  <text x="50%" y="50%" text-anchor="middle" dy=".3em" font-family="sans-serif" font-size="24">
    Vectorization unavailable - install potrace or vtracer
  </text>
</svg>'''


def _create_embedded_png_svg(png_bytes: bytes, size: str) -> str:
    """Create SVG with embedded PNG (no vectorization)."""
    import base64
    w, h = map(int, size.split("x"))
    b64 = base64.b64encode(png_bytes).decode()
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <image width="{w}" height="{h}" xlink:href="data:image/png;base64,{b64}"/>
</svg>'''


def _optimize_svg(svg_content: str) -> str:
    """Optimize SVG content (remove unnecessary elements, minify)."""
    # Basic optimization - remove XML declaration if present
    lines = svg_content.strip().split("\n")
    lines = [l for l in lines if not l.strip().startswith("<?xml")]

    # Remove empty groups
    content = "\n".join(lines)

    # Could use svgo here if available
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".svg", delete=False) as f:
            f.write(content)
            f.flush()

            result = subprocess.run(
                ["svgo", f.name, "-o", "-"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout
    except FileNotFoundError:
        pass  # svgo not available

    return content


def _embed_metadata(
    svg_content: str,
    prompt: str,
    provider: str,
    model: str,
    revised_prompt: Optional[str] = None,
) -> str:
    """Embed generation metadata in SVG as comments/metadata element."""
    import html

    metadata = f'''  <metadata>
    <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
             xmlns:dc="http://purl.org/dc/elements/1.1/">
      <rdf:Description>
        <dc:creator>Luthier's ToolBox AI</dc:creator>
        <dc:description>{html.escape(prompt[:200])}</dc:description>
        <dc:source>{provider}/{model}</dc:source>
      </rdf:Description>
    </rdf:RDF>
  </metadata>
'''

    # Insert metadata after opening svg tag
    if "<svg" in svg_content:
        # Find end of opening svg tag
        svg_end = svg_content.find(">", svg_content.find("<svg"))
        if svg_end != -1:
            return svg_content[:svg_end+1] + "\n" + metadata + svg_content[svg_end+1:]

    return svg_content
