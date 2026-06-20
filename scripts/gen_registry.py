#!/usr/bin/env python3
"""
Drift-detection helper: fetch Avrae aliasing API source files and compare
their public surface against the Wyvern registry.

Usage:
    python scripts/gen_registry.py

The script prints a summary of:
  - Classes found in Avrae source with their method/property counts
  - Any names present in Avrae but absent from CLASS_REGISTRY
  - The current Avrae nightly HEAD commit SHA (for updating the pinned comment)

It does NOT auto-write the registry.  Review the diff and update registry.py
manually so every entry stays human-readable and intentional.

Requirements: only stdlib (urllib, ast, json).
"""
from __future__ import annotations

import ast
import json
import sys
import urllib.request
from typing import Any

AVRAE_RAW = "https://raw.githubusercontent.com/avrae/avrae/nightly/aliasing/api"
AVRAE_API = "https://api.github.com/repos/avrae/avrae/commits/nightly"

API_FILES = [
    "functions.py",
    "character.py",
    "combat.py",
    "context.py",
    "statblock.py",
]


def fetch(url: str) -> str:
    with urllib.request.urlopen(url, timeout=15) as r:
        return r.read().decode()


def get_head_sha() -> str:
    data: Any = json.loads(fetch(AVRAE_API))
    return data["sha"][:7]


def extract_classes(source: str) -> dict[str, dict[str, list[str]]]:
    """Parse source and return {class_name: {'methods': [...], 'properties': [...]}}."""
    tree = ast.parse(source)
    result: dict[str, dict[str, list[str]]] = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        methods: list[str] = []
        properties: list[str] = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name.startswith("_") and item.name not in ("__str__", "__repr__", "__iter__", "__len__", "__getitem__", "__contains__", "__int__"):
                    continue
                # Detect @property via decorator list
                is_prop = any(
                    (isinstance(d, ast.Name) and d.id == "property") or
                    (isinstance(d, ast.Attribute) and d.attr in ("getter", "setter")) or
                    (isinstance(d, ast.Name) and d.id == "cached_property")
                    for d in item.decorator_list
                )
                if is_prop:
                    properties.append(item.name)
                else:
                    methods.append(item.name)
        result[node.name] = {"methods": methods, "properties": properties}

    return result


def check_against_registry(avrae_classes: dict[str, dict[str, list[str]]]) -> None:
    # Import registry from the project root
    sys.path.insert(0, ".")
    try:
        from src.builtins import CLASS_REGISTRY
    except ImportError as e:
        print(f"[ERROR] Could not import CLASS_REGISTRY: {e}")
        print("        Run from the project root: python scripts/gen_registry.py")
        sys.exit(1)

    print("\n=== Avrae API surface vs Wyvern CLASS_REGISTRY ===\n")

    for cls_name, members in sorted(avrae_classes.items()):
        if cls_name.startswith("_"):
            continue
        in_registry = cls_name in CLASS_REGISTRY
        tag = "OK" if in_registry else "MISSING"
        print(f"  [{tag}] {cls_name}  ({len(members['methods'])} methods, {len(members['properties'])} props)")

        if in_registry:
            reg_cls = CLASS_REGISTRY[cls_name]
            reg_method_names = {m.name for m in reg_cls.methods}
            reg_prop_names = {p.name for p in reg_cls.properties}

            for m in members["methods"]:
                if m not in reg_method_names:
                    print(f"           [method MISSING] {m}")
            for p in members["properties"]:
                if p not in reg_prop_names:
                    print(f"           [prop   MISSING] {p}")

    print()


def main() -> None:
    print("Fetching Avrae nightly HEAD SHA...")
    try:
        sha = get_head_sha()
        print(f"  avrae/avrae@{sha}\n")
    except Exception as e:
        print(f"  [WARN] Could not fetch HEAD SHA: {e}\n")
        sha = "unknown"

    all_classes: dict[str, dict[str, list[str]]] = {}
    for fname in API_FILES:
        url = f"{AVRAE_RAW}/{fname}"
        print(f"Fetching {fname}...")
        try:
            source = fetch(url)
            classes = extract_classes(source)
            print(f"  Found classes: {', '.join(classes) or '(none)'}")
            all_classes.update(classes)
        except Exception as e:
            print(f"  [ERROR] {e}")

    check_against_registry(all_classes)
    print(f"Pinned comment to update in registry.py:")
    print(f"  # Last verified against avrae/avrae@{sha} (nightly, <date>)")


if __name__ == "__main__":
    main()
