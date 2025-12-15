"""
Filename Template Token Engine

Supports dynamic filename generation for CAM exports with contextual token replacement.

Supported Tokens:
- {preset} - Preset name (e.g., "Strat_Roughing")
- {machine} - Machine ID (e.g., "CNC_Router_01")
- {post} - Post-processor ID (e.g., "GRBL", "Mach4")
- {operation} - Operation type (e.g., "adaptive", "roughing", "drilling")
- {material} - Material name (e.g., "Maple", "Mahogany")
- {neck_profile} - Neck profile name (e.g., "Fender_Modern_C")
- {neck_section} - Neck section name (e.g., "Fret_1", "Nut", "Heel")
- {compare_mode} - Compare mode indicator (e.g., "baseline", "variant_A")
- {date} - Date in YYYY-MM-DD format
- {timestamp} - Full timestamp (YYYY-MM-DD_HH-MM-SS)
- {job_id} - Job intelligence run ID (e.g., "job_12345")
- {raw} - Raw geometry source (e.g., "body_outline", "pickup_cavity")

Token Resolution Rules:
1. Missing context values → token remains literal (e.g., "{neck_profile}" if neck data unavailable)
2. Empty/None values → token removed from output
3. Tokens are case-insensitive ({Preset} = {preset})
4. Unknown tokens → remain literal for forward compatibility
5. Special characters in values → sanitized (spaces → underscores, slashes removed)

Examples:
>>> resolve_template("{preset}__{date}.gcode", {"preset": "J45_Pocket"})
'J45_Pocket__2025-11-28.gcode'

>>> resolve_template("{preset}__{neck_profile}__{neck_section}.nc", {
...     "preset": "Strat Roughing",
...     "neck_profile": "Fender Modern C",
...     "neck_section": "Fret 1"
... })
'Strat_Roughing__Fender_Modern_C__Fret_1.nc'

>>> resolve_template("{preset}__{machine}__{post}.gcode", {
...     "preset": "Adaptive Test",
...     "machine": "CNC Router 01",
...     "post": "GRBL"
... })
'Adaptive_Test__CNC_Router_01__GRBL.gcode'
"""
import re
from datetime import datetime
from typing import Any, Dict, Optional


def sanitize_filename_part(value: str) -> str:
    """
    Sanitize a filename component by removing/replacing unsafe characters.
    
    Rules:
    - Spaces → underscores
    - Forward/backslashes → removed
    - Colons → hyphens (for timestamps)
    - Multiple underscores → single underscore
    - Leading/trailing underscores → trimmed
    
    Args:
        value: Raw filename component
    
    Returns:
        Sanitized string safe for filesystem use
    """
    if not value:
        return ""
    
    # Replace spaces with underscores
    sanitized = value.replace(" ", "_")
    
    # Remove slashes
    sanitized = sanitized.replace("/", "").replace("\\", "")
    
    # Replace colons with hyphens (for timestamps)
    sanitized = sanitized.replace(":", "-")
    
    # Remove other unsafe characters (keep alphanumeric, underscore, hyphen, period)
    sanitized = re.sub(r'[^\w\-.]', '_', sanitized)
    
    # Collapse multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Trim leading/trailing underscores
    sanitized = sanitized.strip("_")
    
    return sanitized


def resolve_template(template: str, context: Dict[str, Any]) -> str:
    """
    Resolve filename template with context values.
    
    Args:
        template: Filename template with {token} placeholders
        context: Dictionary of token values
    
    Returns:
        Resolved filename with tokens replaced
    
    Examples:
        >>> resolve_template("{preset}_{date}.nc", {"preset": "Test"})
        'Test_2025-11-28.nc'
        
        >>> resolve_template("{preset}__{neck_profile}.gcode", {
        ...     "preset": "Strat",
        ...     "neck_profile": None
        ... })
        'Strat__.gcode'
        
        >>> resolve_template("{preset}__{unknown}__{post}.nc", {
        ...     "preset": "Test",
        ...     "post": "GRBL"
        ... })
        'Test__{unknown}__GRBL.nc'
    """
    # Case-insensitive token mapping
    context_lower = {k.lower(): v for k, v in context.items()}
    
    # Add date/timestamp tokens if not provided
    now = datetime.now()
    context_lower.setdefault("date", now.strftime("%Y-%m-%d"))
    context_lower.setdefault("timestamp", now.strftime("%Y-%m-%d_%H-%M-%S"))
    
    # Find all tokens in template
    token_pattern = r'\{([^}]+)\}'
    
    def replace_token(match: re.Match) -> str:
        token_name = match.group(1).lower()
        
        # Check if token exists in context
        if token_name in context_lower:
            value = context_lower[token_name]
            
            # Handle None/empty values
            if value is None or value == "":
                return ""
            
            # Convert to string and sanitize
            return sanitize_filename_part(str(value))
        
        # Unknown token → keep literal for forward compatibility
        return match.group(0)
    
    # Replace all tokens
    resolved = re.sub(token_pattern, replace_token, template)
    
    # Clean up multiple consecutive delimiters (e.g., "___" → "__")
    resolved = re.sub(r'__+', '__', resolved)
    resolved = re.sub(r'--+', '-', resolved)
    
    # Trim leading/trailing delimiters
    resolved = resolved.strip("_-")
    
    return resolved


