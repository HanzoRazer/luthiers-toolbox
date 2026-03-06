"""
Blueprint Analyzer - Claude Sonnet 4 Integration
Extracts dimensions, scale, and measurements from blueprint PDFs and images
"""
import base64
import io
import json
import logging
import os
import uuid
from typing import Dict, Optional

try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
    USE_EMERGENT = True
except ImportError:
    # Fallback to Anthropic SDK
    try:
        import anthropic
        USE_EMERGENT = False
    except ImportError:
        raise ImportError("Either emergentintegrations or anthropic package required")

from pdf2image import convert_from_bytes
from PIL import Image
# Optional DXF support
try:
    from .dxf_parser import DXFParser, is_dxf_file
    HAS_DXF_PARSER = True
except ImportError:
    HAS_DXF_PARSER = False
    def is_dxf_file(file_bytes, filename):
        return filename.lower().endswith(".dxf")

# Disable PIL decompression bomb protection for large blueprints
# High-resolution blueprint PDFs (300 DPI A2/A1 size) can exceed default 89M pixel limit
Image.MAX_IMAGE_PIXELS = None

logger = logging.getLogger(__name__)

# Claude API has a 5MB limit per image (for base64-encoded data)
# Base64 encoding adds ~33% overhead, so raw image must be < 3.5MB to stay safely under 5MB base64
# Using 3.5MB instead of 3.75MB for extra safety margin
MAX_IMAGE_SIZE_BYTES = int(3.5 * 1024 * 1024)  # ~3.5 MB raw = ~4.7 MB base64 (safe margin)

# Claude API has an 8000 pixel max dimension limit
MAX_IMAGE_DIMENSION = 8000

# Maximum total pixels before we force a resize (helps with large blueprint PDFs)
# 4000x4000 = 16M pixels is a reasonable limit for Claude vision
MAX_TOTAL_PIXELS = 16_000_000


def _resize_image_if_needed(image_bytes: bytes, max_size_bytes: int = MAX_IMAGE_SIZE_BYTES, max_dimension: int = MAX_IMAGE_DIMENSION) -> bytes:
    """
    Resize image if it exceeds the max size or dimension limits.

    Constraints:
    - Max file size: ~3.5 MB (to stay under 5 MB after base64 encoding)
    - Max dimension: 8000 pixels on any side
    - Max total pixels: 16 million (to prevent memory issues)

    Progressively reduces quality and dimensions until all limits are met.
    """
    img = Image.open(io.BytesIO(image_bytes))
    original_size = len(image_bytes)
    original_dims = f"{img.width}x{img.height}"
    total_pixels = img.width * img.height

    logger.info(f"_resize_image_if_needed: input={original_size:,} bytes, dims={original_dims}, pixels={total_pixels:,}")

    # Check all constraints
    needs_dimension_resize = img.width > max_dimension or img.height > max_dimension
    needs_pixel_resize = total_pixels > MAX_TOTAL_PIXELS
    needs_size_resize = original_size > max_size_bytes

    if not needs_dimension_resize and not needs_pixel_resize and not needs_size_resize:
        logger.info(f"_resize_image_if_needed: no resize needed, returning original")
        return image_bytes

    logger.info(f"_resize_image_if_needed: needs_dimension={needs_dimension_resize}, needs_pixel={needs_pixel_resize}, needs_size={needs_size_resize}")

    # Convert to RGB early (required for JPEG output)
    if img.mode in ('RGBA', 'P', 'LA', 'L'):
        img = img.convert('RGB')
        logger.info(f"Converted to RGB mode")

    # Calculate scale factor needed for dimension/pixel constraints
    dim_scale = 1.0
    if needs_dimension_resize:
        dim_scale = min(dim_scale, max_dimension / max(img.width, img.height))
    if needs_pixel_resize:
        pixel_scale = (MAX_TOTAL_PIXELS / total_pixels) ** 0.5
        dim_scale = min(dim_scale, pixel_scale)

    # For very large images, start with a more aggressive initial scale
    if original_size > max_size_bytes * 2:
        # Image is more than 2x the limit - start smaller
        estimated_scale = (max_size_bytes / original_size) ** 0.5 * 0.8  # 80% of estimated
        dim_scale = min(dim_scale, estimated_scale)
        logger.info(f"Large image detected, applying estimated scale: {dim_scale:.2f}")

    # Apply dimension scaling if needed
    if dim_scale < 1.0:
        new_width = max(100, int(img.width * dim_scale))
        new_height = max(100, int(img.height * dim_scale))
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        logger.info(f"Resized to {new_width}x{new_height} (scale={dim_scale:.2f})")

    # Now try different quality levels to meet size constraint
    for quality in [85, 70, 55, 40, 30, 20]:
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        result = output.getvalue()
        if len(result) <= max_size_bytes:
            logger.info(f"Final image: {img.width}x{img.height}, {len(result):,} bytes, quality={quality}")
            return result
        logger.debug(f"Quality {quality}: {len(result):,} bytes (still over {max_size_bytes:,})")

    # If quality reduction isn't enough, also reduce dimensions further
    scale_factors = [0.75, 0.6, 0.5, 0.4, 0.3, 0.25, 0.2, 0.15, 0.1]
    for scale in scale_factors:
        new_width = max(100, int(img.width * scale))
        new_height = max(100, int(img.height * scale))
        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        for quality in [70, 50, 30]:
            output = io.BytesIO()
            resized.save(output, format='JPEG', quality=quality, optimize=True)
            result = output.getvalue()

            if len(result) <= max_size_bytes:
                logger.info(f"Resized image to {new_width}x{new_height}, quality={quality} ({len(result):,} bytes)")
                return result

    # Last resort: very aggressive resize
    new_width = max(100, int(img.width * 0.05))
    new_height = max(100, int(img.height * 0.05))
    resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    output = io.BytesIO()
    resized.save(output, format='JPEG', quality=40, optimize=True)
    result = output.getvalue()
    logger.warning(f"Aggressively resized image to {new_width}x{new_height} ({len(result):,} bytes)")
    return result


