#!/usr/bin/env python3
"""
Vue Component Extraction Analyzer (Enhanced)

Analyzes Vue SFC files and suggests template sections that could be extracted
into child components. Now with advanced features:
- Overlap filtering to prioritize leaf components
- Prop/emit inference
- Composable awareness
- Configurable thresholds
- v-if group detection

Usage:
    python scripts/analyze_vue_extraction.py <file.vue> [options]
    python scripts/analyze_vue_extraction.py <directory> --recursive [options]

Author: Claude Code (Enhanced)
"""

import re
import sys
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Set, Tuple, Any
from html.parser import HTMLParser
import ast


# =============================================================================
# Configuration - Now Configurable via CLI
# =============================================================================

DEFAULT_CONFIG = {
    # Minimum lines for any block to be considered for extraction
    'min_block_lines': 15,
    
    # Minimum lines for a v-if/v-else branch to be flagged
    'min_vif_lines': 20,
    
    # Minimum lines for a section/panel div to be flagged
    'min_section_lines': 25,
    
    # Filter overlapping candidates (keep only leaves)
    'filter_overlapping': True,
    
    # Infer props from template bindings
    'infer_props': True,
    
    # Detect composable usage
    'detect_composables': True,
    
    # Group v-if/v-else chains
    'group_vif_chains': True,
    
    # Section class patterns that suggest extractable components
    'section_class_patterns': [
        r'panel', r'section', r'card', r'form', r'modal', r'dialog',
        r'sidebar', r'header', r'footer', r'preview', r'editor',
        r'config', r'settings', r'params', r'options', r'results',
        r'container', r'wrapper', r'content', r'details', r'summary',
    ],
    
    # Elements that typically wrap extractable sections
    'section_elements': ['div', 'section', 'article', 'aside', 'form', 'fieldset'],
    
    # v-if patterns that suggest domain-specific branches
    'vif_domain_patterns': [
        (r"===\s*['\"](\w+)['\"]", 'type_switch'),  # type === 'foo'
        (r"===\s*(\w+)", 'enum_switch'),  # status === PENDING
        (r"\.value\s*===", 'ref_switch'),  # ref.value === x
    ],
}


# =============================================================================
# Data Classes (Enhanced)
# =============================================================================

@dataclass
class PropDefinition:
    """Inferred prop for a component."""
    name: str
    type: str  # 'String', 'Number', 'Boolean', 'Array', 'Object', 'Function'
    required: bool = False
    default: Optional[Any] = None
    source: str = ''  # Where it was found: 'binding', 'prop', 'emit'


@dataclass
class EmitDefinition:
    """Inferred event emit for a component."""
    name: str
    params: List[str] = field(default_factory=list)
    source: str = ''  # Where it was found


@dataclass
class ComposableUsage:
    """Detected composable usage in a section."""
    name: str
    import_path: str
    used_refs: List[str] = field(default_factory=list)
    used_functions: List[str] = field(default_factory=list)


@dataclass
class ExtractionCandidate:
    """A potential extraction point in a Vue template."""
    start_line: int
    end_line: int
    element: str
    trigger: str  # 'v-if', 'v-else', 'section-class', 'repeated-pattern'
    trigger_value: Optional[str] = None  # e.g., the v-if condition or class name
    confidence: str = 'MEDIUM'  # HIGH, MEDIUM, LOW
    suggested_name: Optional[str] = None
    notes: List[str] = field(default_factory=list)
    
    # Enhanced fields
    props: List[PropDefinition] = field(default_factory=list)
    emits: List[EmitDefinition] = field(default_factory=list)
    composables: List[ComposableUsage] = field(default_factory=list)
    parent_candidate: Optional[int] = None  # Index of parent candidate
    child_candidates: List[int] = field(default_factory=list)
    vif_group_id: Optional[str] = None  # ID for grouped v-if/v-else chains

    @property
    def line_count(self) -> int:
        return self.end_line - self.start_line + 1
    
    @property
    def complexity_score(self) -> float:
        """Calculate complexity score based on props, emits, and composables."""
        score = 1.0
        score += len(self.props) * 0.2
        score += len(self.emits) * 0.3
        score += len(self.composables) * 0.5
        return round(score, 2)


@dataclass
class AnalysisResult:
    """Complete analysis result for a Vue file."""
    file_path: str
    total_lines: int
    template_lines: int
    script_lines: int
    style_lines: int
    candidates: List[Dict]  # List[ExtractionCandidate] as dict
    warnings: List[str]  # List[str]
    summary: Dict[str, Any] = field(default_factory=dict)
    
    # Enhanced fields
    script_imports: List[Dict] = field(default_factory=list)
    composable_imports: List[Dict] = field(default_factory=list)
    global_components: List[str] = field(default_factory=list)


