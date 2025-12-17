#!/usr/bin/env python3
"""
Guitar LoRA — Kohya Training Config Generator

Generates configuration files for training a Guitar LoRA using Kohya_ss.

Output:
    dataset/
    ├── config/
    │   ├── training_config.toml
    │   ├── dataset_config.toml
    │   └── sample_prompts.txt
    └── ...

Usage:
    python3 kohya_config_generator.py --dataset ./guitar_dataset

Author: Luthier's ToolBox
Date: December 16, 2025
"""

from __future__ import annotations

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class KohyaConfig:
    """Configuration for Kohya LoRA training."""
    
    # Model
    base_model: str = "stabilityai/stable-diffusion-xl-base-1.0"
    model_type: str = "sdxl"  # or "sd15"
    
    # Training
    resolution: int = 1024
    train_batch_size: int = 1
    max_train_epochs: int = 10
    learning_rate: float = 1e-4
    lr_scheduler: str = "cosine"
    lr_warmup_steps: int = 100
    
    # LoRA
    network_dim: int = 32  # LoRA rank
    network_alpha: int = 16
    
    # Memory optimization
    mixed_precision: str = "bf16"
    gradient_checkpointing: bool = True
    gradient_accumulation_steps: int = 1
    
    # Output
    output_name: str = "guitar_lora"
    save_every_n_epochs: int = 2


def generate_training_config(config: KohyaConfig, dataset_path: Path) -> str:
    """Generate training_config.toml content."""
    
    return f'''# Guitar LoRA Training Configuration
# Generated for Kohya_ss / sd-scripts

[model]
pretrained_model_name_or_path = "{config.base_model}"
v2 = false
v_parameterization = false

[training]
output_dir = "./output"
output_name = "{config.output_name}"
save_model_as = "safetensors"
save_every_n_epochs = {config.save_every_n_epochs}
max_train_epochs = {config.max_train_epochs}
train_batch_size = {config.train_batch_size}
gradient_checkpointing = {str(config.gradient_checkpointing).lower()}
gradient_accumulation_steps = {config.gradient_accumulation_steps}
mixed_precision = "{config.mixed_precision}"
seed = 42

[optimizer]
optimizer_type = "AdamW8bit"
learning_rate = {config.learning_rate}
lr_scheduler = "{config.lr_scheduler}"
lr_warmup_steps = {config.lr_warmup_steps}

[network]
network_module = "networks.lora"
network_dim = {config.network_dim}
network_alpha = {config.network_alpha}

[dataset]
resolution = {config.resolution}
enable_bucket = true
min_bucket_reso = 512
max_bucket_reso = 2048
bucket_reso_steps = 64
bucket_no_upscale = false

[caption]
shuffle_caption = true
keep_tokens = 1
caption_extension = ".txt"

[advanced]
xformers = true
cache_latents = true
cache_latents_to_disk = false
'''


def generate_dataset_config(config: KohyaConfig, dataset_path: Path) -> str:
    """Generate dataset_config.toml content."""
    
    images_path = dataset_path / "images"
    
    return f'''# Guitar LoRA Dataset Configuration

[[datasets]]
resolution = {config.resolution}
batch_size = {config.train_batch_size}
enable_bucket = true

  [[datasets.subsets]]
  image_dir = "{images_path.absolute()}"
  caption_extension = ".txt"
  num_repeats = 10
  shuffle_caption = true
  keep_tokens = 1
  color_aug = false
  flip_aug = false
'''


def generate_sample_prompts(dataset_path: Path) -> str:
    """Generate sample prompts for testing the trained LoRA."""
    
    # Read some captions from the dataset
    meta_path = dataset_path / "metadata.jsonl"
    samples = []
    
    if meta_path.exists():
        with open(meta_path) as f:
            for line in f:
                if len(samples) >= 10:
                    break
                record = json.loads(line)
                samples.append(record.get("caption", ""))
    
    # Add some test variations
    test_prompts = [
        "guitar_photo, electric guitar, les paul, cherry sunburst finish, gold hardware, product photography, professional photo, high detail",
        "guitar_photo, acoustic guitar, dreadnought, natural wood finish, herringbone binding, studio photography, warm lighting",
        "guitar_photo, electric guitar, stratocaster, olympic white, maple fretboard, vintage style, dramatic lighting",
        "guitar_photo, electric guitar, sg, cherry red finish, chrome hardware, rock style, dramatic photography",
        "guitar_photo, acoustic guitar, grand auditorium, sunburst finish, abalone rosette, lifestyle photography",
    ]
    
    lines = [
        "# Sample Prompts for Testing Guitar LoRA",
        "# Use these to test your trained model",
        "#",
        "# Trigger word: guitar_photo",
        "#",
        "# === From Training Data ===",
        "",
    ]
    
    for sample in samples[:5]:
        lines.append(sample)
    
    lines.extend([
        "",
        "# === Test Variations ===",
        "",
    ])
    
    for prompt in test_prompts:
        lines.append(prompt)
    
    lines.extend([
        "",
        "# === Negative Prompt (recommended) ===",
        "blurry, low quality, distorted, wrong proportions, extra strings, missing strings, broken, cartoon, anime, watermark, text",
    ])
    
    return "\n".join(lines)


