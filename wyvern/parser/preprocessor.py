"""
Transforms Draconic template syntax into parseable Python, preserving line/column
positions so AST node locations map back to the original source.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Region:
    """A slice of Python-parseable code extracted from a Draconic document."""
    code: str
    line_offset: int  # 0-indexed line in the original document where this region starts
    col_offset: int = 0


# Regex patterns for Draconic template syntax
_DRAC2_RE = re.compile(r"<drac2>(.*?)</drac2>", re.DOTALL)
_DOUBLE_BRACE_RE = re.compile(r"\{\{(.*?)\}\}", re.DOTALL)
# {expr} — dice/variable expressions, NOT double-brace
_SINGLE_BRACE_RE = re.compile(r"(?<!\{)\{([^{}]+)\}(?!\})")
# &ARGS& and &N& argument placeholders
_ARG_PLACEHOLDER_RE = re.compile(r"&(\w+)&")
# Draconic allows `except "ErrorName":` and `except 'ErrorName' as e:` — invalid Python
# Regex may misfire if this pattern appears inside a string literal, which is an accepted
# limitation given the preprocessor is regex-based throughout.
_DRAC_EXCEPT_RE = re.compile(r'\bexcept\s+(?:"[^"]+"|\'[^\']+\')\s*(?:as\s+(\w+)\s*)?:')


def extract_regions(source: str, uri: str = "") -> list[Region]:
    """
    Extract all executable Draconic code regions from a source document.

    For .alias and .snippet files, this extracts <drac2> blocks and {{expr}} blocks.
    For .gvar and standalone .draconic files, the whole source is a single region.
    """
    if uri.endswith(".gvar") or uri.endswith(".draconic"):
        return [Region(code=_normalize(source), line_offset=0)]

    regions: list[Region] = []

    # Extract <drac2>...</drac2> multi-line blocks
    for match in _DRAC2_RE.finditer(source):
        inner = match.group(1)
        # Count newlines before the opening tag to get line_offset
        before = source[: match.start()]
        tag_line = before.count("\n")
        # The \n immediately after <drac2> is the first character of `inner`, so
        # Python line 1 of the region sits on the same file line as the tag itself.
        regions.append(Region(code=_normalize(inner), line_offset=tag_line))

    # Extract {{expr}} single-expression inline blocks
    for match in _DOUBLE_BRACE_RE.finditer(source):
        inner = match.group(1).strip()
        before = source[: match.start()]
        line = before.count("\n")
        col = len(before) - before.rfind("\n") - 1
        regions.append(Region(code=_normalize(inner), line_offset=line, col_offset=col + 2))

    # If no embedded blocks found, treat the whole source as a plain Draconic file
    if not regions:
        return [Region(code=_normalize(source), line_offset=0)]

    return regions


def _normalize(code: str) -> str:
    """Replace Draconic-specific syntax with valid Python equivalents for ast.parse()."""
    code = _ARG_PLACEHOLDER_RE.sub(lambda m: f"__arg_{m.group(1).lower()}__", code)
    code = _DRAC_EXCEPT_RE.sub(
        lambda m: f"except Exception as {m.group(1)}:" if m.group(1) else "except Exception:",
        code,
    )
    return code
