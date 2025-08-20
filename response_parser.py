"""
LLM response parsing utilities (XML-like tag extraction and validation).

Designed to be tolerant of slightly malformed XML commonly produced by LLMs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional


def parse_xml_tags(text: str, tags: Iterable[str]) -> Dict[str, str]:
    """Extract inner text for each tag using a permissive regex approach.

    For each tag name in 'tags', attempts to find the first occurrence of
    <tag> ... </tag> and returns the inner content as a string.
    """

    extracted: Dict[str, str] = {}
    for tag in tags:
        pattern = re.compile(rf"<{tag}>([\s\S]*?)</{tag}>", re.IGNORECASE)
        match = pattern.search(text)
        extracted[tag] = match.group(1).strip() if match else ""
    return extracted


@dataclass
class ResponseValidationResult:
    is_valid: bool
    missing_tags: List[str]
    raw_text: str


def validate_response_structure(text: str, required_tags: Iterable[str]) -> ResponseValidationResult:
    """Validate that all required tags exist in the response text."""

    missing: List[str] = []
    for tag in required_tags:
        if not re.search(rf"<{tag}>[\s\S]*?</{tag}>", text, flags=re.IGNORECASE):
            missing.append(tag)
    return ResponseValidationResult(is_valid=len(missing) == 0, missing_tags=missing, raw_text=text)


def merge_extracted_content(
    existing: Dict[str, List[str]],
    new: Dict[str, str],
    *,
    max_history: Optional[int] = None,
) -> Dict[str, List[str]]:
    """Merge latest extraction values into an accumulation dictionary.

    existing: mapping of tag -> history list
    new: mapping of tag -> latest content
    max_history: if set, truncate history lists to this length (keep most recent)
    """

    for tag, content in new.items():
        history = existing.setdefault(tag, [])
        history.append(content)
        if max_history is not None and len(history) > max_history:
            # keep the most recent 'max_history' items
            existing[tag] = history[-max_history:]
    return existing


def handle_parsing_errors(text: str) -> Dict[str, str]:
    """Fallback extraction when well-formed tags are missing.

    Returns a dictionary with a single 'answer' key as a best-effort default.
    """

    cleaned = text.strip()
    # Best-effort heuristic: try to chop off any leading/trailing code fences
    cleaned = re.sub(r"^```[a-zA-Z]*\n", "", cleaned)
    cleaned = re.sub(r"\n```$", "", cleaned)
    return {"answer": cleaned}


