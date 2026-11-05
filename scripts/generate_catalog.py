"""Regenerate ttplib/catalog.json from the instances/ directory.

Run this whenever you add or remove instance files:

    python scripts/generate_catalog.py
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTANCES_DIR = REPO_ROOT / "instances"
CATALOG_PATH = REPO_ROOT / "ttplib" / "catalog.json"


def generate() -> None:
    if not INSTANCES_DIR.exists():
        raise FileNotFoundError(f"instances/ directory not found: {INSTANCES_DIR}")

    names = []
    for folder in sorted(INSTANCES_DIR.iterdir()):
        if not folder.is_dir():
            continue
        for f in sorted(folder.glob("*.json")):
            names.append(f.stem)

    names.sort()

    with open(CATALOG_PATH, "w") as fh:
        json.dump(names, fh, separators=(",", ":"))

    print(f"Wrote {len(names)} instance names to {CATALOG_PATH}")


if __name__ == "__main__":
    generate()
