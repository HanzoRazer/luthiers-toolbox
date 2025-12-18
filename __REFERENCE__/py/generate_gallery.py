"""
Universal File Gallery Generator
Scans directory for SVG/HTML files and generates index.html gallery
"""

import os
import json
from pathlib import Path
from typing import List, Dict

def scan_directory(root_dir: Path, recursive: bool = False) -> List[Dict]:
    """Scan directory for SVG and HTML files."""
    files = []
    
    pattern = "**/*" if recursive else "*"
    
    for file_path in root_dir.glob(pattern):
        if file_path.is_file():
            ext = file_path.suffix.lower()
            if ext in ['.svg', '.html']:
                # Skip the index and viewer files themselves
                if file_path.name in ['index.html', 'svg-viewer.html', 'test-viewer.html']:
                    continue
                
                files.append({
                    'name': file_path.name,
                    'path': str(file_path.relative_to(root_dir)),
                    'type': ext[1:],  # Remove the dot
                    'size': file_path.stat().st_size,
                    'description': generate_description(file_path)
                })
    
    return sorted(files, key=lambda x: (x['type'], x['name']))

def generate_description(file_path: Path) -> str:
    """Generate automatic description based on filename."""
    name = file_path.stem
    ext = file_path.suffix.lower()
    
    # Common patterns
    descriptions = {
        'radius': 'Radius arc template for guitar arching',
        'arc': 'Arc geometry reference',
        'bracing': 'Guitar bracing pattern',
        'rosette': 'Soundhole rosette design',
        'fret': 'Fretboard layout',
        'bridge': 'Bridge design template',
        'neck': 'Neck geometry',
        'body': 'Guitar body shape',
        'top': 'Top plate design',
        'back': 'Back plate design',
        'graduation': 'Thickness graduation map',
    }
    
    name_lower = name.lower()
    for keyword, desc in descriptions.items():
        if keyword in name_lower:
            return desc
    
    return f"{ext.upper()[1:]} file" if ext == '.svg' else "HTML page"

def generate_file_list_json(files: List[Dict], output_path: Path):
    """Generate JSON file list for JavaScript consumption."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(files, f, indent=2)
    print(f"✅ Generated: {output_path}")

def main():
    """Main entry point."""
    root = Path.cwd()
    print(f"🔍 Scanning: {root}")
    
    # Scan for files
    files = scan_directory(root, recursive=False)
    
    print(f"\n📁 Found {len(files)} files:")
    for f in files:
        print(f"  • {f['name']} ({f['type'].upper()}) - {f['size']:,} bytes")
    
    # Generate JSON file list
    output_json = root / 'files.json'
    generate_file_list_json(files, output_json)
    
    print(f"\n✅ Done! The index.html will auto-load from files.json")
    print(f"💡 Tip: Run this script whenever you add new files")

if __name__ == '__main__':
    main()
