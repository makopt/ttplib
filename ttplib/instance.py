"""TTPInstance and Item data structures."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import networkx as nx
import numpy as np


@dataclass
class Item:
    index: int
    profit: float
    weight: int
    assigned_node: int

    @property
    def profit_weight_ratio(self) -> float:
        return self.profit / self.weight if self.weight > 0 else 0.0


@dataclass
class TTPInstance:
    """A TTP instance. Coordinates are kept in a NumPy array and distances are computed when they are needed, so that
    loading an instance takes memory linear in its number of cities, even for pla85900. The complete NetworkX graph of
    earlier versions is still available as ``graph``, but it is built only on first access (n(n-1)/2 edges)."""
    name: str
    knapsack_type: str
    dimension: int
    num_items: int
    capacity: int
    min_speed: float
    max_speed: float
    renting_ratio: float
    edge_weight_type: str
    items: Dict[int, Item] = field(default_factory=dict)
    node_ids: List[int] = field(default_factory=list, repr=False)
    coordinates: np.ndarray = field(default_factory=lambda: np.zeros((0, 2)), repr=False)
    _row: Dict[int, int] = field(default_factory=dict, repr=False)
    _graph: Optional[nx.Graph] = field(default=None, repr=False)

    def __post_init__(self):
        if not isinstance(self.items, dict):
            self.items = {}

    @staticmethod
    def _distance(pos1: Tuple[float, float], pos2: Tuple[float, float], edge_type: str) -> float:
        dx, dy = pos1[0] - pos2[0], pos1[1] - pos2[1]
        d = math.sqrt(dx * dx + dy * dy)
        if edge_type == "CEIL_2D":
            return math.ceil(d)
        if edge_type == "EUC_2D":
            return round(d)
        return d

    def _round(self, d: np.ndarray) -> np.ndarray:
        if self.edge_weight_type == "CEIL_2D":
            return np.ceil(d)
        if self.edge_weight_type == "EUC_2D":
            return np.round(d)
        return d

    def build_graph(self, nodes_data: List[Dict]) -> None:
        """Store the cities. Kept under its old name; no edge is created here any more."""
        self.node_ids = [int(nd["index"]) for nd in nodes_data]
        self.coordinates = np.array([(nd["x"], nd["y"]) for nd in nodes_data], dtype=float).reshape(-1, 2)
        self._row = {u: i for i, u in enumerate(self.node_ids)}
        self._graph = None

    def position(self, u: int) -> Tuple[float, float]:
        x, y = self.coordinates[self._row[u]]
        return float(x), float(y)

    @property
    def graph(self) -> nx.Graph:
        """Complete NetworkX graph with edge weight = distance, built on first access. It has n(n-1)/2 edges, so avoid
        it on large instances and use get_distance or get_distance_matrix instead."""
        if self._graph is None:
            g = nx.Graph()
            for u, (x, y) in zip(self.node_ids, self.coordinates):
                g.add_node(u, pos=(float(x), float(y)), x=float(x), y=float(y))
            for i, u in enumerate(self.node_ids):
                for v in self.node_ids[i + 1:]:
                    g.add_edge(u, v, weight=self.get_distance(u, v))
            self._graph = g
        return self._graph

    def add_items(self, items_data: List[Dict]) -> None:
        for d in items_data:
            item = Item(index=d["index"], profit=d["profit"],
                        weight=d["weight"], assigned_node=d["assigned_node"])
            self.items[item.index] = item

    def get_items_at_node(self, node_id: int) -> List[Item]:
        return [it for it in self.items.values() if it.assigned_node == node_id]

    def get_items_by_city(self) -> Dict[int, List[Item]]:
        result: Dict[int, List[Item]] = {i: [] for i in range(1, self.dimension + 1)}
        for item in self.items.values():
            result[item.assigned_node].append(item)
        return result

    def get_item_parameters_by_city(self) -> Tuple[Dict, Dict, Dict]:
        by_city = self.get_items_by_city()
        p_ik, w_ik, m_i = {}, {}, {}
        for city in range(1, self.dimension + 1):
            city_items = sorted(by_city[city], key=lambda x: x.index)
            m_i[city] = len(city_items)
            p_ik[city] = [it.profit for it in city_items]
            w_ik[city] = [it.weight for it in city_items]
        return p_ik, w_ik, m_i

    def get_distance(self, u: int, v: int) -> float:
        """Distance between cities u and v (city indices as in the instance file)."""
        if u == v:
            return 0
        return self._distance(self.coordinates[self._row[u]], self.coordinates[self._row[v]], self.edge_weight_type)

    def get_distance_matrix(self) -> np.ndarray:
        """Full n x n distance matrix, rows and columns in increasing city index. It needs 8 n^2 bytes (about 59 GB for
        pla85900), so use it only on small and medium instances."""
        order = np.argsort(self.node_ids)
        c = self.coordinates[order]
        mat = np.empty((len(c), len(c)))
        for i in range(len(c)):
            mat[i] = self._round(np.hypot(c[:, 0] - c[i, 0], c[:, 1] - c[i, 1]))
        np.fill_diagonal(mat, 0.0)
        return mat

    def calculate_tour_distance(self, tour: Sequence[int]) -> float:
        """Length of the closed tour (a sequence of city indices)."""
        rows = np.array([self._row[u] for u in tour])
        c = self.coordinates[rows]
        d = self._round(np.hypot(*(c - np.roll(c, -1, axis=0)).T))
        return float(d.sum())

    @classmethod
    def from_dict(cls, data: Dict) -> "TTPInstance":
        inst = cls(
            name=data["problem_name"],
            knapsack_type=data["knapsack_data_type"],
            dimension=data["dimension"],
            num_items=data["number_of_items"],
            capacity=data["capacity_of_knapsack"],
            min_speed=data["min_speed"],
            max_speed=data["max_speed"],
            renting_ratio=data["renting_ratio"],
            edge_weight_type=data["edge_weight_type"],
        )
        inst.build_graph(data["nodes"])
        inst.add_items(data["items"])
        return inst

    def summary(self) -> Dict:
        return {
            "name": self.name,
            "dimension": self.dimension,
            "num_items": self.num_items,
            "capacity": self.capacity,
            "avg_items_per_city": self.num_items / self.dimension,
            "total_weight": sum(it.weight for it in self.items.values()),
            "total_profit": sum(it.profit for it in self.items.values()),
        }

    def __str__(self) -> str:
        return (
            f"TTP Instance: {self.name}\n"
            f"  Type: {self.knapsack_type}\n"
            f"  Cities: {self.dimension}, Items: {self.num_items}\n"
            f"  Capacity: {self.capacity}\n"
            f"  Speed: [{self.min_speed}, {self.max_speed}]\n"
            f"  Renting ratio: {self.renting_ratio}\n"
            f"  Edge type: {self.edge_weight_type}"
        )
