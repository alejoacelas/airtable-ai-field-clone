"""
LLM response parsing utilities (XML-like tag extraction and validation).

Designed to be tolerant of slightly malformed XML commonly produced by LLMs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional
import pandas as pd


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


def extract_tags_from_dataframe(df: pd.DataFrame, tag_name: str) -> pd.DataFrame:
    """Extract content from XML tags in a dataframe, preserving structure.
    
    For each column, if it contains <tag>content</tag>, replace the cell value 
    with the extracted content. If no tag is found, leave empty or original content.
    
    Args:
        df: Input dataframe with potential XML-tagged content
        tag_name: Name of XML tag to extract (e.g., 'sources', 'answer')
        
    Returns:
        New dataframe with same structure but extracted tag content
    """
    if df.empty:
        return df.copy()
        
    result_df = df.copy()
    
    for col in result_df.columns:
        for idx in result_df.index:
            cell_value = str(result_df.loc[idx, col]) if pd.notna(result_df.loc[idx, col]) else ""
            
            if cell_value:
                # Extract tag content using existing parse_xml_tags function
                extracted = parse_xml_tags(cell_value, [tag_name])
                tag_content = extracted.get(tag_name, "")
                
                # Replace cell with extracted content (empty if no tag found)
                result_df.loc[idx, col] = tag_content
            else:
                result_df.loc[idx, col] = ""
    
    return result_df


