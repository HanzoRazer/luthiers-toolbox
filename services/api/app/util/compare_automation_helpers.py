# compare_automation_helpers.py
# B22.13: Helper functions for compare automation API

from typing import Optional


async def resolve_svg(source: dict) -> str:
    """
    Resolve SVG text from the given SvgSource.
    
    Args:
        source: Dict with 'kind' and 'value' keys
            - kind='svg': value is raw SVG text
            - kind='id': value is asset ID to lookup
    
    Returns:
        SVG text as string
    
    Raises:
        ValueError: If source kind is unsupported or ID not found
    """
    kind = source.get("kind")
    value = source.get("value", "")
    
    if kind == "svg":
        return value
    
    if kind == "id":
        svg = await load_svg_by_id(value)
        if not svg:
            raise ValueError(f"Unknown SVG id: {value}")
        return svg
    
    raise ValueError(f"Unsupported SVG kind: {kind}")


async def load_svg_by_id(svg_id: str) -> Optional[str]:
    """
    Load SVG content by asset ID.
    
    TODO: Implement real storage lookup:
    - Database query
    - File system read
    - S3/cloud storage
    - Cache layer
    
    Args:
        svg_id: Asset identifier
    
    Returns:
        SVG text if found, None otherwise
    """
    # Placeholder for real implementation
    # Example integration points:
    # - await db.query("SELECT content FROM svg_assets WHERE id = ?", svg_id)
    # - Path(f"assets/svg/{svg_id}.svg").read_text()
    # - await s3_client.get_object(bucket, f"svg/{svg_id}")
    
    return None


async def compute_diff_for_automation(
    left_svg: str,
    right_svg: str,
    mode: str,
    include_layers: bool = True,
) -> dict:
    """
    Core comparison engine wrapper for automation API.
    
    This should delegate to the same logic used by interactive CompareLab,
    ensuring consistency between UI and headless modes.
    
    Args:
        left_svg: Left SVG content
        right_svg: Right SVG content
        mode: Comparison mode (side-by-side, overlay, delta)
        include_layers: Whether to analyze layer differences
    
    Returns:
        Dict shaped for CompareAutomationJsonResult:
        {
            'fullBBox': {...},
            'diffBBox': {...},
            'layers': [...],
            'arcStats': {...}  # if arc-enhanced
        }
    
    TODO: Wire to actual compare engine
    Example integration:
    ```python
    from compare_service import compute_diff
    
    result = await compute_diff(
        left_svg=left_svg,
        right_svg=right_svg,
        mode=mode,
        include_layers=include_layers,
    )
    return result
    ```
    """
    raise NotImplementedError(
        "Wire compute_diff_for_automation to your compare engine. "
        "See compare_automation_helpers.py for integration guidance."
    )