# =============================================================================
# Script Analyzer for Composable Detection and Prop Inference
# =============================================================================

class VueScriptAnalyzer:
    """Analyzes Vue <script> section to extract composables and props."""
    
    def __init__(self, script_content: str):
        self.content = script_content
        self.imports = []
        self.composables = []
        self.props = []
        self.emits = []
        self.data_props = []
        self.computed_props = []
        self.methods = []
        
        try:
            self.tree = ast.parse(script_content)
            self._analyze()
        except SyntaxError:
            self.tree = None
    
    def _analyze(self):
        """Run all analysis passes."""
        if not self.tree:
            return
        
        self._find_imports()
        self._find_composables()
        self._find_props_defineprops()
        self._find_emits_defineemits()
        self._find_data()
        self._find_computed()
        self._find_methods()
    
    def _find_imports(self):
        """Find all imports, especially composable imports."""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.imports.append({
                        'type': 'import',
                        'module': alias.name,
                        'name': alias.asname or alias.name,
                        'line': node.lineno
                    })
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    import_info = {
                        'type': 'import_from',
                        'module': module,
                        'name': alias.asname or alias.name,
                        'original_name': alias.name,
                        'line': node.lineno
                    }
                    self.imports.append(import_info)
                    
                    # Check if this is a composable (use* naming convention)
                    if alias.name.startswith('use') or (alias.asname and alias.asname.startswith('use')):
                        self.composables.append({
                            'name': alias.asname or alias.name,
                            'original_name': alias.name,
                            'module': module,
                            'line': node.lineno
                        })
    
    def _find_composables(self):
        """Find composable usage in the code."""
        if not self.tree:
            return
        
        for node in ast.walk(self.tree):
            # Look for function calls that might be composables
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    # Check if this matches any imported composable
                    for comp in self.composables:
                        if comp['name'] == func_name:
                            # Found composable usage
                            comp['usage_line'] = node.lineno
                            comp['used'] = True
    
    def _find_props_defineprops(self):
        """Find props defined with defineProps or in options API."""
        for node in ast.walk(self.tree):
            # Look for defineProps calls (Composition API)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == 'defineProps':
                    if node.args:
                        self._extract_props_from_defineprops(node.args[0])
            
            # Look for props in options API
            elif isinstance(node, ast.Dict):
                for i, key in enumerate(node.keys):
                    if key and isinstance(key, ast.Str) and key.s == 'props':
                        if i < len(node.values):
                            self._extract_props_from_options(node.values[i])
    
    def _extract_props_from_defineprops(self, props_node):
        """Extract props from defineProps argument."""
        if isinstance(props_node, ast.List):
            # Array syntax: defineProps(['foo', 'bar'])
            for el in props_node.elts:
                if isinstance(el, ast.Str):
                    self.props.append({
                        'name': el.s,
                        'type': 'any',
                        'required': False,
                        'source': 'defineProps-array'
                    })
        
        elif isinstance(props_node, ast.Dict):
            # Object syntax: defineProps({ foo: String, bar: { type: String, required: true }})
            for i, key in enumerate(props_node.keys):
                if key and isinstance(key, ast.Str):
                    prop_name = key.s
                    prop_def = props_node.values[i] if i < len(props_node.values) else None
                    
                    prop_info = self._parse_prop_object(prop_name, prop_def)
                    self.props.append(prop_info)
    
    def _parse_prop_object(self, name: str, prop_def) -> Dict:
        """Parse a prop definition object."""
        result = {
            'name': name,
            'type': 'any',
            'required': False,
            'default': None,
            'source': 'defineProps-object'
        }
        
        if isinstance(prop_def, ast.Name):
            # Simple type: foo: String
            result['type'] = prop_def.id
        
        elif isinstance(prop_def, ast.Dict):
            # Complex definition: foo: { type: String, required: true }
            for j, def_key in enumerate(prop_def.keys):
                if def_key and isinstance(def_key, ast.Str):
                    if def_key.s == 'type' and j < len(prop_def.values):
                        if isinstance(prop_def.values[j], ast.Name):
                            result['type'] = prop_def.values[j].id
                    elif def_key.s == 'required' and j < len(prop_def.values):
                        if isinstance(prop_def.values[j], ast.NameConstant):
                            result['required'] = prop_def.values[j].value
                    elif def_key.s == 'default' and j < len(prop_def.values):
                        # Store default value representation
                        result['default'] = ast.unparse(prop_def.values[j])
        
        return result
    
    def _extract_props_from_options(self, props_node):
        """Extract props from options API props object."""
        # Similar to above but for options API
        pass
    
    def _find_emits_defineemits(self):
        """Find emits defined with defineEmits or in options API."""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == 'defineEmits':
                    if node.args:
                        self._extract_emits_from_defineemits(node.args[0])
    
    def _extract_emits_from_defineemits(self, emits_node):
        """Extract emits from defineEmits argument."""
        if isinstance(emits_node, ast.List):
            for el in emits_node.elts:
                if isinstance(el, ast.Str):
                    self.emits.append({
                        'name': el.s,
                        'params': [],
                        'source': 'defineEmits-array'
                    })
    
    def _find_data(self):
        """Find data properties."""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'data':
                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.Return):
                        if isinstance(subnode.value, ast.Dict):
                            for i, key in enumerate(subnode.value.keys):
                                if key and isinstance(key, ast.Str):
                                    self.data_props.append({
                                        'name': key.s,
                                        'line': subnode.lineno
                                    })
    
    def _find_computed(self):
        """Find computed properties."""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == 'computed':
                    # Find variable assignment
                    for parent in ast.walk(self.tree):
                        if isinstance(parent, ast.Assign):
                            for target in parent.targets:
                                if isinstance(target, ast.Name):
                                    self.computed_props.append({
                                        'name': target.id,
                                        'line': node.lineno
                                    })
    
    def _find_methods(self):
        """Find methods (Composition API or Options API)."""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                if node.name not in ['data', 'setup', 'created', 'mounted', 'updated', 'unmounted']:
                    self.methods.append({
                        'name': node.name,
                        'line': node.lineno
                    })


