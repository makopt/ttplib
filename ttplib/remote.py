"""Remote loading of TTP instances from Hugging Face Hub."""

from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

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
# Corrected versions of the instances whose renting rate is 0.00 in the original files; the folder layout is the same.
CORRECTED_URL = (
    f"https://huggingface.co/datasets/{_HF_USER}/{_HF_REPO}"
    f"/resolve/{_HF_BRANCH}/corrected"
)

# Instances whose original file gives a renting rate of 0.00 (written with two decimals). Their corrected version has
# the renting rate recomputed with the rule of Polyakovskiy et al. (2014); everything else is identical.
CORRECTED = (
    "dsj1000_n999_bounded-strongly-corr_01",
    "dsj1000_n999_uncorr-similar-weights_01",
    "dsj1000_n999_uncorr-similar-weights_02",
    "dsj1000_n999_uncorr_01",
)

# The 60 categorized instances of El Yafrani and Ahiod (2016), used in most comparisons of TTP heuristics: twenty TSP
# instances (eil76 to pla33810) and three categories. A: 1 item per city, bounded strongly correlated, capacity level 01.
# B: 5 items per city, uncorrelated with similar weights, level 05. C: 10 items per city, uncorrelated, level 10.
CATEGORIZED: Dict[str, tuple] = {
    "A": (
        "eil76_n75_bounded-strongly-corr_01",
        "kroA100_n99_bounded-strongly-corr_01",
        "ch130_n129_bounded-strongly-corr_01",
        "u159_n158_bounded-strongly-corr_01",
        "a280_n279_bounded-strongly-corr_01",
        "u574_n573_bounded-strongly-corr_01",
        "u724_n723_bounded-strongly-corr_01",
        "dsj1000_n999_bounded-strongly-corr_01",
        "rl1304_n1303_bounded-strongly-corr_01",
        "fl1577_n1576_bounded-strongly-corr_01",
        "d2103_n2102_bounded-strongly-corr_01",
        "pcb3038_n3037_bounded-strongly-corr_01",
        "fnl4461_n4460_bounded-strongly-corr_01",
        "pla7397_n7396_bounded-strongly-corr_01",
        "rl11849_n11848_bounded-strongly-corr_01",
        "usa13509_n13508_bounded-strongly-corr_01",
        "brd14051_n14050_bounded-strongly-corr_01",
        "d15112_n15111_bounded-strongly-corr_01",
        "d18512_n18511_bounded-strongly-corr_01",
        "pla33810_n33809_bounded-strongly-corr_01",
    ),
    "B": (
        "eil76_n375_uncorr-similar-weights_05",
        "kroA100_n495_uncorr-similar-weights_05",
        "ch130_n645_uncorr-similar-weights_05",
        "u159_n790_uncorr-similar-weights_05",
        "a280_n1395_uncorr-similar-weights_05",
        "u574_n2865_uncorr-similar-weights_05",
        "u724_n3615_uncorr-similar-weights_05",
        "dsj1000_n4995_uncorr-similar-weights_05",
        "rl1304_n6515_uncorr-similar-weights_05",
        "fl1577_n7880_uncorr-similar-weights_05",
        "d2103_n10510_uncorr-similar-weights_05",
        "pcb3038_n15185_uncorr-similar-weights_05",
        "fnl4461_n22300_uncorr-similar-weights_05",
        "pla7397_n36980_uncorr-similar-weights_05",
        "rl11849_n59240_uncorr-similar-weights_05",
        "usa13509_n67540_uncorr-similar-weights_05",
        "brd14051_n70250_uncorr-similar-weights_05",
        "d15112_n75555_uncorr-similar-weights_05",
        "d18512_n92555_uncorr-similar-weights_05",
        "pla33810_n169045_uncorr-similar-weights_05",
    ),
    "C": (
        "eil76_n750_uncorr_10",
        "kroA100_n990_uncorr_10",
        "ch130_n1290_uncorr_10",
        "u159_n1580_uncorr_10",
        "a280_n2790_uncorr_10",
        "u574_n5730_uncorr_10",
        "u724_n7230_uncorr_10",
        "dsj1000_n9990_uncorr_10",
        "rl1304_n13030_uncorr_10",
        "fl1577_n15760_uncorr_10",
        "d2103_n21020_uncorr_10",
        "pcb3038_n30370_uncorr_10",
        "fnl4461_n44600_uncorr_10",
        "pla7397_n73960_uncorr_10",
        "rl11849_n118480_uncorr_10",
        "usa13509_n135080_uncorr_10",
        "brd14051_n140500_uncorr_10",
        "d15112_n151110_uncorr_10",
        "d18512_n185110_uncorr_10",
        "pla33810_n338090_uncorr_10",
    ),
}

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