def resolve_export_filename(
    preset_name: Optional[str] = None,
    machine_id: Optional[str] = None,
    post_id: Optional[str] = None,
    operation: Optional[str] = None,
    material: Optional[str] = None,
    neck_profile: Optional[str] = None,
    neck_section: Optional[str] = None,
    compare_mode: Optional[str] = None,
    job_id: Optional[str] = None,
    raw: Optional[str] = None,
    template: Optional[str] = None,
    extension: str = "nc"
) -> str:
    """
    Generate export filename from preset and context data.
    
    Args:
        preset_name: Name of preset being used
        machine_id: Machine identifier
        post_id: Post-processor identifier
        operation: CAM operation type (adaptive, roughing, drilling, etc.)
        material: Material being machined
        neck_profile: Neck profile name (for neck operations)
        neck_section: Neck section/fret number (for neck operations)
        compare_mode: Compare mode identifier (baseline, variant_A, etc.)
        job_id: Job intelligence run ID
        raw: Raw geometry source identifier
        template: Custom filename template (uses default if None)
        extension: File extension (default: "nc")
    
    Returns:
        Resolved filename with extension
    
    Examples:
        >>> resolve_export_filename(
        ...     preset_name="Strat Pocket",
        ...     post_id="GRBL",
        ...     extension="gcode"
        ... )
        'Strat_Pocket__GRBL__2025-11-28.gcode'
        
        >>> resolve_export_filename(
        ...     preset_name="Neck Rough",
        ...     neck_profile="Fender Modern C",
        ...     neck_section="Fret 5",
        ...     template="{preset}__{neck_profile}__{neck_section}.nc"
        ... )
        'Neck_Rough__Fender_Modern_C__Fret_5.nc'
    """
    # Default template if none provided
    if template is None:
        # Intelligent default based on available context
        if neck_profile or neck_section:
            # Neck operation template
            template = "{preset}__{neck_profile}__{neck_section}__{date}"
        elif compare_mode:
            # Compare mode template
            template = "{preset}__{compare_mode}__{post}__{date}"
        elif operation:
            # Operation-specific template
            template = "{preset}__{operation}__{post}__{date}"
        else:
            # Generic template
            template = "{preset}__{post}__{date}"
    
    # Build context dictionary
    context = {
        "preset": preset_name,
        "machine": machine_id,
        "post": post_id,
        "operation": operation,
        "material": material,
        "neck_profile": neck_profile,
        "neck_section": neck_section,
        "compare_mode": compare_mode,
        "job_id": job_id,
        "raw": raw,
    }
    
    # Resolve template
    base_filename = resolve_template(template, context)
    
    # Ensure we have at least a default filename
    if not base_filename or base_filename == "":
        now = datetime.now()
        base_filename = f"export_{now.strftime('%Y%m%d_%H%M%S')}"
    
    # Add extension
    if not extension.startswith("."):
        extension = f".{extension}"
    
    return f"{base_filename}{extension}"


def validate_template(template: str) -> Dict[str, Any]:
    """
    Validate a filename template and return analysis.
    
    Args:
        template: Filename template to validate
    
    Returns:
        Dictionary with validation results:
        - valid: bool - Whether template is valid
        - tokens: list - List of tokens found in template
        - unknown_tokens: list - Tokens not in supported set
        - warnings: list - Potential issues
    
    Examples:
        >>> validate_template("{preset}__{post}.nc")
        {'valid': True, 'tokens': ['preset', 'post'], 'unknown_tokens': [], 'warnings': []}
        
        >>> validate_template("{preset}__{unknown}__{post}.nc")
        {'valid': True, 'tokens': ['preset', 'unknown', 'post'], 
         'unknown_tokens': ['unknown'], 'warnings': ['Unknown token: {unknown}']}
    """
    # Supported token set
    supported_tokens = {
        "preset", "machine", "post", "operation", "material",
        "neck_profile", "neck_section", "compare_mode",
        "date", "timestamp", "job_id", "raw"
    }
    
    # Find all tokens
    token_pattern = r'\{([^}]+)\}'
    matches = re.findall(token_pattern, template)
    tokens = [m.lower() for m in matches]
    
    # Find unknown tokens
    unknown_tokens = [t for t in tokens if t not in supported_tokens]
    
    # Generate warnings
    warnings = []
    if unknown_tokens:
        for token in unknown_tokens:
            warnings.append(f"Unknown token: {{{token}}}")
    
    if not tokens:
        warnings.append("Template contains no tokens (static filename)")
    
    # Check for potential issues
    if template.count("{") != template.count("}"):
        warnings.append("Mismatched braces in template")
    
    return {
        "valid": template.count("{") == template.count("}"),
        "tokens": tokens,
        "unknown_tokens": unknown_tokens,
        "warnings": warnings
    }
