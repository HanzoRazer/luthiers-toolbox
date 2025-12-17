#!/usr/bin/env python3
"""
Guitar Vision Engine — Training Data Generator

Uses DALL-E to create a labeled dataset for fine-tuning a Guitar LoRA.

The teacher (DALL-E) creates curriculum for the student (LoRA):
1. Systematic coverage of all guitar types, finishes, hardware
2. Consistent labeling format for training
3. Cost tracking and budget management
4. Resume capability for long runs

Output Structure:
    dataset/
    ├── images/
    │   ├── 00001_electric_les_paul_sunburst.png
    │   ├── 00001_electric_les_paul_sunburst.txt  (caption)
    │   ├── 00002_acoustic_dreadnought_natural.png
    │   └── ...
    ├── metadata.jsonl
    └── generation_log.json

Author: Luthier's ToolBox
Date: December 16, 2025
"""

from __future__ import annotations

import os
import sys
import json
import time
import hashlib
import argparse
import random
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Iterator, Tuple
from itertools import product

# Local imports
try:
    from guitar_prompt_engine import (
        engineer_guitar_prompt,
        BODY_SHAPES,
        FINISHES,
        WOODS,
        HARDWARE,
        INLAYS,
        PHOTOGRAPHY_STYLES,
        GuitarCategory,
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from guitar_prompt_engine import (
        engineer_guitar_prompt,
        BODY_SHAPES,
        FINISHES,
        WOODS,
        HARDWARE,
        INLAYS,
        PHOTOGRAPHY_STYLES,
        GuitarCategory,
    )


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class DatasetConfig:
    """Configuration for dataset generation."""
    
    # Output
    output_dir: Path = Path("./guitar_dataset")
    
    # Generation settings
    images_per_combination: int = 1
    image_size: str = "1024x1024"
    image_quality: str = "standard"
    
    # Budget
    max_images: int = 100
    max_cost_usd: float = 10.0
    cost_per_image: float = 0.04  # Standard DALL-E 3
    
    # Coverage priorities (higher = more samples)
    category_weights: Dict[str, float] = field(default_factory=lambda: {
        "electric": 1.0,
        "acoustic": 1.0,
        "classical": 0.5,
        "bass": 0.3,
    })
    
    # Subset of vocabulary to use (None = use all)
    body_shapes: Optional[List[str]] = None
    finishes: Optional[List[str]] = None
    
    # Photo styles to include
    photo_styles: List[str] = field(default_factory=lambda: [
        "product", "dramatic", "studio"
    ])
    
    # Rate limiting
    requests_per_minute: int = 5
    retry_delay: float = 5.0
    max_retries: int = 3
    
    def __post_init__(self):
        self.output_dir = Path(self.output_dir)


# =============================================================================
# TRAINING SAMPLE SCHEMA
# =============================================================================

@dataclass
class TrainingSample:
    """A single training sample for LoRA fine-tuning."""
    
    # Identity
    sample_id: str
    index: int
    
    # Labels (these become the caption)
    category: str          # electric, acoustic, classical, bass
    body_shape: str        # les paul, dreadnought, etc.
    finish: str            # sunburst, black, etc.
    photo_style: str       # product, dramatic, etc.
    
    # Optional labels
    hardware: Optional[str] = None
    wood: Optional[str] = None
    inlay: Optional[str] = None
    
    # Prompts
    user_prompt: str = ""
    engineered_prompt: str = ""
    dalle_revised_prompt: str = ""
    
    # Generation metadata
    generated_at: Optional[str] = None
    generation_time_seconds: float = 0.0
    cost_usd: float = 0.04
    
    # File paths (relative to dataset root)
    image_path: Optional[str] = None
    caption_path: Optional[str] = None
    
    # Status
    success: bool = False
    error: Optional[str] = None
    
    def to_caption(self) -> str:
        """
        Generate caption for LoRA training.
        
        Format optimized for Stable Diffusion fine-tuning:
        - Trigger word first (guitar_photo)
        - Key attributes as tags
        - Natural description
        """
        parts = ["guitar_photo"]  # Trigger word for the LoRA
        
        # Category and shape
        parts.append(f"{self.category} guitar")
        if self.body_shape:
            parts.append(self.body_shape)
        
        # Finish
        if self.finish:
            parts.append(f"{self.finish} finish")
        
        # Optional attributes
        if self.hardware:
            parts.append(self.hardware)
        if self.wood:
            parts.append(self.wood)
        if self.inlay:
            parts.append(self.inlay)
        
        # Photo style
        parts.append(f"{self.photo_style} photography")
        
        # Quality tags
        parts.extend([
            "professional photo",
            "high detail",
            "studio lighting",
        ])
        
        return ", ".join(parts)
    
    def to_filename(self) -> str:
        """Generate filename from labels."""
        parts = [
            f"{self.index:05d}",
            self.category,
            self.body_shape.replace(" ", "_") if self.body_shape else "unknown",
            self.finish.replace(" ", "_") if self.finish else "natural",
        ]
        return "_".join(parts)


# =============================================================================
# COMBINATION GENERATOR
# =============================================================================

class CombinationGenerator:
    """
    Generates systematic combinations of guitar attributes for training.
    
    Strategy:
    1. Core combinations: body_shape × finish (most important)
    2. Style variations: each core × photo_styles
    3. Priority sampling: more samples for common categories
    """
    
    def __init__(self, config: DatasetConfig):
        self.config = config
        
        # Get vocabulary subsets
        self.body_shapes = self._get_body_shapes()
        self.finishes = self._get_finishes()
        self.photo_styles = config.photo_styles
        
        # Pre-compute all combinations
        self._combinations: List[Dict[str, Any]] = []
        self._generate_combinations()
    
    def _get_body_shapes(self) -> Dict[str, List[str]]:
        """Get body shapes organized by category."""
        if self.config.body_shapes:
            # Filter to specified shapes
            result = {"electric": [], "acoustic": [], "classical": [], "bass": []}
            for shape in self.config.body_shapes:
                if shape in BODY_SHAPES:
                    cat = BODY_SHAPES[shape].value
                    result[cat].append(shape)
            return result
        
        # Use all shapes, organized by category
        result = {"electric": [], "acoustic": [], "classical": [], "bass": []}
        for shape, category in BODY_SHAPES.items():
            result[category.value].append(shape)
        return result
    
    def _get_finishes(self) -> List[str]:
        """Get finish list."""
        if self.config.finishes:
            return self.config.finishes
        
        # Use a representative subset (not all 50+)
        core_finishes = [
            # Solid
            "black", "white", "natural",
            # Burst
            "sunburst", "tobacco burst", "cherry burst",
            # Transparent
            "emerald", "trans red", "amber",
            # Metallic
            "gold top", "silver",
            # Figured
            "flame", "quilted",
        ]
        return core_finishes
    
    def _generate_combinations(self):
        """Generate all combinations with priority weighting."""
        combinations = []
        
        for category, shapes in self.body_shapes.items():
            weight = self.config.category_weights.get(category, 0.5)
            
            for shape in shapes:
                for finish in self.finishes:
                    for style in self.photo_styles:
                        combinations.append({
                            "category": category,
                            "body_shape": shape,
                            "finish": finish,
                            "photo_style": style,
                            "weight": weight,
                        })
        
        # Sort by weight (higher priority first)
        combinations.sort(key=lambda x: x["weight"], reverse=True)
        
        self._combinations = combinations
    
    def __len__(self) -> int:
        return len(self._combinations)
    
    def __iter__(self) -> Iterator[Dict[str, Any]]:
        return iter(self._combinations)
    
    def get_sample_plan(self, max_samples: int) -> List[Dict[str, Any]]:
        """
        Get a sampling plan that fits within budget.
        
        Uses weighted sampling to prioritize important combinations.
        """
        if max_samples >= len(self._combinations):
            return self._combinations.copy()
        
        # Weighted random sampling
        weights = [c["weight"] for c in self._combinations]
        total_weight = sum(weights)
        probs = [w / total_weight for w in weights]
        
        # Sample without replacement
        indices = list(range(len(self._combinations)))
        selected_indices = []
        
        random.seed(42)  # Reproducible
        remaining = indices.copy()
        remaining_probs = probs.copy()
        
        for _ in range(max_samples):
            if not remaining:
                break
            
            # Normalize remaining probabilities
            total = sum(remaining_probs)
            norm_probs = [p / total for p in remaining_probs]
            
            # Sample
            idx = random.choices(range(len(remaining)), weights=norm_probs, k=1)[0]
            selected_indices.append(remaining[idx])
            
            # Remove selected
            remaining.pop(idx)
            remaining_probs.pop(idx)
        
        return [self._combinations[i] for i in sorted(selected_indices)]
    
    def get_coverage_report(self) -> Dict[str, Any]:
        """Report on vocabulary coverage."""
        return {
            "total_combinations": len(self._combinations),
            "categories": {
                cat: len(shapes) 
                for cat, shapes in self.body_shapes.items()
            },
            "finishes": len(self.finishes),
            "photo_styles": len(self.photo_styles),
            "estimated_cost": len(self._combinations) * self.config.cost_per_image,
        }


# =============================================================================
# DALLE GENERATOR
# =============================================================================

class DallETrainingGenerator:
    """
    Generates training images using DALL-E.
    
    Features:
    - Rate limiting
    - Resume capability
    - Cost tracking
    - Automatic caption generation
    """
    
    def __init__(self, config: DatasetConfig, api_key: Optional[str] = None):
        self.config = config
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        
        # State
        self.samples_generated: List[TrainingSample] = []
        self.total_cost: float = 0.0
        self.errors: List[Dict[str, Any]] = []
        
        # Setup directories
        self.images_dir = config.output_dir / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing state if resuming
        self._load_state()
    
    def _load_state(self):
        """Load state from previous run if exists."""
        log_path = self.config.output_dir / "generation_log.json"
        if log_path.exists():
            try:
                with open(log_path) as f:
                    state = json.load(f)
                self.samples_generated = [
                    TrainingSample(**s) for s in state.get("samples", [])
                ]
                self.total_cost = state.get("total_cost", 0.0)
                print(f"📂 Resuming from {len(self.samples_generated)} existing samples")
            except Exception as e:
                print(f"⚠️ Could not load state: {e}")
    
    def _save_state(self):
        """Save state for resume capability."""
        log_path = self.config.output_dir / "generation_log.json"
        state = {
            "config": asdict(self.config),
            "samples": [asdict(s) for s in self.samples_generated],
            "total_cost": self.total_cost,
            "errors": self.errors,
            "last_updated": datetime.utcnow().isoformat(),
        }
        # Convert Path to string for JSON serialization
        state["config"]["output_dir"] = str(self.config.output_dir)
        
        with open(log_path, "w") as f:
            json.dump(state, f, indent=2)
    
    def _save_metadata(self):
        """Save metadata.jsonl for training tools."""
        meta_path = self.config.output_dir / "metadata.jsonl"
        with open(meta_path, "w") as f:
            for sample in self.samples_generated:
                if sample.success:
                    record = {
                        "file_name": sample.image_path,
                        "caption": sample.to_caption(),
                        "category": sample.category,
                        "body_shape": sample.body_shape,
                        "finish": sample.finish,
                        "photo_style": sample.photo_style,
                    }
                    f.write(json.dumps(record) + "\n")
    
    def _get_existing_ids(self) -> set:
        """Get IDs of already generated samples."""
        return {s.sample_id for s in self.samples_generated if s.success}
    
    def _make_sample_id(self, combo: Dict[str, Any]) -> str:
        """Create unique ID for a combination."""
        key = f"{combo['category']}_{combo['body_shape']}_{combo['finish']}_{combo['photo_style']}"
        return hashlib.md5(key.encode()).hexdigest()[:12]
    
    def _generate_one(self, sample: TrainingSample) -> TrainingSample:
        """Generate a single training image."""
        import openai
        import requests
        
        client = openai.OpenAI(api_key=self.api_key)
        
        # Build prompt
        user_prompt = f"{sample.finish} {sample.body_shape} guitar"
        guitar_prompt = engineer_guitar_prompt(
            user_prompt,
            photo_style=sample.photo_style,
        )
        
        sample.user_prompt = user_prompt
        sample.engineered_prompt = guitar_prompt.positive_prompt
        
        start = time.time()
        
        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=guitar_prompt.positive_prompt,
                size=self.config.image_size,
                quality=self.config.image_quality,
                n=1,
            )
            
            sample.generation_time_seconds = time.time() - start
            sample.dalle_revised_prompt = response.data[0].revised_prompt or ""
            
            # Download image
            img_url = response.data[0].url
            img_response = requests.get(img_url)
            
            if img_response.status_code == 200:
                # Save image
                filename = sample.to_filename()
                img_path = self.images_dir / f"{filename}.png"
                img_path.write_bytes(img_response.content)
                sample.image_path = f"images/{filename}.png"
                
                # Save caption
                caption_path = self.images_dir / f"{filename}.txt"
                caption_path.write_text(sample.to_caption())
                sample.caption_path = f"images/{filename}.txt"
                
                sample.success = True
                sample.generated_at = datetime.utcnow().isoformat()
                sample.cost_usd = self.config.cost_per_image
                
            else:
                sample.error = f"Image download failed: {img_response.status_code}"
                
        except Exception as e:
            sample.error = str(e)
            sample.generation_time_seconds = time.time() - start
        
        return sample
    
    def generate_dataset(
        self,
        combinations: List[Dict[str, Any]],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate the full dataset.
        
        Args:
            combinations: List of attribute combinations to generate
            dry_run: If True, don't actually generate (just plan)
        
        Returns:
            Summary of generation run
        """
        existing_ids = self._get_existing_ids()
        
        # Filter out already-generated
        to_generate = []
        for i, combo in enumerate(combinations):
            sample_id = self._make_sample_id(combo)
            if sample_id not in existing_ids:
                to_generate.append((i, combo, sample_id))
        
        print(f"\n📋 Generation Plan:")
        print(f"   Total combinations: {len(combinations)}")
        print(f"   Already generated: {len(existing_ids)}")
        print(f"   To generate: {len(to_generate)}")
        print(f"   Estimated cost: ${len(to_generate) * self.config.cost_per_image:.2f}")
        
        if dry_run:
            print("\n🔍 DRY RUN - No images will be generated")
            return {
                "planned": len(to_generate),
                "estimated_cost": len(to_generate) * self.config.cost_per_image,
            }
        
        if not self.api_key:
            print("\n❌ No API key provided!")
            print("   Set OPENAI_API_KEY or pass --key")
            return {"error": "No API key"}
        
        # Check budget
        remaining_budget = self.config.max_cost_usd - self.total_cost
        affordable = int(remaining_budget / self.config.cost_per_image)
        
        if affordable <= 0:
            print(f"\n❌ Budget exhausted (${self.total_cost:.2f} / ${self.config.max_cost_usd:.2f})")
            return {"error": "Budget exhausted"}
        
        to_generate = to_generate[:min(len(to_generate), affordable, self.config.max_images)]
        
        print(f"\n🚀 Generating {len(to_generate)} images...")
        print(f"   Budget remaining: ${remaining_budget:.2f}")
        
        # Rate limiting
        min_interval = 60.0 / self.config.requests_per_minute
        last_request = 0.0
        
        for idx, (orig_idx, combo, sample_id) in enumerate(to_generate):
            # Rate limit
            elapsed = time.time() - last_request
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            
            sample = TrainingSample(
                sample_id=sample_id,
                index=len(self.samples_generated) + 1,
                category=combo["category"],
                body_shape=combo["body_shape"],
                finish=combo["finish"],
                photo_style=combo["photo_style"],
            )
            
            print(f"\n[{idx + 1}/{len(to_generate)}] {sample.body_shape} / {sample.finish} / {sample.photo_style}")
            
            # Generate with retries
            for attempt in range(self.config.max_retries):
                last_request = time.time()
                sample = self._generate_one(sample)
                
                if sample.success:
                    break
                
                if attempt < self.config.max_retries - 1:
                    print(f"   ⚠️ Retry {attempt + 1}: {sample.error}")
                    time.sleep(self.config.retry_delay)
            
            if sample.success:
                print(f"   ✅ Generated in {sample.generation_time_seconds:.1f}s")
                self.total_cost += sample.cost_usd
            else:
                print(f"   ❌ Failed: {sample.error}")
                self.errors.append({
                    "sample_id": sample_id,
                    "combo": combo,
                    "error": sample.error,
                })
            
            self.samples_generated.append(sample)
            
            # Save state periodically
            if (idx + 1) % 5 == 0:
                self._save_state()
                self._save_metadata()
        
        # Final save
        self._save_state()
        self._save_metadata()
        
        # Summary
        successful = sum(1 for s in self.samples_generated if s.success)
        
        print(f"\n{'='*60}")
        print(f"📊 GENERATION COMPLETE")
        print(f"{'='*60}")
        print(f"   Successful: {successful}")
        print(f"   Failed: {len(self.errors)}")
        print(f"   Total cost: ${self.total_cost:.2f}")
        print(f"   Output: {self.config.output_dir}")
        
        return {
            "successful": successful,
            "failed": len(self.errors),
            "total_cost": self.total_cost,
            "output_dir": str(self.config.output_dir),
        }


# =============================================================================
# STUB GENERATOR (For Testing)
# =============================================================================

class StubTrainingGenerator:
    """
    Stub generator for testing without API calls.
    Creates placeholder files with proper structure.
    """
    
    def __init__(self, config: DatasetConfig):
        self.config = config
        self.samples_generated: List[TrainingSample] = []
        
        self.images_dir = config.output_dir / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_dataset(
        self,
        combinations: List[Dict[str, Any]],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Generate stub dataset."""
        
        print(f"\n📋 STUB Generation Plan:")
        print(f"   Combinations: {len(combinations)}")
        
        if dry_run:
            return {"planned": len(combinations)}
        
        for i, combo in enumerate(combinations[:self.config.max_images]):
            sample_id = hashlib.md5(
                f"{combo['category']}_{combo['body_shape']}_{combo['finish']}".encode()
            ).hexdigest()[:12]
            
            sample = TrainingSample(
                sample_id=sample_id,
                index=i + 1,
                category=combo["category"],
                body_shape=combo["body_shape"],
                finish=combo["finish"],
                photo_style=combo["photo_style"],
                success=True,
                generated_at=datetime.utcnow().isoformat(),
                cost_usd=0.0,
            )
            
            # Create stub files
            filename = sample.to_filename()
            
            # Stub image (1x1 PNG)
            img_path = self.images_dir / f"{filename}.png"
            # Minimal valid PNG
            png_header = bytes([
                0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
                0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
                0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
                0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
                0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
                0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
                0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,
                0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
                0x44, 0xAE, 0x42, 0x60, 0x82
            ])
            img_path.write_bytes(png_header)
            sample.image_path = f"images/{filename}.png"
            
            # Caption
            caption_path = self.images_dir / f"{filename}.txt"
            caption_path.write_text(sample.to_caption())
            sample.caption_path = f"images/{filename}.txt"
            
            self.samples_generated.append(sample)
            
            if (i + 1) % 10 == 0:
                print(f"   Generated {i + 1}/{min(len(combinations), self.config.max_images)}")
        
        # Save metadata
        meta_path = self.config.output_dir / "metadata.jsonl"
        with open(meta_path, "w") as f:
            for sample in self.samples_generated:
                record = {
                    "file_name": sample.image_path,
                    "caption": sample.to_caption(),
                    "category": sample.category,
                    "body_shape": sample.body_shape,
                    "finish": sample.finish,
                }
                f.write(json.dumps(record) + "\n")
        
        print(f"\n✅ Generated {len(self.samples_generated)} stub samples")
        print(f"   Output: {self.config.output_dir}")
        
        return {
            "successful": len(self.samples_generated),
            "failed": 0,
            "total_cost": 0.0,
            "output_dir": str(self.config.output_dir),
        }


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate training data for Guitar LoRA using DALL-E"
    )
    
    # Output
    parser.add_argument(
        "--output", "-o",
        default="./guitar_dataset",
        help="Output directory for dataset",
    )
    
    # Generation
    parser.add_argument(
        "--max-images", "-n",
        type=int,
        default=50,
        help="Maximum images to generate",
    )
    parser.add_argument(
        "--budget",
        type=float,
        default=5.0,
        help="Maximum budget in USD",
    )
    parser.add_argument(
        "--quality",
        choices=["standard", "hd"],
        default="standard",
        help="DALL-E quality level",
    )
    
    # API
    parser.add_argument(
        "--key", "-k",
        help="OpenAI API key (or set OPENAI_API_KEY)",
    )
    
    # Modes
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan only, don't generate",
    )
    parser.add_argument(
        "--stub",
        action="store_true",
        help="Use stub generator (no API calls)",
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Show vocabulary coverage report",
    )
    
    args = parser.parse_args()
    
    # Build config
    config = DatasetConfig(
        output_dir=Path(args.output),
        max_images=args.max_images,
        max_cost_usd=args.budget,
        image_quality=args.quality,
        cost_per_image=0.04 if args.quality == "standard" else 0.08,
    )
    
    print("=" * 60)
    print("🎸 GUITAR LoRA TRAINING DATA GENERATOR")
    print("=" * 60)
    
    # Generate combinations
    combo_gen = CombinationGenerator(config)
    
    if args.coverage:
        report = combo_gen.get_coverage_report()
        print(f"\n📊 Coverage Report:")
        print(f"   Total combinations: {report['total_combinations']}")
        print(f"   Categories: {report['categories']}")
        print(f"   Finishes: {report['finishes']}")
        print(f"   Photo styles: {report['photo_styles']}")
        print(f"   Full dataset cost: ${report['estimated_cost']:.2f}")
        return
    
    # Get sample plan
    plan = combo_gen.get_sample_plan(args.max_images)
    
    print(f"\n📋 Configuration:")
    print(f"   Output: {config.output_dir}")
    print(f"   Max images: {config.max_images}")
    print(f"   Budget: ${config.max_cost_usd:.2f}")
    print(f"   Quality: {config.image_quality}")
    print(f"   Planned samples: {len(plan)}")
    
    # Generate
    if args.stub:
        generator = StubTrainingGenerator(config)
    else:
        if args.key:
            os.environ["OPENAI_API_KEY"] = args.key
        generator = DallETrainingGenerator(config)
    
    result = generator.generate_dataset(plan, dry_run=args.dry_run)
    
    print(f"\n{'='*60}")
    if result.get("error"):
        print(f"❌ {result['error']}")
    else:
        print(f"✅ Done!")


if __name__ == "__main__":
    main()