# =============================================================================
# Enhanced HTML Parser for Vue Templates
# =============================================================================

class EnhancedVueTemplateParser(HTMLParser):
    """
    Enhanced parser that tracks more details and infers props/emits.
    """

    def __init__(self, template_lines: List[str], start_offset: int = 0, 
                 script_analyzer: Optional[VueScriptAnalyzer] = None,
                 config: Dict = None):
        super().__init__()
        self.template_lines = template_lines
        self.start_offset = start_offset
        self.script_analyzer = script_analyzer
        self.config = config or DEFAULT_CONFIG

        # Stack of open elements with detailed info
        self.element_stack: List[Dict] = []

        # Found candidates
        self.candidates: List[ExtractionCandidate] = []

        # Track v-if groups
        self.vif_groups: Dict[str, List[int]] = {}  # group_id -> candidate indices
        self.current_vif_group = None

        # Track bindings for prop inference
        self.bindings: Set[str] = set()
        self.events: Set[str] = set()

        # Current line tracking
        self.current_line = 0

    def get_line_number(self) -> int:
        """Get current line number in original file."""
        line, _ = self.getpos()
        return line + self.start_offset

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]):
        line = self.get_line_number()
        attrs_dict = dict(attrs)

        # Check for Vue directives
        has_vif = 'v-if' in attrs_dict
        has_velse = 'v-else' in attrs_dict or 'v-else-if' in attrs_dict
        vif_condition = attrs_dict.get('v-if') or attrs_dict.get('v-else-if')

        # Check for bindings (for prop inference)
        for attr_name, attr_value in attrs_dict.items():
            if attr_name.startswith(':'):
                binding_name = attr_name[1:]
                if binding_name and attr_value:
                    self.bindings.add(attr_value)
            elif attr_name.startswith('@'):
                event_name = attr_name[1:]
                if event_name and attr_value:
                    self.events.add(attr_value)

        # Check for mustache bindings (will be handled in handle_data)

        # Check for section-like classes
        class_attr = attrs_dict.get('class', '') or attrs_dict.get(':class', '')
        is_section = self._is_section_element(tag, class_attr)

        # Track v-if groups
        if has_vif and self.config.get('group_vif_chains'):
            self.current_vif_group = f"vif_group_{line}"
            self.vif_groups[self.current_vif_group] = []

        element_info = {
            'tag': tag,
            'line': line,
            'attrs': attrs_dict,
            'has_vif': has_vif,
            'has_velse': has_velse,
            'vif_condition': vif_condition,
            'is_section': is_section,
            'class': class_attr,
            'vif_group': self.current_vif_group if has_vif or has_velse else None,
            'bindings': set(),
            'children': [],
        }

        self.element_stack.append(element_info)

    def handle_endtag(self, tag: str):
        if not self.element_stack:
            return

        # Find matching start tag
        for i in range(len(self.element_stack) - 1, -1, -1):
            if self.element_stack[i]['tag'] == tag:
                elem = self.element_stack.pop(i)
                end_line = self.get_line_number()
                
                # Build child relationships
                for child in self.element_stack[i:]:
                    if child not in elem.get('children', []):
                        elem.setdefault('children', []).append(child)
                
                self._evaluate_element(elem, end_line)
                break

    def handle_data(self, data: str):
        """Handle text content, looking for mustache bindings."""
        # Find {{ foo }} bindings
        mustache_pattern = r'\{\{\s*([^}\s]+)\s*\}\}'
        matches = re.findall(mustache_pattern, data)
        for match in matches:
            # Clean up the binding (remove filters, etc.)
            binding = match.split('|')[0].strip()
            if binding and not binding.startswith('$'):
                self.bindings.add(binding)

    def _is_section_element(self, tag: str, class_attr: str) -> bool:
        """Check if element looks like a section/panel."""
        if tag not in self.config['section_elements']:
            return False

        class_lower = class_attr.lower()
        patterns = self.config['section_class_patterns']
        return any(re.search(pattern, class_lower) for pattern in patterns)

    def _evaluate_element(self, elem: Dict, end_line: int):
        """Evaluate if an element should be an extraction candidate."""
        start_line = elem['line']
        line_count = end_line - start_line + 1
        min_block = self.config['min_block_lines']

        # Skip small blocks
        if line_count < min_block:
            return

        candidate = None

        # Case 1: v-if/v-else branch
        if elem['has_vif'] or elem['has_velse']:
            min_vif = self.config['min_vif_lines']
            if line_count >= min_vif:
                candidate = self._create_vif_candidate(elem, start_line, end_line)

        # Case 2: Section-like element
        elif elem['is_section']:
            min_section = self.config['min_section_lines']
            if line_count >= min_section:
                candidate = self._create_section_candidate(elem, start_line, end_line)

        if candidate:
            # Infer props and composables if enabled
            if self.config.get('infer_props'):
                self._infer_props_for_candidate(candidate, elem)
            
            if self.config.get('detect_composables') and self.script_analyzer:
                self._detect_composables_for_candidate(candidate, elem)
            
            # Add to v-if group if applicable
            if elem['vif_group'] and self.config.get('group_vif_chains'):
                candidate.vif_group_id = elem['vif_group']
                self.vif_groups.setdefault(elem['vif_group'], []).append(len(self.candidates))
            
            self.candidates.append(candidate)

    def _create_vif_candidate(self, elem: Dict, start: int, end: int) -> ExtractionCandidate:
        """Create candidate for v-if/v-else branch."""
        condition = elem['vif_condition'] or '(v-else)'
        line_count = end - start + 1
        confidence = 'HIGH' if line_count >= 30 else 'MEDIUM'

        suggested_name = self._suggest_name_from_condition(condition)

        notes = []
        if elem['has_velse']:
            notes.append('Part of v-if/v-else chain - extract all branches together')

        return ExtractionCandidate(
            start_line=start,
            end_line=end,
            element=elem['tag'],
            trigger='v-if' if elem['has_vif'] else 'v-else',
            trigger_value=condition,
            confidence=confidence,
            suggested_name=suggested_name,
            notes=notes,
        )

    def _create_section_candidate(self, elem: Dict, start: int, end: int) -> ExtractionCandidate:
        """Create candidate for section/panel element."""
        class_attr = elem['class']
        line_count = end - start + 1
        confidence = 'HIGH' if line_count >= 40 else 'MEDIUM'

        suggested_name = self._suggest_name_from_class(class_attr)

        return ExtractionCandidate(
            start_line=start,
            end_line=end,
            element=elem['tag'],
            trigger='section-class',
            trigger_value=class_attr,
            confidence=confidence,
            suggested_name=suggested_name,
            notes=[],
        )

    def _infer_props_for_candidate(self, candidate: ExtractionCandidate, elem: Dict):
        """Infer props needed by this candidate section."""
        # Get the template section text
        start_idx = candidate.start_line - self.start_offset - 1
        end_idx = candidate.end_line - self.start_offset
        section_lines = self.template_lines[start_idx:end_idx]
        section_text = '\n'.join(section_lines)

        # Find all bindings in this section
        props_map = {}

        # 1. Mustache bindings {{ foo }}
        mustache_pattern = r'\{\{\s*([^}\s\|]+)'
        for match in re.finditer(mustache_pattern, section_text):
            binding = match.group(1).strip()
            if binding and not binding.startswith('$'):
                props_map[binding] = {
                    'name': binding,
                    'type': self._infer_type_from_context(section_text, binding),
                    'source': 'mustache'
                }

        # 2. Prop bindings :prop="value"
        prop_pattern = r':([\w-]+)="\s*([^"]+)\s*"'
        for match in re.finditer(prop_pattern, section_text):
            prop_name = match.group(1)
            value = match.group(2).strip()
            if value and not value.startswith('$'):
                props_map[value] = {
                    'name': value,
                    'type': self._infer_type_from_value(value),
                    'source': f'prop:{prop_name}'
                }

        # 3. Event bindings @click="handler"
        event_pattern = r'@([\w-]+)="\s*([^"]+)\s*"'
        for match in re.finditer(event_pattern, section_text):
            event_name = match.group(1)
            handler = match.group(2).strip()
            if handler and not handler.startswith('$'):
                candidate.emits.append(EmitDefinition(
                    name=event_name,
                    params=[handler],
                    source='template'
                ))

        # Convert to PropDefinition objects
        for prop_name, prop_info in props_map.items():
            candidate.props.append(PropDefinition(
                name=prop_name,
                type=prop_info['type'],
                required=False,
                source=prop_info['source']
            ))

    def _detect_composables_for_candidate(self, candidate: ExtractionCandidate, elem: Dict):
        """Detect which composables are used in this section."""
        if not self.script_analyzer or not self.script_analyzer.composables:
            return

        # Get section text
        start_idx = candidate.start_line - self.start_offset - 1
        end_idx = candidate.end_line - self.start_offset
        section_lines = self.template_lines[start_idx:end_idx]
        section_text = '\n'.join(section_lines)

        # Check each composable's exports against section bindings
        for comp in self.script_analyzer.composables:
            used_refs = []
            used_functions = []
            
            # Check if any of the props match composable exports
            for prop in candidate.props:
                # This is simplistic - would need actual data flow analysis
                if prop.name in section_text:
                    used_refs.append(prop.name)
            
            if used_refs or used_functions:
                candidate.composables.append(ComposableUsage(
                    name=comp['name'],
                    import_path=comp.get('module', ''),
                    used_refs=used_refs,
                    used_functions=used_functions
                ))

    def _suggest_name_from_condition(self, condition: str) -> Optional[str]:
        """Suggest component name from v-if condition."""
        # Match: type === 'arc' -> ContourArcParams
        match = re.search(r"===\s*['\"](\w+)['\"]", condition)
        if match:
            value = match.group(1)
            return f"{value.title()}Panel"

        # Match: isLoading -> LoadingState
        match = re.search(r"^(\w+)$", condition.strip())
        if match:
            name = match.group(1)
            if name.startswith('is'):
                return f"{name[2:].title()}State"
            if name.startswith('has'):
                return f"{name[3:].title()}Panel"
            if name.startswith('show'):
                return f"{name[4:].title()}Section"

        return None

    def _suggest_name_from_class(self, class_attr: str) -> Optional[str]:
        """Suggest component name from class attribute."""
        # Handle :class="styles.fooBar" -> FooBar
        match = re.search(r"styles\.(\w+)", class_attr)
        if match:
            name = match.group(1)
            return name[0].upper() + name[1:]

        # Handle class="foo-bar" -> FooBar
        match = re.search(r'["\']?([\w-]+)["\']?', class_attr)
        if match:
            name = match.group(1)
            # Convert kebab-case to PascalCase
            parts = name.split('-')
            return ''.join(p.title() for p in parts)

        return None

    def _infer_type_from_context(self, text: str, binding: str) -> str:
        """Infer the type of a binding from context."""
        # Escape special regex characters in binding to prevent pattern errors
        escaped = re.escape(binding)
        # Look for common patterns
        try:
            if re.search(rf'{escaped}\s*\(', text):
                return 'Function'
            elif re.search(rf'{escaped}\s*===?\s*true', text):
                return 'Boolean'
            elif re.search(rf'{escaped}\s*===?\s*false', text):
                return 'Boolean'
            elif re.search(rf'{escaped}\s*\.length', text):
                return 'Array|String'
            elif re.search(rf'{escaped}\s*\.\w+', text):
                return 'Object'
        except re.error:
            pass  # Fallback to 'any' on regex error
        return 'any'

    def _infer_type_from_value(self, value: str) -> str:
        """Infer type from a value string."""
        if value.startswith('ref(') or value.startswith('computed('):
            return 'Ref'
        elif value.startswith('reactive('):
            return 'Reactive'
        elif value.startswith('props.'):
            return 'Prop'
        else:
            return 'any'


