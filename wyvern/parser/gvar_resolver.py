"""
Resolves gvar UUIDs to their parsed symbol definitions by searching the workspace
for matching {uuid}.gvar files.
"""
from __future__ import annotations

import os
from functools import lru_cache

from wyvern.parser.analysis import DefinitionInfo, extract_top_level_definitions

# Gvars authored by other alias coders and pulled in only via using() are kept
# in this directory. They're fully resolved for completions/hover like any
# other gvar, but diagnostics are suppressed when one is opened directly
# since it isn't maintained in this project.
USINGS_DIR_PARTS = (".wyvern", "usings")


def is_usings_path(path: str) -> bool:
    """Return True if `path` lives inside a `.wyvern/usings/` directory."""
    parts = path.replace("\\", "/").split("/")
    for i in range(len(parts) - len(USINGS_DIR_PARTS) + 1):
        if tuple(parts[i : i + len(USINGS_DIR_PARTS)]) == USINGS_DIR_PARTS:
            return True
    return False


def resolve_gvar_definitions(uuid: str, workspace_paths: list[str]) -> dict[str, DefinitionInfo]:
    """Return the top-level symbol definitions from the gvar file matching `uuid`.

    Searches `workspace_paths` recursively for a file named `{uuid}.gvar`.
    Returns an empty dict if not found or if the file cannot be parsed.
    """
    filepath = _find_gvar_file(uuid, tuple(workspace_paths))
    if not filepath:
        return {}
    return _parse_gvar(filepath)


def _find_gvar_file(uuid: str, search_paths: tuple[str, ...]) -> str | None:
    filename = f"{uuid}.gvar"
    for root_path in search_paths:
        for dirpath, _, files in os.walk(root_path):
            if filename in files:
                return os.path.join(dirpath, filename)
    return None


@lru_cache(maxsize=64)
def _parse_gvar(filepath: str) -> dict[str, DefinitionInfo]:
    try:
        with open(filepath, encoding="utf-8") as f:
            source = f.read()
        return extract_top_level_definitions(source, filepath)
    except OSError:
        return {}
