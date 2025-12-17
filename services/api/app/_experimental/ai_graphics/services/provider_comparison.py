#!/usr/bin/env python3
"""
Guitar Vision Engine — Provider Comparison Tool

Generate the same prompt across multiple providers for side-by-side comparison.
Tracks which provider wins for different guitar categories to improve routing.

Features:
- Same prompt → multiple providers
- Side-by-side HTML report
- Win/loss tracking per category
- Cost comparison
- Quality scoring interface

Usage:
    # Compare all available providers
    python3 provider_comparison.py --prompt "emerald les paul gold hardware"
    
    # Compare specific providers
    python3 provider_comparison.py --prompt "sunburst acoustic" --providers dalle3,guitar_lora
    
    # Batch comparison from file
    python3 provider_comparison.py --batch prompts.txt --output ./comparisons

Author: Luthier's ToolBox
Date: December 16, 2025
"""

from __future__ import annotations

import os
import sys
import json
import time
import base64
import argparse
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

# Local imports
sys.path.insert(0, str(Path(__file__).parent))

from guitar_prompt_engine import (
    engineer_guitar_prompt,
    parse_guitar_request,
    GuitarPrompt,
    ParsedGuitarRequest,
    GuitarCategory,
)
from guitar_image_providers import (
    GuitarVisionEngine,
    ImageProvider,
    ImageSize,
    ImageQuality,
    ImageGenerationResult,
    GeneratedImage,
    PROVIDER_COSTS,
)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ProviderResult:
    """Result from a single provider."""
    provider: str
    success: bool
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    image_path: Optional[str] = None
    generation_time_ms: float = 0.0
    cost_usd: float = 0.0
    error: Optional[str] = None
    
    # Evaluation (filled later)
    user_rating: Optional[int] = None  # 1-5
    is_winner: bool = False


@dataclass
class ComparisonRun:
    """A single comparison run across providers."""
    run_id: str
    timestamp: str
    
    # Input
    user_prompt: str
    engineered_prompt: str
    negative_prompt: str
    
    # Parsed attributes
    category: str
    body_shape: Optional[str]
    finish: Optional[str]
    parse_confidence: float
    
    # Results per provider
    results: Dict[str, ProviderResult] = field(default_factory=dict)
    
    # Evaluation
    winner: Optional[str] = None
    notes: str = ""
    
    # Totals
    total_cost: float = 0.0
    total_time_ms: float = 0.0


@dataclass
class ComparisonSession:
    """A session of multiple comparison runs."""
    session_id: str
    created_at: str
    
    runs: List[ComparisonRun] = field(default_factory=list)
    
    # Aggregate stats
    provider_wins: Dict[str, int] = field(default_factory=dict)
    category_wins: Dict[str, Dict[str, int]] = field(default_factory=dict)
    total_cost: float = 0.0
    
    def add_run(self, run: ComparisonRun):
        self.runs.append(run)
        self.total_cost += run.total_cost
        
        if run.winner:
            self.provider_wins[run.winner] = self.provider_wins.get(run.winner, 0) + 1
            
            if run.category not in self.category_wins:
                self.category_wins[run.category] = {}
            cat_wins = self.category_wins[run.category]
            cat_wins[run.winner] = cat_wins.get(run.winner, 0) + 1


# =============================================================================
# COMPARISON ENGINE
# =============================================================================

