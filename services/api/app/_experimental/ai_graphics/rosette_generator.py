#!/usr/bin/env python3
"""
AI Rosette Pattern Generator
Generates MatrixFormula JSON from natural language prompts.

"Do it like Sonny Pruitt" - just dive in and get it done.

Author: Luthier's ToolBox
Date: December 16, 2025
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Literal
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator


# ============================================================================
# PYDANTIC VALIDATION MODELS - AI Output Must Match These
# ============================================================================

class AIMatrixRow(BaseModel):
    """Single row in the matrix formula."""
    black: int = Field(ge=0, le=20, default=0)
    white: int = Field(ge=0, le=20, default=0)
    brown: int = Field(ge=0, le=20, default=0)
    
    @model_validator(mode='after')
    def at_least_one_material(self):
        total = self.black + self.white + self.brown
        if total < 1:
            raise ValueError("Each row must have at least 1 strip")
        if total > 20:
            raise ValueError("Row cannot exceed 20 total strips")
        return self


class AIMatrixFormula(BaseModel):
    """
    Validated matrix formula from AI generation.
    This is what the AI must produce.
    """
    name: str = Field(..., min_length=3, max_length=100)
    rows: List[Dict[str, int]] = Field(..., min_length=2, max_length=12)
    column_sequence: List[int] = Field(..., min_length=3, max_length=20)
    strip_width_mm: float = Field(default=1.0, ge=0.5, le=2.0)
    strip_thickness_mm: float = Field(default=0.6, ge=0.3, le=1.0)
    chip_length_mm: float = Field(default=2.0, ge=1.0, le=4.0)
    style: Optional[str] = Field(default=None)
    notes: Optional[str] = Field(default=None)
    
    @field_validator('rows')
    @classmethod
    def validate_row_materials(cls, rows):
        valid_materials = {'black', 'white', 'brown', 'natural'}
        for row in rows:
            for key in row.keys():
                if key not in valid_materials:
                    raise ValueError(f"Invalid material '{key}'. Use: {valid_materials}")
            total = sum(row.values())
            if total < 1 or total > 20:
                raise ValueError(f"Row total must be 1-20, got {total}")
        return rows
    
    @model_validator(mode='after')
    def validate_column_refs(self):
        if not self.rows:
            return self
        max_row = len(self.rows)
        for ref in self.column_sequence:
            if ref < 1 or ref > max_row:
                raise ValueError(
                    f"Column sequence references row {ref}, "
                    f"but only rows 1-{max_row} exist"
                )
        return self
    
    def to_pattern_generator_format(self) -> Dict[str, Any]:
        """Convert to format expected by RosettePatternEngine."""
        return {
            "name": self.name,
            "rows": self.rows,
            "column_sequence": self.column_sequence,
            "strip_width_mm": self.strip_width_mm,
            "strip_thickness_mm": self.strip_thickness_mm,
            "chip_length_mm": self.chip_length_mm,
            "notes": self.notes or f"AI-generated: {self.style or 'custom'} style"
        }


# ============================================================================
# PROMPT TEMPLATES - What We Send to the AI
# ============================================================================

SYSTEM_PROMPT = """You are a master luthier specializing in Spanish guitar rosette design.
You create matrix formulas for traditional rope/mosaic patterns.

RULES:
1. Output ONLY valid JSON matching the schema - no markdown, no explanation
2. Rows define material counts: {"black": N, "white": M} or add "brown" for 3-color
3. column_sequence is 1-indexed references to rows (assembly order)
4. Keep patterns manufacturable: 2-12 rows, 3-20 columns
5. Classic patterns are symmetric in column_sequence
6. Torres style: clean, elegant, often diamond/wave shapes
7. Hauser style: precise, often herringbone influence
8. Modern style: can be asymmetric, bold contrasts

