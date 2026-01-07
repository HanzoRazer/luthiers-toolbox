"""
Basic SVG Vectorizer - Phase 1
Converts AI-detected dimensions to simple SVG paths (lines and rectangles)
Phase 2 will add OpenCV edge detection and DXF export
"""
import logging
from typing import Dict, List, Tuple
import svgwrite
from svgwrite import mm

logger = logging.getLogger(__name__)


class BasicSVGVectorizer:
    """
    Phase 1: Simple SVG generator from AI dimensions
    Creates basic geometric shapes based on detected measurements
    """
    
    def __init__(self, units: str = "mm"):
        """
        Initialize vectorizer
        
        Args:
            units: Target units (mm or inch)
        """
        self.units = units
    
    def dimensions_to_svg(
        self,
        analysis_data: Dict,
        output_path: str,
        width_mm: float = 300.0,
        height_mm: float = 200.0
    ) -> str:
        """
        Convert AI-detected dimensions to SVG file
        
        Args:
            analysis_data: Output from BlueprintAnalyzer
            output_path: Path to save SVG file
            width_mm: Canvas width in mm
            height_mm: Canvas height in mm
        
        Returns:
            Path to generated SVG file
        """
        try:
            # Create SVG drawing
            dwg = svgwrite.Drawing(
                output_path,
                size=(f"{width_mm}mm", f"{height_mm}mm"),
                viewBox=f"0 0 {width_mm} {height_mm}"
            )
            
            # Add metadata
            dwg.defs.add(dwg.style("""
                .dimension-line { stroke: blue; stroke-width: 0.5; fill: none; }
                .dimension-text { font-family: Arial; font-size: 4px; fill: black; }
                .detected { stroke: green; }
                .estimated { stroke: orange; }
            """))
            
            # Add scale info as description element (svgwrite doesn't have .comment())
            scale = analysis_data.get('scale', 'Unknown')
            dwg.add(dwg.desc(f"Scale: {scale}. Generated from AI analysis with {len(analysis_data.get('dimensions', []))} dimensions"))
            
            # Draw border
            dwg.add(dwg.rect(
                insert=(5*mm, 5*mm),
                size=(f"{width_mm-10}mm", f"{height_mm-10}mm"),
                fill='none',
                stroke='black',
                stroke_width=0.5
            ))
            
            # Draw dimensions as simple lines
            dimensions = analysis_data.get('dimensions', [])
            y_offset = 15
            
            for idx, dim in enumerate(dimensions[:20]):  # Limit to first 20
                label = dim.get('label', f'Dimension {idx+1}')
                value = dim.get('value', 'N/A')
                dim_type = dim.get('type', 'unknown')
                confidence = dim.get('confidence', 'unknown')
                
                # Color code by type
                css_class = 'detected' if dim_type == 'detected' else 'estimated'
                
                # Draw dimension line
                line_start = (10*mm, y_offset*mm)
                line_end = ((width_mm - 10)*mm, y_offset*mm)
                
                dwg.add(dwg.line(
                    start=line_start,
                    end=line_end,
                    class_=f"dimension-line {css_class}"
                ))
                
                # Add label text
                dwg.add(dwg.text(
                    f"{label}: {value} ({confidence})",
                    insert=(12*mm, (y_offset + 1)*mm),
                    class_="dimension-text"
                ))
                
                y_offset += 8
            
            # Add summary
            total_dims = len(dimensions)
            detected = sum(1 for d in dimensions if d.get('type') == 'detected')
            estimated = total_dims - detected
            
            summary_y = height_mm - 10
            dwg.add(dwg.text(
                f"Total: {total_dims} dimensions | Detected: {detected} | Estimated: {estimated}",
                insert=(10*mm, summary_y*mm),
                class_="dimension-text",
                style="font-weight: bold; font-size: 5px;"
            ))
            
            # Save SVG
            dwg.save()
            logger.info(f"Generated SVG: {output_path} ({total_dims} dimensions)")
            return output_path
        
        except Exception as e:
            logger.error(f"Error generating SVG: {e}")
            raise
    
    def create_simple_geometry_svg(
        self,
        dimensions: List[Dict],
        output_path: str,
        scale_factor: float = 1.0
    ) -> str:
        """
        Create simple geometric shapes from dimensions
        (Placeholder for Phase 2 intelligent geometry extraction)
        
        Args:
            dimensions: List of dimension dictionaries
            output_path: Output SVG path
            scale_factor: Scaling multiplier (1.0 = full size)
        
        Returns:
            Path to generated SVG
        """
        # Extract numeric values from dimensions
        numeric_dims = []
        for dim in dimensions:
            value_str = dim.get('value', '')
            try:
                # Try to parse numeric value (e.g., "120mm" -> 120.0)
                import re
                match = re.search(r'([\d.]+)', value_str)
                if match:
                    numeric_dims.append(float(match.group(1)) * scale_factor)
            except:
                pass
        
        if not numeric_dims:
            logger.warning("No numeric dimensions found, creating placeholder SVG")
            numeric_dims = [100, 80]  # Default rectangle
        
        # Use first two dimensions as width/height
        width = numeric_dims[0] if len(numeric_dims) > 0 else 100
        height = numeric_dims[1] if len(numeric_dims) > 1 else 80
        
        # Create simple rectangle
        dwg = svgwrite.Drawing(
            output_path,
            size=(f"{width + 20}mm", f"{height + 20}mm")
        )
        
        dwg.add(dwg.rect(
            insert=(10*mm, 10*mm),
            size=(f"{width}mm", f"{height}mm"),
            fill='none',
            stroke='blue',
            stroke_width=0.5
        ))
        
        # Add dimension annotations
        dwg.add(dwg.text(
            f"{width}mm",
            insert=((10 + width/2)*mm, 8*mm),
            text_anchor="middle",
            style="font-size: 4px; fill: black;"
        ))
        
        dwg.add(dwg.text(
            f"{height}mm",
            insert=(8*mm, (10 + height/2)*mm),
            text_anchor="middle",
            transform=f"rotate(-90, {8}, {10 + height/2})",
            style="font-size: 4px; fill: black;"
        ))
        
        dwg.save()
        logger.info(f"Generated simple geometry SVG: {width}x{height}mm")
        return output_path


def create_vectorizer(units: str = "mm") -> BasicSVGVectorizer:
    """Factory function to create vectorizer instance"""
    return BasicSVGVectorizer(units=units)
