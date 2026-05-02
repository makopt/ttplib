"""Remote loading of TTP instances from Hugging Face Hub."""

from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

from .instance import TTPInstance

# Instances are hosted as a public Hugging Face dataset.
# Override via env vars or by setting ttplib.remote.BASE_URL directly.
_HF_USER   = os.environ.get("TTPLIB_HF_USER",   "makopt")
_HF_REPO   = os.environ.get("TTPLIB_HF_REPO",   "ttplib-data")
_HF_BRANCH = os.environ.get("TTPLIB_HF_BRANCH", "main")

BASE_URL = (
    f"https://huggingface.co/datasets/{_HF_USER}/{_HF_REPO}"
    f"/resolve/{_HF_BRANCH}/instances"
)

# In-memory session cache: name -> TTPInstance
_mem_cache: Dict[str, TTPInstance] = {}

# Catalog (loaded lazily)
_catalog: Optional[List[str]] = None


def _get_catalog() -> List[str]:
    global _catalog
    if _catalog is None:
        catalog_path = Path(__file__).parent / "catalog.json"
        with open(catalog_path, "r") as f:
            _catalog = json.load(f)
    return _catalog


def _folder_from_name(name: str) -> str:
    """Derive the instances/ subfolder from the instance name."""
    m = re.match(r"^(.+?)_n\d", name)
    base = m.group(1) if m else name.split("_")[0]
    return base + "-ttp"


def _fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _disk_cache_path(name: str) -> Path:
    cache_dir = Path(
        os.environ.get("TTPLIB_CACHE_DIR", Path.home() / ".cache" / "ttplib" / "instances")
    )
    folder = _folder_from_name(name)
    return cache_dir / folder / (name + ".json")


def load(name: str, cache: bool = True) -> TTPInstance:
    """Load a TTP instance by name, fetching from GitHub if needed.

    Parameters
    ----------
    name:
        Instance name without `.json` extension, e.g.
        ``"berlin52_n51_uncorr_01"``.
    cache:
        When True, cache downloaded files to ``~/.cache/ttplib/`` so
        subsequent calls skip the network request.

    Returns
    -------
    TTPInstance
    """
    if name in _mem_cache:
        return _mem_cache[name]

    if cache:
        disk_path = _disk_cache_path(name)
        if disk_path.exists():
            with open(disk_path, "r") as f:
                data = json.load(f)
            inst = TTPInstance.from_dict(data)
            _mem_cache[name] = inst
            return inst


    folder = _folder_from_name(name)
    url = f"{BASE_URL}/{folder}/{name}.json"
    try:
        data = _fetch_json(url)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to fetch instance '{name}' from {url}.\n"
            f"Make sure the instance name is correct (see ttplib.list_instances()).\n"
            f"Original error: {exc}"
        ) from exc

    if cache:
        disk_path = _disk_cache_path(name)
        disk_path.parent.mkdir(parents=True, exist_ok=True)
        with open(disk_path, "w") as f:
            json.dump(data, f)

    inst = TTPInstance.from_dict(data)
    _mem_cache[name] = inst
    return inst


def load_file(path) -> TTPInstance:
    """Load a TTP instance from a local JSON file."""
    with open(path, "r") as f:
        data = json.load(f)
    return TTPInstance.from_dict(data)


def list_instances(
    base: Optional[str] = None,
    item_type: Optional[str] = None,
    n_items: Optional[int] = None,
) -> List[str]:
    """Return the list of all available instance names.

    Parameters
    ----------
    base:
        Filter by base TSP problem name, e.g. ``"berlin52"``.
    item_type:
        Filter by correlation type: ``"uncorr"``,
        ``"uncorr-similar-weights"``, or ``"bounded-strongly-corr"``.
    n_items:
        Filter by exact item count (the ``n<X>`` part of the name).

    Returns
    -------
    List of matching instance names.
    """
    names = _get_catalog()

    if base is not None:
        names = [n for n in names if n.startswith(base + "_")]
    if item_type is not None:
        names = [n for n in names if f"_{item_type}_" in n]
    if n_items is not None:
        prefix = f"_n{n_items}_"
        names = [n for n in names if prefix in n]

    return names


def list_bases() -> List[str]:
    """Return the distinct base TSP problem names (e.g. ``["berlin52", ...]``)."""
    seen = []
    for name in _get_catalog():
        m = re.match(r"^(.+?)_n\d", name)
        base = m.group(1) if m else name.split("_")[0]
        if base not in seen:
            seen.append(base)
    return seen


def clear_cache(disk: bool = False) -> None:
    """Clear the in-memory cache (and optionally the disk cache)."""
    _mem_cache.clear()
    if disk:
        import shutil
        cache_dir = Path(
            os.environ.get("TTPLIB_CACHE_DIR", Path.home() / ".cache" / "ttplib")
        )
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