def _disk_cache_path(name: str, corrected: bool = False) -> Path:
    cache_dir = Path(
        os.environ.get("TTPLIB_CACHE_DIR", Path.home() / ".cache" / "ttplib" / "instances")
    )
    if corrected:
        cache_dir = cache_dir / "corrected"           # folders of the originals all end with "-ttp", so no clash
    folder = _folder_from_name(name)
    return cache_dir / folder / (name + ".json")


def is_corrected(name: str) -> bool:
    """True if the instance has a corrected version (renting rate 0.00 in the original file)."""
    return name in CORRECTED


def load(name: str, cache: bool = True, corrected: bool = True) -> TTPInstance:
    """Load a TTP instance by name, fetching it from Hugging Face if needed.

    Parameters
    ----------
    name:
        Instance name without `.json` extension, e.g.
        ``"berlin52_n51_uncorr_01"``.
    cache:
        When True, cache downloaded files to ``~/.cache/ttplib/`` so
        subsequent calls skip the network request.
    corrected:
        When True (default), the four instances whose original file gives a
        renting rate of 0.00 are loaded in their corrected version (see
        ``ttplib.CORRECTED``). Use False to load the original 2014 files,
        for example to compare with published results. All other instances
        are the same in both cases.

    Returns
    -------
    TTPInstance
    """
    use_corrected = corrected and name in CORRECTED
    key = name + ("#corrected" if use_corrected else "")
    if key in _mem_cache:
        return _mem_cache[key]

    if cache:
        disk_path = _disk_cache_path(name, use_corrected)
        if disk_path.exists():
            with open(disk_path, "r") as f:
                data = json.load(f)
            inst = TTPInstance.from_dict(data)
            _mem_cache[key] = inst
            return inst

    folder = _folder_from_name(name)
    url = f"{CORRECTED_URL if use_corrected else BASE_URL}/{folder}/{name}.json"
    try:
        data = _fetch_json(url)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to fetch instance '{name}' from {url}.\n"
            f"Make sure the instance name is correct (see ttplib.list_instances()).\n"
            f"Original error: {exc}"
        ) from exc

    if cache:
        disk_path = _disk_cache_path(name, use_corrected)
        disk_path.parent.mkdir(parents=True, exist_ok=True)
        with open(disk_path, "w") as f:
            json.dump(data, f)

    inst = TTPInstance.from_dict(data)
    _mem_cache[key] = inst
    return inst


def iter_instances(
    names: Optional[List[str]] = None,
    corrected: bool = True,
    cache: bool = True,
    base: Optional[str] = None,
    item_type: Optional[str] = None,
    n_items: Optional[int] = None,
    category: Optional[str] = None,
) -> Iterator[Tuple[str, TTPInstance]]:
    """Yield ``(name, instance)`` for many instances, one at a time.

    Parameters
    ----------
    names:
        Instance names to load. If None, the names are those of
        ``list_instances(base, item_type, n_items, category)``, so that with
        no argument all 9,720 instances are loaded.
    corrected:
        As in ``load``: True (default) gives the corrected version of the
        four instances of ``ttplib.CORRECTED``, False gives the original files.
    cache:
        As in ``load``: keep a copy of each downloaded file on the computer.

    Each instance is removed from the memory of the session once the next one
    is requested (unless it was already loaded before), so that iterating over
    the whole benchmark does not fill the memory.
    """
    if names is None:
        names = list_instances(base=base, item_type=item_type, n_items=n_items, category=category)
    for name in names:
        key = name + ("#corrected" if corrected and name in CORRECTED else "")
        was_loaded = key in _mem_cache
        inst = load(name, cache=cache, corrected=corrected)
        try:
            yield name, inst
        finally:
            if not was_loaded:
                _mem_cache.pop(key, None)


def load_file(path) -> TTPInstance:
    """Load a TTP instance from a local JSON file."""
    with open(path, "r") as f:
        data = json.load(f)
    return TTPInstance.from_dict(data)


def list_instances(
    base: Optional[str] = None,
    item_type: Optional[str] = None,
    n_items: Optional[int] = None,
    category: Optional[str] = None,
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
    category:
        Keep only the 60 categorized instances (see ``ttplib.CATEGORIZED``): ``"A"``, ``"B"`` or ``"C"`` for one
        category (20 instances), or ``"all"`` for the 60.

    Returns
    -------
    List of matching instance names.
    """
    names = _get_catalog()

    if category is not None:
        key = category.upper()
        if key == "ALL":
            keep = {n for c in CATEGORIZED.values() for n in c}
        elif key in CATEGORIZED:
            keep = set(CATEGORIZED[key])
        else:
            raise ValueError(f"category must be 'A', 'B', 'C' or 'all', not {category!r}")
        names = [n for n in names if n in keep]
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
