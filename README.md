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
<base>_n<items>_<type>_<seed>
```

| Part | Meaning | Examples |
|------|---------|---------|
| `<base>` | TSP benchmark name | `berlin52`, `kroA100`, `a280` |
| `n<items>` | Number of items | `n51`, `n153`, `n255`, `n510` |
| `<type>` | Item weight correlation | `uncorr`, `uncorr-similar-weights`, `bounded-strongly-corr` |
| `<seed>` | Instance seed (01–10) | `01` … `10` |

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

## TTPInstance API

| Attribute / Method | Type | Description |
|--------------------|------|-------------|
| `name` | `str` | Instance name |
| `dimension` | `int` | Number of cities |
| `num_items` | `int` | Number of items |
| `capacity` | `int` | Knapsack capacity |
| `min_speed` / `max_speed` | `float` | Thief speed bounds |
| `renting_ratio` | `float` | Cost per unit time |
| `knapsack_type` | `str` | Correlation type |
| `edge_weight_type` | `str` | Distance formula |
| `graph` | `nx.Graph` | NetworkX complete graph (edge weight = distance) |
| `items` | `dict[int, Item]` | All items indexed by global item id |
| `get_distance(u, v)` | `float` | Distance between cities `u` and `v` |
| `get_distance_matrix()` | `np.ndarray` | Full n×n distance matrix |
| `get_items_at_node(i)` | `list[Item]` | Items available at city `i` |
| `get_items_by_city()` | `dict` | Items grouped by city index |
| `get_item_parameters_by_city()` | `tuple` | `(p_ik, w_ik, m_i)` tensors for solvers |
| `calculate_tour_distance(tour)` | `float` | Total tour length |
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
| Small (≤200 cities) | berlin52, eil51, eil76, … | ~3 600 |
| Medium (200–1 000) | lin318, rat575, u724, … | ~3 600 |
| Large (>1 000) | d1291, nrw1379, pla7397, … | ~2 520 |
| **Total** | **81** | **9 720** |

Each base problem has instances for 4 item-count multipliers, 3 correlation types, and 10 random seeds.

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

> Polyakovskiy, S., Bonyadi, M. R., Wagner, M., Vinglas, L., & Neumann, F. (2014).
> **A comprehensive benchmark set and heuristics for the traveling thief problem.**
> *Proceedings of the 2014 Annual Conference on Genetic and Evolutionary Computation (GECCO '14).*
> ACM. <https://dl.acm.org/doi/abs/10.1145/2576768.2598249>

The original instances in text format are available at:
<https://cs.adelaide.edu.au/~optlog/CEC2014COMP_InstancesNew/>

---

## License

MIT
