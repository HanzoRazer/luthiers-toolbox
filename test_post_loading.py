"""Test script to verify post loading works"""
import sys
from pathlib import Path

# Add services/api to path
sys.path.insert(0, str(Path(__file__).parent / "services" / "api"))

from app.routers.post_router import load_builtin_posts, load_custom_posts, DATA_DIR

print(f"\n=== Testing Post Loading ===\n")
print(f"DATA_DIR: {DATA_DIR}")
print(f"DATA_DIR exists: {DATA_DIR.exists()}\n")

if DATA_DIR.exists():
    import os
    print(f"Contents of DATA_DIR:")
    for item in sorted(os.listdir(DATA_DIR)):
        print(f"  - {item}")
    print()

print("Loading builtin posts...")
builtin_posts = load_builtin_posts()
print(f"Loaded {len(builtin_posts)} builtin posts:\n")
for post in builtin_posts:
    print(f"  ✓ {post.id}: {post.name}")
    print(f"    Header lines: {len(post.header)}")
    print(f"    Footer lines: {len(post.footer)}")
    print()

print("Loading custom posts...")
custom_posts = load_custom_posts()
print(f"Loaded {len(custom_posts)} custom posts\n")

print(f"Total posts: {len(builtin_posts) + len(custom_posts)}")
