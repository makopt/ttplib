"""Copy TTP JSON instances from a source directory into instances/.

Usage
-----
    python scripts/copy_instances.py [SOURCE_DIR]

SOURCE_DIR defaults to the sibling ``ttp_instances_json/`` folder relative
to the repo root.  Run from the repo root:

    python scripts/copy_instances.py
    python scripts/copy_instances.py /path/to/ttp_instances_json
"""

import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SRC = REPO_ROOT.parent / "ttp_instances_json"
DEST = REPO_ROOT / "instances"


def copy_instances(src: Path) -> None:
    if not src.exists():
        sys.exit(f"Source directory not found: {src}")

    total = 0
    for folder in sorted(src.iterdir()):
        if not folder.is_dir():
            continue
        dest_folder = DEST / folder.name
        dest_folder.mkdir(parents=True, exist_ok=True)
        for json_file in sorted(folder.glob("*.json")):
            dest_file = dest_folder / json_file.name
            if not dest_file.exists():
                shutil.copy2(json_file, dest_file)
                total += 1
        print(f"  {folder.name}: done")

    print(f"\nCopied {total} new files to {DEST}")


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SRC
    print(f"Source : {src}")
    print(f"Dest   : {DEST}\n")
    copy_instances(src)
