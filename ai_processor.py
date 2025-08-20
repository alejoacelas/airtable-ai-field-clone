"""
OpenAI Responses API integration module.

This module provides:
- Async client setup using the OpenAI Responses API
- Prompt templating with column reference substitution
- Robust retry logic with tenacity for transient failures
- Helpers to extract text and XML-tagged content from responses
- Batch prompt execution with bounded concurrency

Notes:
- Prefers the Responses API (client.responses.create) per project guidelines
- Attempts to read API key from Streamlit secrets first, then environment
"""

from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple
import importlib


# Optional Streamlit secrets support
def _read_api_key_from_streamlit() -> Optional[str]:
    try:
        st = importlib.import_module("streamlit")  # type: ignore
        secrets = getattr(st, "secrets", None)
        if secrets is None:
            return None
        if "openai" in secrets and "api_key" in secrets["openai"]:
            return str(secrets["openai"]["api_key"])  # type: ignore
        if "OPENAI_API_KEY" in secrets:
            return str(secrets["OPENAI_API_KEY"])  # type: ignore
    except Exception:
        return None
    return None


def setup_openai_client() -> Tuple[Any, str]:
    """Initialize and return an AsyncOpenAI client along with default model.

    Priority for API key:
    1) Streamlit secrets: [openai][api_key] or OPENAI_API_KEY
    2) Environment variable: OPENAI_API_KEY

    Returns:
        (client, default_model)
    """

    api_key = _read_api_key_from_streamlit() or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Provide it via Streamlit secrets or environment."
        )

    default_model = os.getenv("DEFAULT_MODEL", "gpt-5")
    openai_mod = importlib.import_module("openai")
    AsyncOpenAI = getattr(openai_mod, "AsyncOpenAI")
    client = AsyncOpenAI(api_key=api_key)
    return client, default_model


_DOUBLE_BRACE_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_\- ]+)\s*\}\}")


def build_prompt_with_references(
    prompt_template: str,
    row_values: Dict[str, Any],
) -> str:
    """Substitute column references inside a template string.

    Supported syntax:
    - {{column_name}}

    Whitespace around names is ignored. If a value is missing, empty string is used.
    """

    def normalize_key(raw: str) -> str:
        return raw.strip()

    def replace_double(match: re.Match[str]) -> str:
        key = normalize_key(match.group(1))
        value = row_values.get(key, "")
        return "" if value is None else str(value)

    result = _DOUBLE_BRACE_PATTERN.sub(replace_double, prompt_template)
    return result


def _get_text_from_response(response: Any) -> str:
    """Extract plain text from a Responses API result.

    Tries the convenient 'output_text' first, then reconstructs from content parts.
    """

    # Newer SDKs expose 'output_text'
    text = getattr(response, "output_text", None)
    if isinstance(text, str) and text.strip():
        return text

    # Fallback: assemble from output -> content -> text
    try:
        parts: List[str] = []
        output = getattr(response, "output", None)
        if isinstance(output, list):
            for item in output:
                content = getattr(item, "content", None)
                if isinstance(content, list):
                    for piece in content:
                        # piece may be Text content with 'text' field
                        piece_text = getattr(piece, "text", None)
                        if piece_text and isinstance(piece_text, dict):
                            value = piece_text.get("value")
                            if isinstance(value, str):
                                parts.append(value)
                        elif isinstance(piece_text, str):
                            parts.append(piece_text)
        if parts:
            return "\n".join(parts)
    except Exception:
        pass

    # As a last resort, string cast
    return str(response)


def extract_xml_content(xml_like_text: str, tags: Iterable[str]) -> Dict[str, str]:
    """Extract content for given XML-like tags using regex as a tolerant parser.

    This is intentionally permissive to handle LLM-generated markup that may not be
    perfectly well-formed XML.
    """

    extracted: Dict[str, str] = {}
    for tag in tags:
        # Non-greedy match to capture inner content; DOTALL to span newlines
        pattern = re.compile(rf"<{tag}>([\s\S]*?)</{tag}>", re.IGNORECASE)
        match = pattern.search(xml_like_text)
        if match:
            extracted[tag] = match.group(1).strip()
        else:
            extracted[tag] = ""
    return extracted