# =============================================================================
# Main Analysis Functions (Enhanced)
# =============================================================================

def extract_vue_sections(content: str) -> Tuple[str, str, str, int, int, int]:
    """
    Extract template, script, and style sections from Vue SFC.
    Returns: (template, script, style, template_start_line, script_start_line, style_start_line)
    """
    lines = content.split('\n')

    template = []
    script = []
    style = []

    template_start = script_start = style_start = 0
    current_section = None

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith('<template'):
            current_section = 'template'
            template_start = i
        elif stripped.startswith('</template>'):
            current_section = None
        elif stripped.startswith('<script'):
            current_section = 'script'
            script_start = i
        elif stripped.startswith('</script>'):
            current_section = None
        elif stripped.startswith('<style'):
            current_section = 'style'
            style_start = i
        elif stripped.startswith('</style>'):
            current_section = None
        elif current_section == 'template':
            template.append(line)
        elif current_section == 'script':
            script.append(line)
        elif current_section == 'style':
            style.append(line)

    return (
        '\n'.join(template),
        '\n'.join(script),
        '\n'.join(style),
        template_start,
        script_start,
        style_start,
    )


def filter_overlapping_candidates(candidates: List[ExtractionCandidate]) -> List[ExtractionCandidate]:
    """
    Filter out candidates that contain other candidates (keep only leaves).
    Returns a new list with parent-child relationships recorded.
    """
    # Sort by start line
    sorted_cands = sorted(candidates, key=lambda c: c.start_line)
    
    # Build tree structure
    for i, cand in enumerate(sorted_cands):
        for j, other in enumerate(sorted_cands):
            if i == j:
                continue
            # Check if other is within cand
            if (other.start_line > cand.start_line and 
                other.end_line < cand.end_line):
                cand.child_candidates.append(j)
                other.parent_candidate = i
    
    # Keep only leaves (no children) OR roots with high confidence
    result = []
    for i, cand in enumerate(sorted_cands):
        if not cand.child_candidates:
            result.append(cand)
        elif cand.confidence == 'HIGH' and len(cand.child_candidates) > 3:
            # This is a complex parent that might be worth extracting
            cand.notes.append(f"Contains {len(cand.child_candidates)} sub-sections")
            result.append(cand)
    
    return result


