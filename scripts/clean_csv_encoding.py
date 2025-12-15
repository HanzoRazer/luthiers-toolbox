"""
CSV Encoding Cleaner
Fixes binary/encoding corruption in Carveco CSV files with spaced-out text
"""
import sys
import re
from pathlib import Path

def clean_csv_encoding(input_file: str, output_file: str = None):
    """
    Clean corrupted Carveco CSV file with spaced-out text encoding
    
    Args:
        input_file: Path to corrupted CSV
        output_file: Path to save cleaned CSV (optional, defaults to input_file + '_cleaned.csv')
    """
    input_path = Path(input_file)
    
    if output_file is None:
        output_file = input_path.parent / f"{input_path.stem}_cleaned{input_path.suffix}"
    
    print(f"Reading: {input_path}")
    
    # Read as binary and extract ASCII text
    with open(input_path, 'rb') as f:
        raw = f.read()
    
    print(f"✓ Read {len(raw)} bytes")
    print("Cleaning content...")
    
    # Convert to ASCII string, ignore non-ASCII
    text = raw.decode('ascii', errors='ignore')
    
    # Fix spaced-out text (e.g., "M e t r i c" → "Metric")
    # Pattern: Single char followed by space(s), repeated
    def fix_spaced_text(text):
        result = []
        i = 0
        while i < len(text):
            if i < len(text) - 2 and text[i].isalnum() and text[i+1] == ' ' and text[i+2].isalnum():
                # Found spaced pattern, collect characters
                word = []
                while i < len(text) and (text[i].isalnum() or text[i].isspace()):
                    if text[i].isalnum():
                        word.append(text[i])
                    elif word and i+1 < len(text) and not text[i+1].isalnum():
                        # Space at end of word
                        break
                    i += 1
                result.append(''.join(word))
            else:
                result.append(text[i])
                i += 1
        return ''.join(result)
    
    text = fix_spaced_text(text)
    
    # Remove binary control characters but keep CSV structure
    # Keep: letters, numbers, spaces, commas, quotes, newlines, periods, dashes, parentheses
    cleaned_chars = []
    for char in text:
        if (char.isalnum() or 
            char in ' ,\n\r\t."\'()-/@%:;+'):
            cleaned_chars.append(char)
    
    text = ''.join(cleaned_chars)
    
    # Fix multiple spaces
    text = re.sub(r' {2,}', ' ', text)
    
    # Fix excessive commas (max 3 consecutive)
    text = re.sub(r',{4,}', ',,,', text)
    
    # Split into lines and clean
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        # Skip empty lines or lines with only commas
        if line and not re.match(r'^[,\s]*$', line):
            cleaned_lines.append(line)
    
    content = '\n'.join(cleaned_lines)
    
    # Write cleaned file
    print(f"Writing: {output_file}")
    with open(output_file, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    
    print(f"✓ Cleaned CSV saved to: {output_file}")
    print(f"  Original lines: {len(lines)}")
    print(f"  Cleaned lines: {len(cleaned_lines)}")
    print(f"  Removed {len(lines) - len(cleaned_lines)} empty/corrupt lines")
    
    # Show first 5 lines as sample
    print("\nFirst 5 lines of cleaned file:")
    for i, line in enumerate(cleaned_lines[:5]):
        preview = line[:80] + '...' if len(line) > 80 else line
        print(f"  {i+1}: {preview}")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python clean_csv_encoding.py <input_csv> [output_csv]")
        print("Example: python clean_csv_encoding.py corrupted.csv cleaned.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = clean_csv_encoding(input_file, output_file)
    sys.exit(0 if success else 1)
