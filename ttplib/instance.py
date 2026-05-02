"""TTPInstance and Item data structures."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

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
    name: str
    knapsack_type: str
    dimension: int
    num_items: int
    capacity: int
    min_speed: float
    max_speed: float
    renting_ratio: float
    edge_weight_type: str
    graph: nx.Graph = field(default_factory=nx.Graph)
    items: Dict[int, Item] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.graph, nx.Graph):
            self.graph = nx.Graph()
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

    def build_graph(self, nodes_data: List[Dict]) -> None:
        for node in nodes_data:
            self.graph.add_node(node["index"], pos=(node["x"], node["y"]),
                                x=node["x"], y=node["y"])
        nodes = list(self.graph.nodes())
        for i, u in enumerate(nodes):
            for v in nodes[i + 1:]:
                pu = self.graph.nodes[u]["pos"]
                pv = self.graph.nodes[v]["pos"]
                self.graph.add_edge(u, v, weight=self._distance(pu, pv, self.edge_weight_type))

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
        return self.graph[u][v]["weight"]

    def get_distance_matrix(self) -> np.ndarray:
        nodes = sorted(self.graph.nodes())
        n = len(nodes)
        mat = np.zeros((n, n))
        for i, u in enumerate(nodes):
            for j, v in enumerate(nodes):
                if i != j:
                    mat[i, j] = self.graph[u][v]["weight"]
        return mat

    def calculate_tour_distance(self, tour: List[int]) -> float:
        total = sum(self.get_distance(tour[i], tour[i + 1]) for i in range(len(tour) - 1))
        return total + self.get_distance(tour[-1], tour[0])

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
