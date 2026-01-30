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

logger = logging.getLogger(__name__)


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
            # Convert PDF to image if needed
            if filename.lower().endswith('.pdf'):
                logger.info(f"Converting PDF {filename} to image at 300 DPI")
                images = convert_from_bytes(file_bytes, dpi=300, fmt='png')
                if not images:
                    raise ValueError("Could not convert PDF to image")
                
                # Use first page
                img_byte_arr = io.BytesIO()
                images[0].save(img_byte_arr, format='PNG')
                image_bytes = img_byte_arr.getvalue()
            else:
                image_bytes = file_bytes
            
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

            # Detect media type from filename extension
            ext = filename.lower().split('.')[-1] if '.' in filename else 'png'
            media_type_map = {
                'png': 'image/png',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'gif': 'image/gif',
                'webp': 'image/webp',
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