def group_vif_chains(candidates: List[ExtractionCandidate]) -> List[ExtractionCandidate]:
    """
    Group v-if/v-else chains and update notes.
    """
    # Group by vif_group_id
    groups = {}
    for i, cand in enumerate(candidates):
        if cand.vif_group_id:
            groups.setdefault(cand.vif_group_id, []).append(i)
    
    # Update notes for grouped candidates
    for group_id, indices in groups.items():
        if len(indices) > 1:
            for idx in indices:
                candidates[idx].notes.append(
                    f"Part of {len(indices)}-branch v-if chain"
                )
                candidates[idx].suggested_name = candidates[idx].suggested_name or "ConditionalSection"
    
    return candidates


def analyze_vue_file(file_path: Path, config: Dict = None) -> AnalysisResult:
    """Analyze a Vue file and return extraction candidates with enhanced info."""
    config = config or DEFAULT_CONFIG
    content = file_path.read_text(encoding='utf-8')
    lines = content.split('\n')
    total_lines = len(lines)

    template, script, style, template_start, script_start, style_start = extract_vue_sections(content)

    template_lines = len(template.split('\n')) if template else 0
    script_lines = len(script.split('\n')) if script else 0
    style_lines = len(style.split('\n')) if style else 0

    # Analyze script section
    script_analyzer = VueScriptAnalyzer(script) if script else None

    # Parse template with enhanced parser
    parser = EnhancedVueTemplateParser(
        template.split('\n'), 
        start_offset=template_start,
        script_analyzer=script_analyzer,
        config=config
    )
    
    try:
        parser.feed(template)
    except Exception as e:
        return AnalysisResult(
            file_path=str(file_path),
            total_lines=total_lines,
            template_lines=template_lines,
            script_lines=script_lines,
            style_lines=style_lines,
            candidates=[],
            warnings=[f"Parse error: {e}"],
        )

    # Post-process candidates
    candidates = parser.candidates
    
    if config.get('group_vif_chains'):
        candidates = group_vif_chains(candidates)
    
    if config.get('filter_overlapping'):
        candidates = filter_overlapping_candidates(candidates)

    # Generate warnings
    warnings = []
    if total_lines > 500:
        warnings.append(f"File exceeds 500 LOC ({total_lines} lines) - decomposition recommended")
    if template_lines > 300:
        warnings.append(f"Template exceeds 300 lines ({template_lines}) - extract child components")
    if script_lines > 200:
        warnings.append(f"Script exceeds 200 lines ({script_lines}) - extract composables")

    # Build summary
    high_confidence = len([c for c in candidates if c.confidence == 'HIGH'])
    medium_confidence = len([c for c in candidates if c.confidence == 'MEDIUM'])

    total_props = sum(len(c.props) for c in candidates)
    total_emits = sum(len(c.emits) for c in candidates)
    total_composables = sum(len(c.composables) for c in candidates)

    summary = {
        'total_candidates': len(candidates),
        'high_confidence': high_confidence,
        'medium_confidence': medium_confidence,
        'potential_line_reduction': sum(c.line_count for c in candidates),
        'total_inferred_props': total_props,
        'total_inferred_emits': total_emits,
        'total_detected_composables': total_composables,
    }

    # Convert candidates to dict for JSON serialization
    candidate_dicts = []
    for c in candidates:
        c_dict = asdict(c)
        # Convert nested objects
        c_dict['props'] = [asdict(p) for p in c.props]
        c_dict['emits'] = [asdict(e) for e in c.emits]
        c_dict['composables'] = [asdict(co) for co in c.composables]
        c_dict['line_count'] = c.line_count
        c_dict['complexity_score'] = c.complexity_score
        candidate_dicts.append(c_dict)

    return AnalysisResult(
        file_path=str(file_path),
        total_lines=total_lines,
        template_lines=template_lines,
        script_lines=script_lines,
        style_lines=style_lines,
        candidates=candidate_dicts,
        warnings=warnings,
        summary=summary,
        script_imports=[asdict(i) for i in (script_analyzer.imports if script_analyzer else [])],
        composable_imports=[asdict(c) for c in (script_analyzer.composables if script_analyzer else [])],
    )


