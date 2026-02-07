"""
AI Context Adapter - Docs Excerpt Provider

Provides read-only documentation excerpts relevant to the user's context.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..schemas import (
    AdapterWarning,
    ContextAttachment,
    ContextRequest,
    ContextSource,
    RedactionPolicy,
    SourceKind,
    WarningCode,
)


# Documentation index - maps topics to relevant doc files
DOC_INDEX: Dict[str, List[str]] = {
    "workflow": [
        "docs/OPERATION_EXECUTION_GOVERNANCE_v1.md",
        "docs/CNC_SAW_LAB_DEVELOPER_GUIDE.md",
    ],
    "boundary": [
        "docs/BOUNDARY_RULES.md",
        "FENCE_REGISTRY.json",
    ],
    "rosette": [
        "docs/ART_STUDIO_GUIDE.md",
    ],
    "cam": [
        "ROUTER_MAP.md",
        "docs/ENDPOINT_TRUTH_MAP.md",
    ],
    "feasibility": [
        "contracts/SERVER_SIDE_FEASIBILITY_ENFORCEMENT_CONTRACT_v1.md",
    ],
    "artifact": [
        "contracts/RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md",
    ],
    "api": [
        "docs/ENDPOINT_TRUTH_MAP.md",
        "ROUTER_MAP.md",
    ],
    "getting_started": [
        ".github/copilot-instructions.md",
        "README.md",
    ],
}

# Maximum excerpt length
MAX_EXCERPT_LENGTH = 2000


class DocsExcerptProvider:
    """
    Provides docs_excerpt context from project documentation.
    
    Includes:
    - Relevant documentation snippets
    - Contract references
    - Guide excerpts
    
    Excerpts are truncated and focused on the relevant section.
    """
    
    def __init__(self, docs_root: Optional[str] = None):
        """
        Initialize provider.
        
        Args:
            docs_root: Root directory for documentation (defaults to repo root)
        """
        if docs_root:
            self.docs_root = Path(docs_root)
        else:
            # Try to find repo root
            self.docs_root = self._find_repo_root()
    
    @property
    def source_kind(self) -> SourceKind:
        return SourceKind.DOCS_EXCERPT
    
    def provide(
        self,
        req: ContextRequest,
        policy: RedactionPolicy,
    ) -> Tuple[List[ContextSource], List[ContextAttachment], List[AdapterWarning]]:
        """Provide documentation excerpts."""
        sources: List[ContextSource] = []
        attachments: List[ContextAttachment] = []
        warnings: List[AdapterWarning] = []
        
        # Extract topics from intent
        topics = self._extract_topics(req.intent)
        
        # Gather relevant doc files
        doc_files: List[str] = []
        for topic in topics:
            doc_files.extend(DOC_INDEX.get(topic, []))
        
        # Remove duplicates while preserving order
        seen: set[str] = set()
        unique_docs: List[str] = []
        for doc in doc_files:
            if doc not in seen:
                seen.add(doc)
                unique_docs.append(doc)
        
        # Limit to 3 most relevant docs
        unique_docs = unique_docs[:3]
        
        if not unique_docs:
            # Provide getting started docs as fallback
            unique_docs = DOC_INDEX.get("getting_started", [])[:2]
        
        for doc_path in unique_docs:
            excerpt = self._read_excerpt(doc_path, req.intent)
            if excerpt:
                sources.append(ContextSource(
                    source_id=f"docs_{Path(doc_path).stem}",
                    kind=SourceKind.DOCS_EXCERPT,
                    content_type="text/markdown",
                    payload={
                        "doc_path": doc_path,
                        "excerpt": excerpt,
                        "truncated": len(excerpt) >= MAX_EXCERPT_LENGTH,
                    },
                ))
            else:
                warnings.append(AdapterWarning(
                    code=WarningCode.SCOPE_NOT_FOUND,
                    message=f"Could not read doc: {doc_path}",
                ))
        
        return sources, attachments, warnings
    
    def _find_repo_root(self) -> Path:
        """Find the repository root directory."""
        # Start from this file's location
        current = Path(__file__).resolve()
        
        # Walk up looking for indicators of repo root
        for parent in [current] + list(current.parents):
            if (parent / ".github").is_dir():
                return parent
            if (parent / "services" / "api").is_dir():
                return parent
        
        # Fallback
        return Path.cwd()
    
    def _extract_topics(self, intent: str) -> List[str]:
        """Extract documentation topics from intent string."""
        topics: List[str] = []
        intent_lower = intent.lower()
        
        # Topic keyword mapping
        keyword_map = {
            "workflow": "workflow",
            "session": "workflow",
            "boundary": "boundary",
            "fence": "boundary",
            "import": "boundary",
            "rosette": "rosette",
            "art": "rosette",
            "pattern": "rosette",
            "cam": "cam",
            "toolpath": "cam",
            "gcode": "cam",
            "feasibility": "feasibility",
            "artifact": "artifact",
            "run": "artifact",
            "api": "api",
            "endpoint": "api",
            "router": "api",
        }
        
        for keyword, topic in keyword_map.items():
            if keyword in intent_lower and topic not in topics:
                topics.append(topic)
        
        return topics
    
    def _read_excerpt(self, doc_path: str, intent: str) -> Optional[str]:
        """
        Read an excerpt from a documentation file.
        
        Tries to find the most relevant section based on the intent.
        """
        full_path = self.docs_root / doc_path
        
        if not full_path.exists():
            return None
        
        try:
            content = full_path.read_text(encoding="utf-8")
        except OSError:  # WP-1: narrowed from except Exception
            return None
        
        # If content is short enough, return it all
        if len(content) <= MAX_EXCERPT_LENGTH:
            return content
        
        # Try to find relevant section
        excerpt = self._find_relevant_section(content, intent)
        
        if excerpt:
            return excerpt
        
        # Fallback: return beginning of file
        return content[:MAX_EXCERPT_LENGTH] + "\n\n[... truncated ...]"
    
    def _find_relevant_section(self, content: str, intent: str) -> Optional[str]:
        """Find the most relevant section in the document."""
        intent_lower = intent.lower()
        lines = content.split("\n")
        
        # Find headers that might be relevant
        best_start = 0
        best_score = 0
        
        for i, line in enumerate(lines):
            if line.startswith("#"):
                # Score this header
                header_lower = line.lower()
                score = sum(1 for word in intent_lower.split() if word in header_lower)
                
                if score > best_score:
                    best_score = score
                    best_start = i
        
        if best_score > 0:
            # Extract section from best header
            section_lines = [lines[best_start]]
            char_count = len(lines[best_start])
            
            for line in lines[best_start + 1:]:
                # Stop at next same-level or higher header
                if line.startswith("#") and not line.startswith("##"):
                    break
                
                section_lines.append(line)
                char_count += len(line) + 1
                
                if char_count >= MAX_EXCERPT_LENGTH:
                    section_lines.append("\n[... truncated ...]")
                    break
            
            return "\n".join(section_lines)
        
        return None


# Singleton instance
docs_excerpt_provider = DocsExcerptProvider()