class BlueprintAnalyzer:
    """AI-powered blueprint dimension analyzer using Claude Sonnet 4"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize analyzer with API key
        
        Args:
            api_key: API key for Claude (EMERGENT_LLM_KEY or ANTHROPIC_API_KEY)
        """
        self.api_key = api_key or os.environ.get('EMERGENT_LLM_KEY') or os.environ.get('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("EMERGENT_LLM_KEY or ANTHROPIC_API_KEY environment variable required")
        
        self.use_emergent = USE_EMERGENT
        if not USE_EMERGENT:
            self.client = anthropic.Anthropic(api_key=self.api_key)
    
    async def analyze_from_bytes(self, file_bytes: bytes, filename: str) -> Dict:
        """
        Analyze blueprint from raw file bytes
        
        Args:
            file_bytes: PDF or image file bytes
            filename: Original filename (used to detect PDF)
        
        Returns:
            Dictionary with:
            - scale: Detected scale (e.g., "1/4\" = 1'")
            - scale_confidence: high/medium/low
            - dimensions: List of detected dimensions
            - notes: General observations
        """
        try:
            # Handle DXF files directly (no AI analysis needed - contains vector geometry)
            if is_dxf_file(file_bytes, filename):
                if not HAS_DXF_PARSER:
                    raise ImportError("ezdxf package required for DXF files. Install with: pip install ezdxf")
                parser = DXFParser()
                return parser.parse_from_bytes(file_bytes, filename)

            # Convert PDF to image if needed
            if filename.lower().endswith('.pdf'):
                # Use adaptive DPI based on file size
                # Large PDFs (blueprints) at 300 DPI can produce 50MB+ images
                # Start with lower DPI for large files to avoid memory issues
                pdf_size_mb = len(file_bytes) / (1024 * 1024)
                if pdf_size_mb > 5:
                    dpi = 150  # Large PDF - use lower DPI
                elif pdf_size_mb > 2:
                    dpi = 200  # Medium PDF
                else:
                    dpi = 300  # Small PDF - use full resolution

                logger.info(f"Converting PDF {filename} ({pdf_size_mb:.1f} MB) to image at {dpi} DPI")
                images = convert_from_bytes(file_bytes, dpi=dpi, fmt='png')
                if not images:
                    raise ValueError("Could not convert PDF to image")

                # Use first page
                img_byte_arr = io.BytesIO()
                images[0].save(img_byte_arr, format='PNG')
                image_bytes = img_byte_arr.getvalue()
                logger.info(f"PDF converted to {len(image_bytes):,} byte PNG")
            else:
                image_bytes = file_bytes

            # Resize image if it exceeds Claude's 5MB limit
            image_bytes = _resize_image_if_needed(image_bytes)

            # Analyze with Claude
            return await self._analyze_with_claude(image_bytes, filename)
        
        except Exception as e:
            logger.error(f"Error analyzing blueprint {filename}: {e}")
            raise
    
    async def _analyze_with_claude(self, image_bytes: bytes, filename: str) -> Dict:
        """
        Use Claude Sonnet 4 vision to extract dimensions
        
        Args:
            image_bytes: PNG/JPG image bytes
            filename: Original filename (for logging)
        
        Returns:
            Structured analysis dictionary
        """
        try:
            # Encode image as base64
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')

            # Detect media type from image bytes (magic numbers)
            # This is more reliable than filename, especially after resizing
            if image_bytes[:3] == b'\xff\xd8\xff':
                detected_media_type = 'image/jpeg'
            elif image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
                detected_media_type = 'image/png'
            elif image_bytes[:6] in (b'GIF87a', b'GIF89a'):
                detected_media_type = 'image/gif'
            elif image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
                detected_media_type = 'image/webp'
            elif image_bytes[:2] == b'BM':
                # BMP file detected - will be converted to PNG
                detected_media_type = 'image/png'
            else:
                # Fallback to filename extension
                ext = filename.lower().split('.')[-1] if '.' in filename else 'png'
                media_type_map = {
                    'png': 'image/png',
                    'jpg': 'image/jpeg',
                    'jpeg': 'image/jpeg',
                    'gif': 'image/gif',
                    'webp': 'image/webp',
                    'bmp': 'image/png',  # BMP converted to PNG
                    'pdf': 'image/png',  # PDF converted to PNG
                }
                detected_media_type = media_type_map.get(ext, 'image/png')

            prompt = """Analyze this construction blueprint image and provide detailed measurement information:

1. Identify ALL visible dimensions and measurements on the blueprint
2. Detect the scale (e.g., 1/4" = 1', 1:100, full size, etc.) - look for scale notation or infer from existing measurements
3. For any unmarked distances, estimate dimensions based on the detected scale
4. List each dimension with:
   - Location description (e.g., "north wall length", "body width", "neck length", etc.)
   - Measured/detected value
   - Whether it's an existing measurement or estimated
   - Confidence level (high/medium/low)

If this is a guitar body/neck blueprint, identify the model if possible (e.g., Les Paul, Stratocaster, Telecaster, etc.).

Provide your response in JSON format:
{
  "scale": "detected or assumed scale",
  "scale_confidence": "high/medium/low",
  "dimensions": [
    {
      "label": "description of what is measured",
      "value": "measurement with units",
      "type": "detected" or "estimated",
      "confidence": "high/medium/low",
      "notes": "any relevant notes"
    }
  ],
  "blueprint_type": "architectural/guitar/mechanical/other",
  "detected_model": "model name if applicable",
  "notes": "general observations about the blueprint"
}"""
            
            logger.info(f"Analyzing {filename} with Claude Sonnet 4...")
            
            if self.use_emergent:
                # Use emergentintegrations library
                chat = LlmChat(
                    api_key=self.api_key,
                    session_id=f"blueprint-{uuid.uuid4()}",
                    system_message=(
                        "You are an expert construction blueprint analyzer. "
                        "Analyze blueprints to detect dimensions, scales, and measurements with precision. "
                        "For guitar lutherie blueprints, recognize common shapes like Les Paul, Stratocaster, etc."
                    )
                ).with_model("anthropic", "claude-sonnet-4-20250514")
                
                image_content = ImageContent(image_base64=image_b64)
                user_message = UserMessage(
                    text=prompt,
                    file_contents=[image_content]
                )
                
                response = await chat.send_message(user_message)
            else:
                # Use Anthropic SDK directly
                message = self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4096,
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": detected_media_type,
                                    "data": image_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ],
                    }],
                    system="You are an expert construction blueprint analyzer. Analyze blueprints to detect dimensions, scales, and measurements with precision. For guitar lutherie blueprints, recognize common shapes like Les Paul, Stratocaster, etc."
                )
                
                response = message.content[0].text
            
            # Parse JSON response
            response_text = response.strip() if isinstance(response, str) else str(response)
            
            # Check for processing errors
            if "could not process" in response_text.lower() or "unable to analyze" in response_text.lower():
                logger.warning(f"Claude image processing issue: {response_text[:200]}")
                return {
                    "scale": "Unable to detect",
                    "scale_confidence": "low",
                    "dimensions": [],
                    "notes": "Image quality or format may not be optimal. Try higher resolution or clearer scan.",
                    "error": "image_processing_failed"
                }
            
            # Extract JSON from markdown code blocks if present
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            analysis_data = json.loads(response_text)
            logger.info(f"Successfully analyzed {filename}: {len(analysis_data.get('dimensions', []))} dimensions detected")
            return analysis_data
        
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing error: {e}")
            return {
                "scale": "Unable to detect",
                "scale_confidence": "low",
                "dimensions": [],
                "notes": response[:500] if len(response) < 500 else response[:500] + "...",
                "raw_response": response
            }
        
        except Exception as e:
            logger.error(f"Error in Claude analysis: {e}")
            raise


def create_analyzer() -> BlueprintAnalyzer:
    """Factory function to create analyzer instance"""
    return BlueprintAnalyzer()
