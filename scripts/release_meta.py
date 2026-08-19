#!/usr/bin/env python3
"""Print the pyproject.toml facts the workflows need, as GITHUB_OUTPUT lines.

Keeps the SDK container tag and the ruff pin derived from the single version
source instead of duplicated into the workflow YAML.
"""

import tomllib
from pathlib import Path

project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]
version = project["version"]

facts = {
    "version": version,
    "sdk": ".".join(version.split(".")[:3]),
    "ruff": next(
        spec
        for spec in project["optional-dependencies"]["dev"]
        if spec.startswith("ruff")
    ),
}

print("\n".join(f"{key}={value}" for key, value in facts.items()))