class ProviderComparison:
    """
    Run side-by-side comparisons across providers.
    """
    
    def __init__(
        self,
        output_dir: Path = Path("./comparisons"),
        providers: Optional[List[str]] = None,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.engine = GuitarVisionEngine()
        self.available_providers = self.engine.router.get_available_providers()
        
        # Filter to requested providers
        if providers:
            self.target_providers = [
                p for p in self.available_providers
                if p.value in providers
            ]
        else:
            self.target_providers = self.available_providers
        
        # Session tracking
        self.session = ComparisonSession(
            session_id=f"cmp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            created_at=datetime.utcnow().isoformat(),
        )
    
    def compare_prompt(
        self,
        user_prompt: str,
        size: ImageSize = ImageSize.SQUARE_LG,
        quality: ImageQuality = ImageQuality.STANDARD,
        save_images: bool = True,
    ) -> ComparisonRun:
        """
        Run the same prompt through all target providers.
        
        Args:
            user_prompt: Natural language guitar description
            size: Image size
            quality: Quality level
            save_images: Save images to disk
        
        Returns:
            ComparisonRun with results from all providers
        """
        # Engineer prompt
        guitar_prompt = engineer_guitar_prompt(user_prompt)
        parsed = guitar_prompt.parsed_request
        
        run_id = f"run_{int(time.time())}_{hash(user_prompt) % 10000:04d}"
        
        run = ComparisonRun(
            run_id=run_id,
            timestamp=datetime.utcnow().isoformat(),
            user_prompt=user_prompt,
            engineered_prompt=guitar_prompt.positive_prompt,
            negative_prompt=guitar_prompt.negative_prompt,
            category=parsed.category.value,
            body_shape=parsed.body_shape,
            finish=parsed.finish,
            parse_confidence=parsed.confidence,
        )
        
        print(f"\n{'='*60}")
        print(f"COMPARISON: {user_prompt}")
        print(f"{'='*60}")
        print(f"Category: {parsed.category.value}")
        print(f"Body: {parsed.body_shape}")
        print(f"Finish: {parsed.finish}")
        print(f"Providers: {[p.value for p in self.target_providers]}")
        
        # Run each provider
        for provider in self.target_providers:
            print(f"\n--- {provider.value.upper()} ---")
            
            start = time.time()
            
            try:
                result = self.engine.generate(
                    user_prompt=user_prompt,
                    num_images=1,
                    size=size,
                    quality=quality,
                    force_provider=provider,
                )
                
                elapsed = (time.time() - start) * 1000
                
                if result.success and result.images:
                    img = result.images[0]
                    
                    # Save image if requested
                    img_path = None
                    if save_images and (img.url or img.base64_data):
                        img_path = self._save_image(run_id, provider.value, img)
                    
                    provider_result = ProviderResult(
                        provider=provider.value,
                        success=True,
                        image_url=img.url,
                        image_base64=img.base64_data,
                        image_path=img_path,
                        generation_time_ms=elapsed,
                        cost_usd=result.actual_cost,
                    )
                    
                    print(f"✅ Success: {elapsed:.0f}ms, ${result.actual_cost:.4f}")
                    if img_path:
                        print(f"   Saved: {img_path}")
                else:
                    provider_result = ProviderResult(
                        provider=provider.value,
                        success=False,
                        generation_time_ms=elapsed,
                        error=result.error or "No images returned",
                    )
                    print(f"❌ Failed: {result.error}")
                    
            except Exception as e:
                elapsed = (time.time() - start) * 1000
                provider_result = ProviderResult(
                    provider=provider.value,
                    success=False,
                    generation_time_ms=elapsed,
                    error=str(e),
                )
                print(f"❌ Error: {e}")
            
            run.results[provider.value] = provider_result
            run.total_cost += provider_result.cost_usd
            run.total_time_ms += provider_result.generation_time_ms
        
        # Summary
        successful = [p for p, r in run.results.items() if r.success]
        print(f"\n📊 Summary:")
        print(f"   Successful: {len(successful)}/{len(self.target_providers)}")
        print(f"   Total cost: ${run.total_cost:.4f}")
        print(f"   Total time: {run.total_time_ms:.0f}ms")
        
        return run
    
    def _save_image(
        self,
        run_id: str,
        provider: str,
        image: GeneratedImage,
    ) -> Optional[str]:
        """Save image to disk."""
        try:
            images_dir = self.output_dir / "images"
            images_dir.mkdir(exist_ok=True)
            
            filename = f"{run_id}_{provider}.png"
            filepath = images_dir / filename
            
            if image.base64_data:
                img_bytes = base64.b64decode(image.base64_data)
                filepath.write_bytes(img_bytes)
                return str(filepath)
            
            if image.url:
                import requests
                response = requests.get(image.url, timeout=30)
                if response.status_code == 200:
                    filepath.write_bytes(response.content)
                    return str(filepath)
            
            return None
            
        except Exception as e:
            print(f"   ⚠️ Could not save image: {e}")
            return None
    
    def run_batch(
        self,
        prompts: List[str],
        size: ImageSize = ImageSize.SQUARE_LG,
        quality: ImageQuality = ImageQuality.STANDARD,
    ) -> ComparisonSession:
        """
        Run comparisons for multiple prompts.
        """
        print(f"\n{'#'*60}")
        print(f"BATCH COMPARISON: {len(prompts)} prompts")
        print(f"{'#'*60}")
        
        for i, prompt in enumerate(prompts):
            print(f"\n[{i+1}/{len(prompts)}]")
            run = self.compare_prompt(prompt, size=size, quality=quality)
            self.session.add_run(run)
        
        # Save session
        self._save_session()
        
        return self.session
    
    def _save_session(self):
        """Save session data to JSON."""
        session_file = self.output_dir / f"{self.session.session_id}.json"
        
        # Convert to serializable format
        data = {
            "session_id": self.session.session_id,
            "created_at": self.session.created_at,
            "total_runs": len(self.session.runs),
            "total_cost": self.session.total_cost,
            "provider_wins": self.session.provider_wins,
            "category_wins": self.session.category_wins,
            "runs": [asdict(run) for run in self.session.runs],
        }
        
        with open(session_file, "w") as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"\n📁 Session saved: {session_file}")
    
    def generate_html_report(self) -> str:
        """Generate HTML report for visual comparison."""
        
        html_parts = [
            "<!DOCTYPE html>",
            "<html><head>",
            "<meta charset='utf-8'>",
            "<title>Guitar Vision Provider Comparison</title>",
            "<style>",
            "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; background: #1a1a1a; color: #e0e0e0; }",
            "h1, h2, h3 { color: #fff; }",
            ".run { background: #2a2a2a; border-radius: 8px; padding: 20px; margin: 20px 0; }",
            ".run-header { border-bottom: 1px solid #444; padding-bottom: 10px; margin-bottom: 15px; }",
            ".prompt { font-size: 1.2em; color: #4fc3f7; }",
            ".meta { color: #888; font-size: 0.9em; }",
            ".providers { display: flex; flex-wrap: wrap; gap: 20px; }",
            ".provider { flex: 1; min-width: 300px; background: #333; border-radius: 8px; padding: 15px; }",
            ".provider-name { font-weight: bold; font-size: 1.1em; margin-bottom: 10px; }",
            ".provider img { width: 100%; border-radius: 4px; }",
            ".provider.winner { border: 2px solid #4caf50; }",
            ".provider.failed { opacity: 0.6; }",
            ".stats { display: flex; gap: 20px; margin-top: 10px; font-size: 0.9em; color: #aaa; }",
            ".summary { background: #2a2a2a; border-radius: 8px; padding: 20px; margin: 20px 0; }",
            ".summary table { width: 100%; border-collapse: collapse; }",
            ".summary th, .summary td { padding: 10px; text-align: left; border-bottom: 1px solid #444; }",
            ".rating-buttons { margin-top: 10px; }",
            ".rating-buttons button { padding: 5px 15px; margin-right: 5px; cursor: pointer; }",
            ".winner-badge { background: #4caf50; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; }",
            "</style>",
            "</head><body>",
            f"<h1>🎸 Guitar Vision Provider Comparison</h1>",
            f"<p>Session: {self.session.session_id}</p>",
            f"<p>Total runs: {len(self.session.runs)} | Total cost: ${self.session.total_cost:.2f}</p>",
        ]
        
        # Summary table
        if self.session.provider_wins:
            html_parts.append("<div class='summary'>")
            html_parts.append("<h2>Provider Win Summary</h2>")
            html_parts.append("<table>")
            html_parts.append("<tr><th>Provider</th><th>Wins</th><th>Win Rate</th></tr>")
            
            total_decided = sum(self.session.provider_wins.values())
            for provider, wins in sorted(self.session.provider_wins.items(), key=lambda x: -x[1]):
                rate = wins / total_decided * 100 if total_decided > 0 else 0
                html_parts.append(f"<tr><td>{provider}</td><td>{wins}</td><td>{rate:.0f}%</td></tr>")
            
            html_parts.append("</table>")
            html_parts.append("</div>")
        
        # Individual runs
        for run in self.session.runs:
            html_parts.append(f"<div class='run' id='{run.run_id}'>")
            html_parts.append("<div class='run-header'>")
            html_parts.append(f"<div class='prompt'>\"{run.user_prompt}\"</div>")
            html_parts.append(f"<div class='meta'>")
            html_parts.append(f"Category: {run.category} | Body: {run.body_shape or 'N/A'} | Finish: {run.finish or 'N/A'}")
            html_parts.append(f"</div>")
            html_parts.append("</div>")
            
            html_parts.append("<div class='providers'>")
            
            for provider_name, result in run.results.items():
                winner_class = " winner" if result.is_winner else ""
                failed_class = " failed" if not result.success else ""
                
                html_parts.append(f"<div class='provider{winner_class}{failed_class}'>")
                html_parts.append(f"<div class='provider-name'>{provider_name.upper()}")
                if result.is_winner:
                    html_parts.append(" <span class='winner-badge'>WINNER</span>")
                html_parts.append("</div>")
                
                if result.success:
                    if result.image_path:
                        # Local file
                        rel_path = Path(result.image_path).name
                        html_parts.append(f"<img src='images/{rel_path}' alt='{provider_name}'>")
                    elif result.image_url:
                        html_parts.append(f"<img src='{result.image_url}' alt='{provider_name}'>")
                    elif result.image_base64:
                        html_parts.append(f"<img src='data:image/png;base64,{result.image_base64[:100]}...' alt='{provider_name}'>")
                    
                    html_parts.append("<div class='stats'>")
                    html_parts.append(f"<span>⏱️ {result.generation_time_ms:.0f}ms</span>")
                    html_parts.append(f"<span>💰 ${result.cost_usd:.4f}</span>")
                    html_parts.append("</div>")
                else:
                    html_parts.append(f"<p>❌ Failed: {result.error}</p>")
                
                html_parts.append("</div>")
            
            html_parts.append("</div>")  # providers
            html_parts.append("</div>")  # run
        
        html_parts.extend([
            "</body></html>",
        ])
        
        # Save HTML
        html_file = self.output_dir / f"{self.session.session_id}.html"
        html_content = "\n".join(html_parts)
        html_file.write_text(html_content)
        
        print(f"📄 HTML report: {html_file}")
        
        return str(html_file)
    
    def record_winner(self, run_id: str, winner_provider: str):
        """Record which provider won a comparison."""
        for run in self.session.runs:
            if run.run_id == run_id:
                run.winner = winner_provider
                
                # Mark the winner
                for provider, result in run.results.items():
                    result.is_winner = (provider == winner_provider)
                
                # Update session stats
                self.session.provider_wins[winner_provider] = \
                    self.session.provider_wins.get(winner_provider, 0) + 1
                
                if run.category not in self.session.category_wins:
                    self.session.category_wins[run.category] = {}
                cat_wins = self.session.category_wins[run.category]
                cat_wins[winner_provider] = cat_wins.get(winner_provider, 0) + 1
                
                # Save updated session
                self._save_session()
                
                print(f"✅ Recorded: {winner_provider} wins for '{run.user_prompt}'")
                return True
        
        print(f"❌ Run not found: {run_id}")
        return False


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Compare guitar image generation across providers"
    )
    
    # Input modes
    parser.add_argument(
        "--prompt", "-p",
        help="Single prompt to compare",
    )
    parser.add_argument(
        "--batch", "-b",
        help="File with prompts (one per line)",
    )
    
    # Provider selection
    parser.add_argument(
        "--providers",
        help="Comma-separated list of providers to compare (default: all available)",
    )
    
    # Output
    parser.add_argument(
        "--output", "-o",
        default="./comparisons",
        help="Output directory",
    )
    
    # Generation options
    parser.add_argument(
        "--size",
        default="1024x1024",
        choices=["512x512", "768x768", "1024x1024"],
        help="Image size",
    )
    parser.add_argument(
        "--quality",
        default="standard",
        choices=["draft", "standard", "hd"],
        help="Quality level",
    )
    
    # Actions
    parser.add_argument(
        "--list-providers",
        action="store_true",
        help="List available providers and exit",
    )
    parser.add_argument(
        "--winner",
        nargs=2,
        metavar=("RUN_ID", "PROVIDER"),
        help="Record winner for a run",
    )
    parser.add_argument(
        "--session",
        help="Session ID to load for recording winners",
    )
    
    args = parser.parse_args()
    
    # Parse providers
    providers = None
    if args.providers:
        providers = [p.strip() for p in args.providers.split(",")]
    
    # Size mapping
    size_map = {
        "512x512": ImageSize.SQUARE_SM,
        "768x768": ImageSize.SQUARE_MD,
        "1024x1024": ImageSize.SQUARE_LG,
    }
    size = size_map.get(args.size, ImageSize.SQUARE_LG)
    
    # Quality mapping
    quality_map = {
        "draft": ImageQuality.DRAFT,
        "standard": ImageQuality.STANDARD,
        "hd": ImageQuality.HD,
    }
    quality = quality_map.get(args.quality, ImageQuality.STANDARD)
    
    # Create comparison engine
    comparison = ProviderComparison(
        output_dir=Path(args.output),
        providers=providers,
    )
    
    if args.list_providers:
        print("Available providers:")
        for p in comparison.available_providers:
            costs = PROVIDER_COSTS.get(p, {})
            cost_str = ", ".join(f"{q.value}=${c:.3f}" for q, c in costs.items())
            print(f"  • {p.value}: {cost_str or 'free'}")
        return
    
    if args.winner:
        run_id, provider = args.winner
        comparison.record_winner(run_id, provider)
        return
    
    if args.prompt:
        # Single prompt
        run = comparison.compare_prompt(args.prompt, size=size, quality=quality)
        comparison.session.add_run(run)
        comparison._save_session()
        comparison.generate_html_report()
        
    elif args.batch:
        # Batch from file
        batch_file = Path(args.batch)
        if not batch_file.exists():
            print(f"❌ Batch file not found: {batch_file}")
            sys.exit(1)
        
        prompts = [
            line.strip() 
            for line in batch_file.read_text().splitlines()
            if line.strip() and not line.startswith("#")
        ]
        
        if not prompts:
            print("❌ No prompts found in batch file")
            sys.exit(1)
        
        comparison.run_batch(prompts, size=size, quality=quality)
        comparison.generate_html_report()
        
    else:
        # Interactive demo
        print("=" * 60)
        print("🎸 GUITAR VISION PROVIDER COMPARISON")
        print("=" * 60)
        print(f"\nAvailable providers: {[p.value for p in comparison.target_providers]}")
        print("\nUsage:")
        print("  --prompt 'green les paul'     Compare single prompt")
        print("  --batch prompts.txt           Compare from file")
        print("  --list-providers              Show available providers")
        print("\nExample:")
        print("  python3 provider_comparison.py --prompt 'sunburst acoustic'")


# =============================================================================
# SAMPLE COMPARISON PROMPTS
# =============================================================================

SAMPLE_PROMPTS = """
# Electric guitars
emerald green les paul with gold hardware
black stratocaster maple fretboard
tobacco burst es-335 cream binding
white telecaster rosewood fretboard

# Acoustic guitars  
sunburst dreadnought acoustic herringbone
natural grand auditorium cedar top
vintage parlor mahogany

# Classical
spanish classical cedar top
flamenco guitar cypress

# Bass
sunburst precision bass
natural jazz bass maple fretboard
"""


if __name__ == "__main__":
    main()
