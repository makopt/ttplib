"""Upload all TTP instances to a Hugging Face dataset repository.

Prerequisites
-------------
    pip install huggingface_hub

Steps
-----
1. Create a *dataset* repo on https://huggingface.co/new-dataset
   (e.g. makopt/ttplib-data, public visibility).
2. Log in once:
       huggingface-cli login
3. Run this script from the repo root:
       python scripts/upload_to_huggingface.py [SOURCE_DIR]

   SOURCE_DIR defaults to the sibling ttp_instances_json/ folder.
   Files already present in the HF repo are skipped automatically.
"""

import sys
from pathlib import Path

try:
    from huggingface_hub import HfApi, RepoCard
except ImportError:
    sys.exit("Install huggingface_hub first:  pip install huggingface_hub")

REPO_ROOT  = Path(__file__).resolve().parent.parent
DEFAULT_SRC = REPO_ROOT.parent / "ttp_instances_json"

HF_REPO_ID  = "makopt/ttplib-data"   # change if your username/repo differs
REPO_TYPE   = "dataset"
BRANCH      = "main"


def upload(src: Path) -> None:
    if not src.exists():
        sys.exit(f"Source directory not found: {src}")

    api = HfApi()

    # Create the repo if it doesn't exist yet (safe to call if it exists)
    api.create_repo(repo_id=HF_REPO_ID, repo_type=REPO_TYPE, exist_ok=True)

    # Upload folder-by-folder so we can show progress per base problem
    total_uploaded = 0
    for folder in sorted(src.iterdir()):
        if not folder.is_dir():
            continue
        hf_path_in_repo = f"instances/{folder.name}"
        print(f"Uploading {folder.name} …", end=" ", flush=True)
        api.upload_folder(
            folder_path=str(folder),
            path_in_repo=hf_path_in_repo,
            repo_id=HF_REPO_ID,
            repo_type=REPO_TYPE,
            commit_message=f"Add {folder.name}",
        )
        count = sum(1 for f in folder.glob("*.json"))
        total_uploaded += count
        print(f"{count} files")

    print(f"\nDone. {total_uploaded} files uploaded to {HF_REPO_ID}")
    print(f"Dataset URL: https://huggingface.co/datasets/{HF_REPO_ID}")


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SRC
    print(f"Source : {src}")
    print(f"Target : hf://datasets/{HF_REPO_ID}\n")
    upload(src)
