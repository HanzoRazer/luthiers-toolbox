import csv
import os

# Get the script directory
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define input/output file mappings
conversions = [
    {
        "input": os.path.join(script_dir, "Two-Moose-Set-CarveCo-V1.2", "Two Moose Set-CarveCo-V1.2.txt"),
        "output": os.path.join(script_dir, "Two-Moose-Set-CarveCo-V1.2", "Two Moose Set-CarveCo-V1.2.csv")
    },
    {
        "input": os.path.join(script_dir, "Bits-Bits-CarveCo-Complete-V1.2", "Bits Bits CarveCo Complete-V1.2.txt"),
        "output": os.path.join(script_dir, "Bits-Bits-CarveCo-Complete-V1.2", "Bits Bits CarveCo Complete-V1.2.csv")
    },
    {
        "input": os.path.join(script_dir, "Myers-Woodshop-Set-CarveCo-V1.2", "Myers Woodshop Set-CarveCo-V1.2.txt"),
        "output": os.path.join(script_dir, "Myers-Woodshop-Set-CarveCo-V1.2", "Myers Woodshop Set-CarveCo-V1.2.csv")
    },
    {
        "input": os.path.join(script_dir, "Amana-Tool-Vectric.tool.txt"),
        "output": os.path.join(script_dir, "Amana-Tool-Vectric.tool.csv")
    }
]

for conversion in conversions:
    input_file = conversion["input"]
    output_file = conversion["output"]
    
    if not os.path.exists(input_file):
        print(f"File not found: {input_file}")
        continue
    
    print(f"Converting: {input_file}")
    
    # Open the TXT file and read content (binary mode to preserve encoding)
    with open(input_file, "rb") as f:
        content = f.read()
    
    # Replace tabs with commas (if any)
    content = content.replace(b'\t', b',')
    
    # Write out as MS-DOS CSV (ASCII/ANSI encoding)
    with open(output_file, "wb") as f:
        f.write(content)
    
    print(f"  -> Created: {output_file}")

print("\nConversion complete: TXT -> MS-DOS CSV")