def generate_training_script(config: KohyaConfig, dataset_path: Path) -> str:
    """Generate shell script to run training."""
    
    return f'''#!/bin/bash
# Guitar LoRA Training Script
# Run this from your Kohya_ss installation directory

# Configuration paths
CONFIG_DIR="{dataset_path.absolute()}/config"
OUTPUT_DIR="./output"

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Run training
accelerate launch --num_cpu_threads_per_process 1 train_network.py \\
    --pretrained_model_name_or_path="{config.base_model}" \\
    --dataset_config="$CONFIG_DIR/dataset_config.toml" \\
    --output_dir="$OUTPUT_DIR" \\
    --output_name="{config.output_name}" \\
    --save_model_as=safetensors \\
    --save_every_n_epochs={config.save_every_n_epochs} \\
    --max_train_epochs={config.max_train_epochs} \\
    --train_batch_size={config.train_batch_size} \\
    --learning_rate={config.learning_rate} \\
    --lr_scheduler="{config.lr_scheduler}" \\
    --lr_warmup_steps={config.lr_warmup_steps} \\
    --network_module=networks.lora \\
    --network_dim={config.network_dim} \\
    --network_alpha={config.network_alpha} \\
    --resolution={config.resolution} \\
    --enable_bucket \\
    --mixed_precision="{config.mixed_precision}" \\
    --gradient_checkpointing \\
    --xformers \\
    --cache_latents \\
    --seed=42

echo ""
echo "Training complete!"
echo "LoRA saved to: $OUTPUT_DIR/{config.output_name}.safetensors"
'''


def count_dataset_images(dataset_path: Path) -> int:
    """Count images in dataset."""
    images_dir = dataset_path / "images"
    if not images_dir.exists():
        return 0
    return len(list(images_dir.glob("*.png")))


def main():
    parser = argparse.ArgumentParser(
        description="Generate Kohya training config for Guitar LoRA"
    )
    
    parser.add_argument(
        "--dataset", "-d",
        required=True,
        help="Path to dataset directory",
    )
    parser.add_argument(
        "--base-model",
        default="stabilityai/stable-diffusion-xl-base-1.0",
        help="Base model to fine-tune",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=10,
        help="Number of training epochs",
    )
    parser.add_argument(
        "--rank",
        type=int,
        default=32,
        help="LoRA rank (network_dim)",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=1e-4,
        help="Learning rate",
    )
    parser.add_argument(
        "--output-name",
        default="guitar_lora",
        help="Output LoRA filename",
    )
    
    args = parser.parse_args()
    
    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        print(f"❌ Dataset not found: {dataset_path}")
        sys.exit(1)
    
    # Count images
    image_count = count_dataset_images(dataset_path)
    if image_count == 0:
        print(f"⚠️ No images found in {dataset_path}/images/")
        print("   Run training_data_generator.py first")
    
    # Build config
    config = KohyaConfig(
        base_model=args.base_model,
        max_train_epochs=args.epochs,
        network_dim=args.rank,
        learning_rate=args.lr,
        output_name=args.output_name,
    )
    
    # Create config directory
    config_dir = dataset_path / "config"
    config_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("🎸 GUITAR LoRA — KOHYA CONFIG GENERATOR")
    print("=" * 60)
    print(f"\n📁 Dataset: {dataset_path}")
    print(f"   Images: {image_count}")
    
    # Generate configs
    print(f"\n📝 Generating configuration files...")
    
    # Training config
    training_config = generate_training_config(config, dataset_path)
    (config_dir / "training_config.toml").write_text(training_config)
    print(f"   ✅ config/training_config.toml")
    
    # Dataset config
    dataset_config = generate_dataset_config(config, dataset_path)
    (config_dir / "dataset_config.toml").write_text(dataset_config)
    print(f"   ✅ config/dataset_config.toml")
    
    # Sample prompts
    sample_prompts = generate_sample_prompts(dataset_path)
    (config_dir / "sample_prompts.txt").write_text(sample_prompts)
    print(f"   ✅ config/sample_prompts.txt")
    
    # Training script
    train_script = generate_training_script(config, dataset_path)
    script_path = config_dir / "train.sh"
    script_path.write_text(train_script)
    script_path.chmod(0o755)
    print(f"   ✅ config/train.sh")
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TRAINING CONFIGURATION")
    print("=" * 60)
    print(f"   Base model: {config.base_model}")
    print(f"   Epochs: {config.max_train_epochs}")
    print(f"   LoRA rank: {config.network_dim}")
    print(f"   Learning rate: {config.learning_rate}")
    print(f"   Output: {config.output_name}.safetensors")
    
    # Estimate training time
    # Rough estimate: ~30 seconds per image per epoch on RTX 3090
    if image_count > 0:
        est_time_per_epoch = image_count * 30 / 60  # minutes
        est_total = est_time_per_epoch * config.max_train_epochs
        print(f"\n⏱️ Estimated training time: {est_total:.0f} minutes")
        print(f"   (on RTX 3090/4090, may vary)")
    
    print(f"\n🚀 To train:")
    print(f"   cd /path/to/kohya_ss")
    print(f"   bash {config_dir.absolute()}/train.sh")
    
    print(f"\n💡 After training, use the LoRA:")
    print(f"   <lora:{config.output_name}:0.8> guitar_photo, electric guitar, ...")


if __name__ == "__main__":
    main()