def format_result(result: AnalysisResult, show_details: bool = True) -> str:
    """Format analysis result for human reading with enhanced details."""
    lines = []
    lines.append(f"\n{'='*80}")
    lines.append(f"Vue Extraction Analysis: {result.file_path}")
    lines.append(f"{'='*80}\n")

    lines.append(f"Lines: {result.total_lines} total "
                 f"(template: {result.template_lines}, "
                 f"script: {result.script_lines}, "
                 f"style: {result.style_lines})\n")

    if result.warnings:
        lines.append("WARNINGS:")
        for w in result.warnings:
            lines.append(f"  [!] {w}")
        lines.append("")

    if not result.candidates:
        lines.append("No extraction candidates found (file may already be well-decomposed)")
        return '\n'.join(lines)

    lines.append(f"EXTRACTION CANDIDATES ({len(result.candidates)} found):\n")

    # Sort candidates by complexity score (highest first)
    sorted_cands = sorted(result.candidates, 
                         key=lambda c: c.get('complexity_score', 0), 
                         reverse=True)

    for i, c in enumerate(sorted_cands, 1):
        conf_icon = '[HIGH]' if c['confidence'] == 'HIGH' else '[MED] '
        
        # Indicate if this is a leaf candidate (leaf = no children, ready to extract)
        leaf_marker = " (leaf)" if not c.get('child_candidates') else ""
        
        lines.append(f"{i}. {conf_icon}{leaf_marker} Lines {c['start_line']}-{c['end_line']} "
                     f"({c['line_count']} lines)")
        lines.append(f"   Element: <{c['element']}> | Trigger: {c['trigger']}")
        
        if c['trigger_value']:
            tv = c['trigger_value']
            lines.append(f"   Condition/Class: {tv[:60]}{'...' if len(tv) > 60 else ''}")
        
        if c['suggested_name']:
            lines.append(f"   Suggested name: {c['suggested_name']}.vue")
        
        if c['notes']:
            for note in c['notes']:
                lines.append(f"   Note: {note}")
        
        # Show inferred props (if any)
        if show_details and c['props']:
            prop_names = [p['name'] for p in c['props'][:5]]
            prop_str = ', '.join(prop_names)
            if len(c['props']) > 5:
                prop_str += f" and {len(c['props'])-5} more"
            lines.append(f"   Props: {prop_str}")
        
        # Show inferred emits (if any)
        if show_details and c['emits']:
            emit_names = [e['name'] for e in c['emits'][:3]]
            emit_str = ', '.join(emit_names)
            if len(c['emits']) > 3:
                emit_str += f" and {len(c['emits'])-3} more"
            lines.append(f"   Emits: {emit_str}")
        
        # Show detected composables (if any)
        if show_details and c['composables']:
            comp_names = [comp['name'] for comp in c['composables']]
            lines.append(f"   Composables: {', '.join(comp_names)}")
        
        # Show complexity score
        if c.get('complexity_score'):
            lines.append(f"   Complexity: {c['complexity_score']}")
        
        lines.append("")

    lines.append(f"SUMMARY:")
    lines.append(f"  Candidates: {result.summary['total_candidates']} "
                 f"({result.summary['high_confidence']} high, "
                 f"{result.summary['medium_confidence']} medium)")
    lines.append(f"  Potential reduction: ~{result.summary['potential_line_reduction']} lines")
    
    if result.summary.get('total_inferred_props'):
        lines.append(f"  Inferred props: {result.summary['total_inferred_props']}")
        lines.append(f"  Inferred emits: {result.summary['total_inferred_emits']}")
        lines.append(f"  Detected composables: {result.summary['total_detected_composables']}")

    return '\n'.join(lines)


