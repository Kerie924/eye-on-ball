"""YAML load that works without a C compiler (Python 3.15 / Windows court PCs)."""

from __future__ import annotations

from typing import Any, TextIO


def safe_load(stream: TextIO | str) -> Any:
    """Load YAML using PyYAML if present, else ruamel.yaml (pure Python)."""
    try:
        import yaml  # PyYAML

        return yaml.safe_load(stream)
    except ImportError:
        pass

    try:
        from ruamel.yaml import YAML

        loader = YAML(typ="safe", pure=True)
        return loader.load(stream)
    except ImportError as exc:
        raise ImportError(
            "No YAML library installed. On Windows install: pip install ruamel.yaml\n"
            "On Linux install: pip install pyyaml"
        ) from exc