def handle_api_errors(error: Exception) -> Dict[str, Any]:
    """Normalize API errors into a structured dictionary for display/logging."""

    error_type = type(error).__name__
    message = str(error)
    return {
        "error_type": error_type,
        "message": message,
        "is_rate_limit": "Rate" in message or "429" in message,
        "is_timeout": "timeout" in message.lower(),
        "raw": message,
    }


async def _call_responses_api(
    client: Any,
    prompt: str,
    model: str,
    needs_search: bool = False,
    tool_type: str = "web_search_preview",
) -> str:
    """Single Responses API call with retry using tenacity if available.

    Returns plain text aggregated from the response.
    """

    # Try to use tenacity if installed; otherwise do a simple manual retry with backoff
    try:
        tenacity = importlib.import_module("tenacity")
        retry = getattr(tenacity, "retry")
        wait_random_exponential = getattr(tenacity, "wait_random_exponential")
        stop_after_attempt = getattr(tenacity, "stop_after_attempt")

        @retry(wait=wait_random_exponential(min=5, max=60 * 5), stop=stop_after_attempt(6))
        async def _inner() -> str:
            tools = [{"type": tool_type}] if needs_search else []
            args = {
                "model": model,
                "input": prompt,
                "tools": tools,  # type: ignore[arg-type]
            }
            reasoning_args = {"reasoning": {"effort": "high"}}
            args = args | reasoning_args if model == "gpt-5" and needs_search else args
            
            response = await client.responses.create(
                **args
            )
            return _get_text_from_response(response)

        return await _inner()
    except Exception:
        # Fallback manual retry with exponential backoff and jitter
        import random
        attempts = 6
        base = 1.0
        for attempt in range(1, attempts + 1):
            try:
                tools = [{"type": tool_type}] if needs_search else []
                response = await client.responses.create(
                    model=model,
                    input=prompt,
                    tools=tools,  # type: ignore[arg-type]
                )
                return _get_text_from_response(response)
            except Exception:
                if attempt >= attempts:
                    raise
                # Exponential backoff with jitter
                sleep_s = min(60.0, base * (2 ** (attempt - 1)))
                sleep_s += random.uniform(0, 1)
                await asyncio.sleep(sleep_s)


@dataclass
class PromptJob:
    row_index: int
    column_name: str
    prompt: str
    needs_search: bool = False


@dataclass
class PromptResult:
    row_index: int
    column_name: str
    text: str = ""
    error: Optional[Dict[str, Any]] = None


async def execute_batch_prompts(
    client: Any,
    model: str,
    jobs: List[PromptJob],
    *,
    max_concurrent_requests: Optional[int] = None,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> List[PromptResult]:
    """Execute multiple prompts concurrently with bounded concurrency and retries.

    Args:
        client: Initialized AsyncOpenAI client
        model: Model name (e.g., "gpt-4.1")
        jobs: List of PromptJob to execute
        max_concurrent_requests: Optional override for concurrency limit
        progress_callback: Optional callback invoked as (completed, total)
    """

    total = len(jobs)
    if total == 0:
        return []

    concurrency_env = os.getenv("MAX_CONCURRENT_REQUESTS")
    limit = (
        max_concurrent_requests
        if max_concurrent_requests is not None
        else int(concurrency_env) if concurrency_env else 5
    )

    semaphore = asyncio.Semaphore(max(1, limit))
    completed_count = 0
    results: List[PromptResult] = [PromptResult(j.row_index, j.column_name) for j in jobs]

    async def run_one(idx: int, job: PromptJob) -> None:
        nonlocal completed_count
        try:
            async with semaphore:
                text = await _call_responses_api(
                    client=client,
                    prompt=job.prompt,
                    model=model,
                    needs_search=job.needs_search,
                )
                results[idx].text = text
        except Exception as exc:  # noqa: BLE001
            results[idx].error = handle_api_errors(exc)
        finally:
            completed_count += 1
            if progress_callback:
                try:
                    progress_callback(completed_count, total)
                except Exception:
                    # Do not fail batch for progress UI issues
                    pass

    await asyncio.gather(*[run_one(i, job) for i, job in enumerate(jobs)])
    return results


# Convenience wrapper for one-off prompt execution
async def execute_single_prompt(
    client: Any,
    prompt: str,
    model: Optional[str] = None,
    *,
    needs_search: bool = False,
) -> str:
    if model is None:
        _, default_model = setup_openai_client()
        model = default_model
    return await _call_responses_api(client=client, prompt=prompt, model=model, needs_search=needs_search)