# =============================================================================
# CLI (Enhanced)
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Enhanced Vue Component Extraction Analyzer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s src/components/MyComponent.vue
  %(prog)s src/components/ --recursive
  %(prog)s src/components/MyComponent.vue --json --show-props
  %(prog)s src/components/ --recursive --min-lines 300 --min-block 20

Enhancements:
  • Overlap filtering - shows only leaf candidates
  • Prop/emit inference - suggests component interface
  • Composable detection - identifies which composables are used
  • v-if group detection - groups related conditional branches
  • Configurable thresholds - tune via CLI
        """
    )
    parser.add_argument('path', help='Vue file or directory to analyze')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--recursive', '-r', action='store_true',
                        help='Recursively analyze directory')
    parser.add_argument('--min-lines', type=int, default=500,
                        help='Only analyze files over this LOC (default: 500)')
    
    # Enhancement options
    parser.add_argument('--min-block', type=int, default=15,
                        help='Minimum lines for any block (default: 15)')
    parser.add_argument('--min-vif', type=int, default=20,
                        help='Minimum lines for v-if branch (default: 20)')
    parser.add_argument('--min-section', type=int, default=25,
                        help='Minimum lines for section div (default: 25)')
    parser.add_argument('--no-overlap-filter', action='store_true',
                        help='Disable overlap filtering (show all candidates)')
    parser.add_argument('--no-prop-inference', action='store_true',
                        help='Disable prop/emit inference')
    parser.add_argument('--no-composable-detection', action='store_true',
                        help='Disable composable detection')
    parser.add_argument('--no-vif-grouping', action='store_true',
                        help='Disable v-if group detection')
    parser.add_argument('--show-details', action='store_true',
                        help='Show detailed prop/emit info in output')
    parser.add_argument('--output-file', '-o', type=Path,
                        help='Write output to file instead of stdout')

    args = parser.parse_args()
    path = Path(args.path)

    # Build configuration
    config = DEFAULT_CONFIG.copy()
    config.update({
        'min_block_lines': args.min_block,
        'min_vif_lines': args.min_vif,
        'min_section_lines': args.min_section,
        'filter_overlapping': not args.no_overlap_filter,
        'infer_props': not args.no_prop_inference,
        'detect_composables': not args.no_composable_detection,
        'group_vif_chains': not args.no_vif_grouping,
    })

    if path.is_file():
        files = [path]
    elif path.is_dir():
        pattern = '**/*.vue' if args.recursive else '*.vue'
        files = list(path.glob(pattern))
    else:
        print(f"Error: {path} not found", file=sys.stderr)
        sys.exit(1)

    results = []
    for f in files:
        # Quick line count check
        try:
            line_count = len(f.read_text(encoding='utf-8').split('\n'))
            if line_count < args.min_lines:
                continue

            result = analyze_vue_file(f, config)
            results.append(result)
        except Exception as e:
            print(f"Error analyzing {f}: {e}", file=sys.stderr)
            continue

    if not results:
        print(f"No Vue files over {args.min_lines} LOC found")
        sys.exit(0)

    # Prepare output
    if args.json:
        output = json.dumps([asdict(r) for r in results], indent=2, default=str)
    else:
        output = '\n---\n'.join(format_result(r, show_details=args.show_details) for r in results)

    # Write to file or stdout
    if args.output_file:
        args.output_file.write_text(output)
        print(f"Analysis written to {args.output_file}")
    else:
        print(output)


if __name__ == '__main__':
    main()