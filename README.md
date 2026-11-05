# ttplib

A Python library for the **Travelling Thief Problem (TTP)** that lets you load any of the **9 720 benchmark instances** directly from the network — no local files required.

Instance data is hosted on [Hugging Face Hub](https://huggingface.co/datasets/makopt/ttplib-data) (17 GB, free public dataset).  
Inspired by [tsplib95](https://github.com/rhgrant10/tsplib95).

---

## Installation

```bash
pip install ttplib
```

Or install from source:

```bash
git clone https://github.com/makopt/ttplib.git
cd ttplib
pip install -e .
```

---

## Quick start

```python
import ttplib

# Load an instance by name — fetched from Hugging Face on first call, cached automatically
problem = ttplib.load("berlin52_n51_uncorr_01")

print(problem)
# TTP Instance: berlin52-TTP
#   Type: uncorrelated
#   Cities: 52, Items: 51
#   Capacity: 2245
#   Speed: [0.1, 1.0]
#   Renting ratio: 0.53
#   Edge type: CEIL_2D

# Access instance fields
print(problem.dimension)      # 52
print(problem.capacity)       # 2245
print(problem.renting_ratio)  # 0.53

# Distance between two cities
d = problem.get_distance(1, 2)

# All items at city 5
items = problem.get_items_at_node(5)

# Full distance matrix (numpy)
D = problem.get_distance_matrix()

# Summary statistics
print(problem.summary())
```

---

## Browsing available instances

```python
import ttplib

# All 9 720 instance names
all_names = ttplib.list_instances()

# Filter by base TSP problem
berlin = ttplib.list_instances(base="berlin52")

# Filter by correlation type
uncorr  = ttplib.list_instances(item_type="uncorr")
similar = ttplib.list_instances(item_type="uncorr-similar-weights")
corr    = ttplib.list_instances(item_type="bounded-strongly-corr")

# Filter by number of items
small = ttplib.list_instances(base="berlin52", n_items=51)

# Combine filters
subset = ttplib.list_instances(base="kroA100", item_type="uncorr", n_items=99)

# List all base TSP problem names
bases = ttplib.list_bases()
# ['a280', 'berlin52', 'bier127', ..., 'vm1748']
```

### Naming convention

Each instance name follows the pattern:

```
<base>_n<items>_<type>_<level>
```

| Part | Meaning | Examples |
|------|---------|---------|
| `<base>` | TSP benchmark name | `berlin52`, `kroA100`, `a280` |
| `n<items>` | Number of items | `n51`, `n153`, `n255`, `n510` |
| `<type>` | Item weight correlation | `uncorr`, `uncorr-similar-weights`, `bounded-strongly-corr` |
| `<level>` | Capacity level k (01–10): the capacity is k/11 of the total weight of the items, rounded down | `01` … `10` |

---

## Caching

Downloaded instances are cached to `~/.cache/ttplib/` by default so subsequent loads are instant.

```python
# Disable caching (always fetch from network)
problem = ttplib.load("berlin52_n51_uncorr_01", cache=False)

# Change the cache directory
import os
os.environ["TTPLIB_CACHE_DIR"] = "/tmp/my_ttplib_cache"

# Clear the in-memory session cache only
ttplib.clear_cache()

# Clear both memory and disk caches
ttplib.clear_cache(disk=True)
```

---

## Loading from a local file

```python
problem = ttplib.load_file("path/to/my_instance.json")
```

---

## Configuration

| Environment variable | Default | Purpose |
|----------------------|---------|---------|
| `TTPLIB_HF_USER` | `makopt` | Hugging Face username |
| `TTPLIB_HF_REPO` | `ttplib-data` | Hugging Face dataset repo name |
| `TTPLIB_HF_BRANCH` | `main` | Branch / revision |
| `TTPLIB_CACHE_DIR` | `~/.cache/ttplib/instances` | Local disk cache directory |

You can also override the base URL at runtime:

```python
import ttplib.remote as r
r.BASE_URL = "https://huggingface.co/datasets/myuser/ttplib-data/resolve/main/instances"
```

---

## Library functions

| Function or constant | Returns | Description |
|---|---|---|
| `load(name, cache=True, corrected=True)` | `TTPInstance` | Loads the instance `name`. The file is downloaded from the dataset at its first use and a copy is kept on the computer (`cache=False`: no copy). For the four instances with a renting rate of 0.00, the corrected version is returned unless `corrected=False`. |
| `load_file(path)` | `TTPInstance` | Loads an instance from a JSON file on the computer. |
| `list_instances(base=None, item_type=None, n_items=None, category=None)` | `list[str]` | Names of the instances, all 9 720 by default. Filters: `base` (TSP instance, e.g. `"dsj1000"`), `item_type` (`"bounded-strongly-corr"`, `"uncorr-similar-weights"` or `"uncorr"`), `n_items` (number of items, e.g. `999`), `category` (`"A"`, `"B"`, `"C"` or `"all"` for the 60 categorized instances). Filters can be combined. |
| `list_bases()` | `list[str]` | Names of the 81 TSP instances. |
| `is_corrected(name)` | `bool` | True for the four instances served in a corrected version. |
| `clear_cache(disk=False)` | `None` | Empties the cache of the session; with `disk=True`, also deletes the copies kept on the computer. |
| `CORRECTED` | `tuple[str]` | Names of the four corrected instances. |
| `CATEGORIZED` | `dict` | The 60 categorized instances, as `{"A": (...), "B": (...), "C": (...)}`. |
| `BASE_URL`, `CORRECTED_URL` | `str` | Addresses of the folders `instances/` and `corrected/` of the dataset. |

In the library, as in the files, cities and items are numbered from 1, and city 1 is the city where the tour starts
and ends.

---

## TTPInstance API

| Attribute / Method | Type | Description |
|--------------------|------|-------------|
| `name` | `str` | Name in the file header, e.g. `dsj1000-TTP` (the name of the TSP instance, not the full instance name) |
| `dimension` | `int` | Number of cities |
| `num_items` | `int` | Number of items |
| `capacity` | `int` | Knapsack capacity |
| `min_speed` / `max_speed` | `float` | Thief speed bounds |
| `renting_ratio` | `float` | Cost per unit time |
| `knapsack_type` | `str` | Correlation type |
| `edge_weight_type` | `str` | Distance formula |
| `coordinates` | `np.ndarray` | n×2 array of city coordinates, in the order of `node_ids` |
| `node_ids` | `list[int]` | City indices as in the instance file |
| `graph` | `nx.Graph` | NetworkX complete graph (edge weight = distance), built only on first access; it has n(n−1)/2 edges, so avoid it on large instances |
| `items` | `dict[int, Item]` | All items indexed by global item id |
| `get_distance(u, v)` | `float` | Distance between cities `u` and `v` |
| `get_distance_matrix()` | `np.ndarray` | Full n×n distance matrix (8n² bytes; for small and medium instances) |
| `position(u)` | `tuple` | Coordinates `(x, y)` of city `u` |
| `get_items_at_node(i)` | `list[Item]` | Items available at city `i` |
| `get_items_by_city()` | `dict` | Items grouped by city index |
| `get_item_parameters_by_city()` | `tuple` | Three dicts by city: profits `p_ik`, weights `w_ik` and number of items `m_i` |
| `calculate_tour_distance(tour)` | `float` | Length of the closed tour `tour` (a list of cities, back to the first one) |
| `summary()` | `dict` | Quick statistics |

### Item fields

| Field | Type | Description |
|-------|------|-------------|
| `index` | `int` | Global item index |
| `profit` | `float` | Item profit |
| `weight` | `int` | Item weight |
| `assigned_node` | `int` | City where the item is available |
| `profit_weight_ratio` | `float` | `profit / weight` |

---

## Instance coverage

| Group | Base problems | Instances |
|-------|--------------|-----------|
| Small (≤200 cities) | berlin52, eil51, eil76, … | 3 480 |
| Medium (201–1 000) | lin318, rat575, u724, … | 2 400 |
| Large (>1 000) | d1291, nrw1379, pla7397, … | 3 840 |
| **Total** | **81** | **9 720** |

Each base problem has instances for 4 numbers of items per city (1, 3, 5, 10), 3 types of knapsack and 10 capacity
levels, which gives 120 instances per base problem.

---

## The 60 categorized instances

Most comparisons of TTP heuristics use the 60 categorized instances of El Yafrani and Ahiod (2016): twenty TSP
instances, from eil76 to pla33810, and three categories on each of them.

| Category | Items per city | Type of knapsack | Capacity level |
|---|---|---|---|
| A | 1 | bounded strongly correlated | 01 |
| B | 5 | uncorrelated, similar weights | 05 |
| C | 10 | uncorrelated | 10 |

```python
import ttplib

ttplib.list_instances(category="all")   # the 60 names
ttplib.list_instances(category="A")     # the 20 instances of category A
ttplib.CATEGORIZED                      # {"A": (...), "B": (...), "C": (...)}

for name in ttplib.list_instances(category="all"):
    inst = ttplib.load(name)
```

The instance of category A built on dsj1000 is one of the four instances with a renting rate of 0.00 (see below), so
`ttplib.load` serves its corrected version by default.

---

## Corrected instances

In the original files, the renting rate is written with two decimals. For four instances built on dsj1000 with 999
items, this gives a renting rate of 0.00, so travel time costs nothing and the instance is a pure knapsack problem:

| Instance | Renting rate in the original file | Corrected renting rate |
|---|---|---|
| `dsj1000_n999_bounded-strongly-corr_01` | 0.00 | 0.0028417669143102806 |
| `dsj1000_n999_uncorr-similar-weights_01` | 0.00 | 0.00187512008103438 |
| `dsj1000_n999_uncorr-similar-weights_02` | 0.00 | 0.0036829751838066 |
| `dsj1000_n999_uncorr_01` | 0.00 | 0.0034836798642203476 |

The corrected rate is computed with the rule of the original generator (optimal knapsack profit divided by the travel
time of a reference solution). The stored value is the double-precision value of this ratio, and the published
reference solution has an objective of zero up to floating-point rounding (below 1e-8). These rates are proposed by the
authors of `ttplib`; they are not an official release of the benchmark authors. Only the renting rate differs from the
original file. `ttplib.load` serves the corrected version by default:

```python
import ttplib

ttplib.load("dsj1000_n999_uncorr_01").renting_ratio                   # 0.0034836798642203476
ttplib.load("dsj1000_n999_uncorr_01", corrected=False).renting_ratio  # 0.0, the original 2014 file
ttplib.CORRECTED                                                      # the four names
ttplib.is_corrected("dsj1000_n999_uncorr_01")                         # True
```

Use `corrected=False` to compare with results published on the original files. The corrected files are stored in the
`corrected/` folder of the Hugging Face dataset; the originals in `instances/` are unchanged.

## Memory use

An instance stores its city coordinates in a NumPy array and computes distances on demand.
Loading pla85900 takes a few seconds and less than 200 MB. The complete NetworkX graph `graph` is available, but it is built only when it is first used. It has n(n−1)/2 edges (3.7 billion for pla85900), so use
`get_distance` or `calculate_tour_distance` on large instances.

---

## For maintainers: uploading the dataset

The `instances/` folder is **not** committed to this GitHub repo (it's in `.gitignore`).  
The data lives on Hugging Face: [makopt/ttplib-data](https://huggingface.co/datasets/makopt/ttplib-data).

To upload or re-upload all instances:

```bash
pip install huggingface_hub
huggingface-cli login          # one-time authentication
python scripts/upload_to_huggingface.py
```

To add new instances after uploading:

1. Add new JSON files under `instances/<base>-ttp/`.
2. Regenerate the catalog (commits to the **GitHub** repo):
   ```bash
   python scripts/generate_catalog.py
   ```
3. Re-run the upload script to push only the new files.

---

## Attribution

The benchmark instances were originally generated by:

> Polyakovskiy, S., Bonyadi, M. R., Wagner, M., Michalewicz, Z., & Neumann, F. (2014).
> **A comprehensive benchmark set and heuristics for the traveling thief problem.**
> *Proceedings of the 2014 Annual Conference on Genetic and Evolutionary Computation (GECCO '14).*
> ACM, pp. 477–484. <https://doi.org/10.1145/2576768.2598249>

The original instances in text format are available at:
<https://cs.adelaide.edu.au/~optlog/CEC2014COMP_InstancesNew/>

---

## Changes

- **0.2.1**: distances computed on demand (pla85900 loads in a few seconds with less than 200 MB); the complete graph
  `graph` is built only when it is used; the 60 categorized instances (`CATEGORIZED`, `list_instances(category=...)`).
- **0.2.0**: corrected versions of the four instances with a renting rate of 0.00, served by default (`corrected`,
  `CORRECTED`, `is_corrected`).

---

## License

MIT