JSON SCHEMA:
{
  "name": "Pattern Name",
  "rows": [
    {"black": 5, "white": 2},
    {"black": 4, "white": 3}
  ],
  "column_sequence": [1, 2, 1, 2, 1],
  "strip_width_mm": 0.8,
  "chip_length_mm": 1.8,
  "style": "torres|hauser|romanillos|fleta|modern|custom",
  "notes": "Brief description"
}"""

STYLE_HINTS = {
    "torres": "Antonio de Torres style: elegant Spanish classical, often symmetric diamond or wave patterns, refined proportions",
    "hauser": "Hermann Hauser style: German precision, clean lines, often herringbone influence, made guitars for Segovia",
    "romanillos": "José Romanillos style: Spanish-British fusion, balanced traditional patterns with modern sensibility",
    "fleta": "Ignacio Fleta style: Barcelona master, rich contrast patterns, concert guitar aesthetic",
    "simplicio": "Francisco Simplicio style: bold Barcelona patterns, strong visual impact",
    "modern": "Contemporary style: can break symmetry, bold contrasts, artistic expression",
    "celtic": "Celtic knot influence: interlocking patterns, continuous flow",
    "moorish": "Moorish/Islamic influence: geometric, star patterns, intricate detail",
}

COMPLEXITY_HINTS = {
    "simple": "2-3 rows, 5-7 columns, basic alternating pattern, good for beginners",
    "intermediate": "4-5 rows, 7-9 columns, classic rope or wave pattern",
    "advanced": "6-8 rows, 9-13 columns, complex mosaic or diamond pattern",
    "master": "8-12 rows, 11-15 columns, intricate multi-color pattern, museum quality",
}


def build_generation_prompt(
    user_request: str,
    style: Optional[str] = None,
    complexity: Optional[str] = None,
    colors: int = 2,
    rows_hint: Optional[int] = None,
    columns_hint: Optional[int] = None,
) -> str:
    """Build the prompt to send to the AI."""
    
    parts = [f"Create a rosette matrix formula for: {user_request}"]
    
    if style and style in STYLE_HINTS:
        parts.append(f"\nStyle guidance: {STYLE_HINTS[style]}")
    
    if complexity and complexity in COMPLEXITY_HINTS:
        parts.append(f"\nComplexity: {COMPLEXITY_HINTS[complexity]}")
    
    if rows_hint:
        parts.append(f"\nTarget approximately {rows_hint} rows")
    
    if columns_hint:
        parts.append(f"\nTarget approximately {columns_hint} columns")
    
    if colors == 3:
        parts.append("\nUse three colors: black, white, and brown")
    else:
        parts.append("\nUse two colors: black and white")
    
    parts.append("\n\nRespond with ONLY the JSON, no other text.")
    
    return "\n".join(parts)


# ============================================================================
# AI CLIENT ABSTRACTION
# ============================================================================

class AIProvider(str, Enum):
    STUB = "stub"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class AIGenerationResult:
    """Result from AI generation attempt."""
    success: bool
    formula: Optional[AIMatrixFormula] = None
    raw_response: Optional[str] = None
    error: Optional[str] = None
    provider: str = "stub"
    prompt_used: str = ""


class RosetteAIGenerator:
    """
    AI-powered rosette pattern generator.
    Generates MatrixFormula JSON from natural language.
    """
    
    def __init__(self, provider: AIProvider = AIProvider.STUB):
        self.provider = provider
        self._openai_client = None
        self._anthropic_client = None
    
    def generate(
        self,
        request: str,
        style: Optional[str] = None,
        complexity: Optional[str] = None,
        colors: int = 2,
    ) -> AIGenerationResult:
        """
        Generate a rosette pattern from natural language.
        
        Args:
            request: Natural language description
            style: Optional style hint (torres, hauser, modern, etc.)
            complexity: Optional complexity (simple, intermediate, advanced, master)
            colors: Number of colors (2 or 3)
        
        Returns:
            AIGenerationResult with validated formula or error
        """
        prompt = build_generation_prompt(
            user_request=request,
            style=style,
            complexity=complexity,
            colors=colors,
        )
        
        if self.provider == AIProvider.STUB:
            return self._generate_stub(prompt, style, complexity)
        elif self.provider == AIProvider.OPENAI:
            return self._generate_openai(prompt)
        elif self.provider == AIProvider.ANTHROPIC:
            return self._generate_anthropic(prompt)
        else:
            return AIGenerationResult(
                success=False,
                error=f"Unknown provider: {self.provider}",
                prompt_used=prompt,
            )
    
    def _generate_stub(
        self, 
        prompt: str, 
        style: Optional[str],
        complexity: Optional[str],
    ) -> AIGenerationResult:
        """
        Stub generator - returns deterministic patterns based on hints.
        Used for testing without API calls.
        """
        # Select pattern based on style/complexity
        if style == "torres":
            formula_dict = {
                "name": "AI Torres-Style Diamond",
                "rows": [
                    {"black": 1, "white": 5},
                    {"black": 2, "white": 4},
                    {"black": 3, "white": 3},
                    {"black": 4, "white": 2},
                    {"black": 3, "white": 3},
                    {"black": 2, "white": 4},
                    {"black": 1, "white": 5},
                ],
                "column_sequence": [1, 2, 3, 4, 5, 6, 7, 6, 5],
                "strip_width_mm": 0.7,
                "chip_length_mm": 1.6,
                "style": "torres",
                "notes": "AI-generated Torres-style diamond pattern"
            }
        elif style == "hauser":
            formula_dict = {
                "name": "AI Hauser-Style Herringbone",
                "rows": [
                    {"black": 6, "white": 2},
                    {"black": 5, "white": 3},
                    {"black": 4, "white": 4},
                    {"black": 3, "white": 5},
                    {"black": 4, "white": 4},
                    {"black": 5, "white": 3},
                ],
                "column_sequence": [1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1],
                "strip_width_mm": 0.65,
                "chip_length_mm": 1.7,
                "style": "hauser",
                "notes": "AI-generated Hauser-style pattern"
            }
        elif style == "modern":
            formula_dict = {
                "name": "AI Modern Asymmetric",
                "rows": [
                    {"black": 5, "white": 1},
                    {"black": 3, "white": 3},
                    {"black": 1, "white": 5},
                    {"black": 2, "white": 4},
                ],
                "column_sequence": [1, 2, 3, 4, 3, 2, 1, 4],
                "strip_width_mm": 1.0,
                "chip_length_mm": 2.0,
                "style": "modern",
                "notes": "AI-generated modern asymmetric pattern"
            }
        elif complexity == "simple":
            formula_dict = {
                "name": "AI Simple Rope",
                "rows": [
                    {"black": 3, "white": 2},
                    {"black": 2, "white": 3},
                    {"black": 3, "white": 2},
                ],
                "column_sequence": [1, 2, 3, 2, 1],
                "strip_width_mm": 1.0,
                "chip_length_mm": 2.0,
                "style": "simple",
                "notes": "AI-generated simple beginner pattern"
            }
        elif complexity == "master":
            formula_dict = {
                "name": "AI Master Mosaic",
                "rows": [
                    {"black": 2, "white": 6, "brown": 2},
                    {"black": 3, "white": 4, "brown": 3},
                    {"black": 4, "white": 2, "brown": 4},
                    {"black": 5, "white": 2, "brown": 3},
                    {"black": 4, "white": 2, "brown": 4},
                    {"black": 3, "white": 4, "brown": 3},
                    {"black": 2, "white": 6, "brown": 2},
                    {"black": 3, "white": 4, "brown": 3},
                ],
                "column_sequence": [1, 2, 3, 4, 5, 6, 7, 8, 7, 6, 5, 4, 3],
                "strip_width_mm": 0.6,
                "chip_length_mm": 1.5,
                "style": "master",
                "notes": "AI-generated master-level 3-color mosaic"
            }
        else:
            # Default intermediate pattern
            formula_dict = {
                "name": "AI Classic Rope",
                "rows": [
                    {"black": 5, "white": 2},
                    {"black": 4, "white": 3},
                    {"black": 3, "white": 4},
                    {"black": 4, "white": 3},
                    {"black": 5, "white": 2},
                ],
                "column_sequence": [1, 2, 3, 4, 5, 4, 3, 2, 1],
                "strip_width_mm": 0.8,
                "chip_length_mm": 1.8,
                "style": "classic",
                "notes": "AI-generated classic rope pattern"
            }
        
        try:
            formula = AIMatrixFormula(**formula_dict)
            return AIGenerationResult(
                success=True,
                formula=formula,
                raw_response=json.dumps(formula_dict, indent=2),
                provider="stub",
                prompt_used=prompt,
            )
        except Exception as e:
            return AIGenerationResult(
                success=False,
                error=str(e),
                raw_response=json.dumps(formula_dict, indent=2),
                provider="stub",
                prompt_used=prompt,
            )
    
    def _generate_openai(self, prompt: str) -> AIGenerationResult:
        """Generate using OpenAI API via AI Platform layer."""
        try:
            # Use canonical AI Platform transport (no direct openai import)
            from app.ai.transport import get_llm_client
            from app.ai.safety import assert_allowed, SafetyCategory
            from app.ai.observability import audit_ai_call

            # Safety check
            try:
                assert_allowed(prompt, category=SafetyCategory.ROSETTE_DESIGN)
            except Exception as e:
                return AIGenerationResult(
                    success=False,
                    error=f"Safety check failed: {e}",
                    prompt_used=prompt,
                )

            client = get_llm_client(provider="openai")

            if not client.is_configured:
                return AIGenerationResult(
                    success=False,
                    error="OPENAI_API_KEY not set",
                    prompt_used=prompt,
                )

            response = client.request_text(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.7,
                max_tokens=1000,
            )

            raw = response.content.strip()

            # Audit the call
            audit_ai_call(
                operation="llm",
                provider="openai",
                model=response.model,
                prompt=prompt,
                response_content=raw,
            )

            return self._parse_response(raw, prompt, "openai")

        except ImportError as e:
            return AIGenerationResult(
                success=False,
                error=f"AI Platform not available: {e}",
                prompt_used=prompt,
            )
        except Exception as e:
            return AIGenerationResult(
                success=False,
                error=str(e),
                prompt_used=prompt,
            )
    
    def _generate_anthropic(self, prompt: str) -> AIGenerationResult:
        """Generate using Anthropic API via AI Platform layer."""
        try:
            # Use canonical AI Platform transport (no direct anthropic import)
            from app.ai.transport import get_llm_client
            from app.ai.safety import assert_allowed, SafetyCategory
            from app.ai.observability import audit_ai_call

            # Safety check
            try:
                assert_allowed(prompt, category=SafetyCategory.ROSETTE_DESIGN)
            except Exception as e:
                return AIGenerationResult(
                    success=False,
                    error=f"Safety check failed: {e}",
                    prompt_used=prompt,
                )

            client = get_llm_client(provider="anthropic")

            if not client.is_configured:
                return AIGenerationResult(
                    success=False,
                    error="ANTHROPIC_API_KEY not set",
                    prompt_used=prompt,
                )

            response = client.request_text(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.7,
                max_tokens=1000,
            )

            raw = response.content.strip()

            # Audit the call
            audit_ai_call(
                operation="llm",
                provider="anthropic",
                model=response.model,
                prompt=prompt,
                response_content=raw,
            )

            return self._parse_response(raw, prompt, "anthropic")

        except ImportError as e:
            return AIGenerationResult(
                success=False,
                error=f"AI Platform not available: {e}",
                prompt_used=prompt,
            )
        except Exception as e:
            return AIGenerationResult(
                success=False,
                error=str(e),
                prompt_used=prompt,
            )
    
    def _parse_response(
        self, 
        raw: str, 
        prompt: str, 
        provider: str
    ) -> AIGenerationResult:
        """Parse and validate AI response."""
        try:
            # Strip markdown code blocks if present
            if raw.startswith("```"):
                raw = re.sub(r"```json?\n?", "", raw)
                raw = re.sub(r"```\n?$", "", raw)
            
            data = json.loads(raw)
            formula = AIMatrixFormula(**data)
            
            return AIGenerationResult(
                success=True,
                formula=formula,
                raw_response=raw,
                provider=provider,
                prompt_used=prompt,
            )
        except json.JSONDecodeError as e:
            return AIGenerationResult(
                success=False,
                error=f"Invalid JSON: {e}",
                raw_response=raw,
                provider=provider,
                prompt_used=prompt,
            )
        except Exception as e:
            return AIGenerationResult(
                success=False,
                error=f"Validation failed: {e}",
                raw_response=raw,
                provider=provider,
                prompt_used=prompt,
            )


# ============================================================================
# FASTAPI ENDPOINTS
# ============================================================================

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

router = APIRouter(
    prefix="/ai/rosette",
    tags=["AI Rosette Generator"],
)


class GenerateRequest(BaseModel):
    """Request to generate a rosette pattern."""
    prompt: str = Field(..., min_length=5, max_length=500, 
                        description="Natural language description of desired pattern")
    style: Optional[str] = Field(None, description="Style hint: torres, hauser, modern, etc.")
    complexity: Optional[str] = Field(None, description="Complexity: simple, intermediate, advanced, master")
    colors: int = Field(default=2, ge=2, le=3, description="Number of colors (2 or 3)")


class GenerateResponse(BaseModel):
    """Response from pattern generation."""
    success: bool
    formula: Optional[Dict[str, Any]] = None
    preview_available: bool = False
    error: Optional[str] = None
    provider: str = "stub"


@router.post("/generate", response_model=GenerateResponse)
def generate_rosette_pattern(req: GenerateRequest) -> GenerateResponse:
    """
    Generate a rosette matrix formula from natural language.
    
    Examples:
    - "Torres-style diamond pattern with high contrast"
    - "Simple beginner rope pattern, 5 rows"
    - "Modern asymmetric design with bold stripes"
    - "Master-level 3-color Spanish mosaic"
    """
    generator = RosetteAIGenerator(provider=AIProvider.STUB)
    
    result = generator.generate(
        request=req.prompt,
        style=req.style,
        complexity=req.complexity,
        colors=req.colors,
    )
    
    if result.success and result.formula:
        return GenerateResponse(
            success=True,
            formula=result.formula.to_pattern_generator_format(),
            preview_available=True,
            provider=result.provider,
        )
    else:
        return GenerateResponse(
            success=False,
            error=result.error,
            provider=result.provider,
        )


@router.get("/styles")
def list_styles() -> Dict[str, str]:
    """List available style hints for generation."""
    return STYLE_HINTS


@router.get("/complexity")
def list_complexity_levels() -> Dict[str, str]:
    """List available complexity levels."""
    return COMPLEXITY_HINTS


# ============================================================================
# DEMO / TEST
# ============================================================================

def demo():
    """Demonstrate the AI rosette generator."""
    print("=" * 60)
    print("AI ROSETTE PATTERN GENERATOR - Demo")
    print("=" * 60)
    
    generator = RosetteAIGenerator(provider=AIProvider.STUB)
    
    test_cases = [
        ("Torres-style diamond", {"style": "torres"}),
        ("Hauser herringbone", {"style": "hauser"}),
        ("Modern bold design", {"style": "modern"}),
        ("Simple beginner pattern", {"complexity": "simple"}),
        ("Master 3-color mosaic", {"complexity": "master", "colors": 3}),
        ("Classic rope pattern", {}),
    ]
    
    for prompt, kwargs in test_cases:
        print(f"\n--- Request: {prompt} ---")
        result = generator.generate(prompt, **kwargs)
        
        if result.success:
            f = result.formula
            print(f"✅ Generated: {f.name}")
            print(f"   Rows: {len(f.rows)}, Columns: {len(f.column_sequence)}")
            print(f"   Materials: {set(k for row in f.rows for k in row.keys())}")
            print(f"   Style: {f.style}")
        else:
            print(f"❌ Failed: {result.error}")
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    return generator


if __name__ == "__main__":
    demo()
