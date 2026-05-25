"""Test suite for the ttplib API.

Run all tests:
    python -m pytest test_ttplib.py -v

Skip tests that require network access:
    TTPLIB_SKIP_NETWORK=1 python -m pytest test_ttplib.py -v
"""

import json
import os
import tempfile
import unittest

import numpy as np

import ttplib
from ttplib.remote import _mem_cache

SKIP_NETWORK = os.environ.get("TTPLIB_SKIP_NETWORK", "0") == "1"

# Small instance (52 cities, 51 items) used across network tests.
TEST_INSTANCE = "berlin52_n51_uncorr_01"

# Minimal hand-crafted 3-city instance for offline tests.
_MINIMAL = {
    "problem_name": "test_n2_uncorr_01",
    "knapsack_data_type": "uncorr",
    "dimension": 3,
    "number_of_items": 2,
    "capacity_of_knapsack": 100,
    "min_speed": 0.1,
    "max_speed": 1.0,
    "renting_ratio": 1.0,
    "edge_weight_type": "EUC_2D",
    "nodes": [
        {"index": 1, "x": 0.0, "y": 0.0},
        {"index": 2, "x": 3.0, "y": 4.0},
        {"index": 3, "x": 6.0, "y": 0.0},
    ],
    "items": [
        {"index": 1, "profit": 10.0, "weight": 5, "assigned_node": 2},
        {"index": 2, "profit": 20.0, "weight": 10, "assigned_node": 3},
    ],
}
# Distances in _MINIMAL (EUC_2D = round):
#   1→2: round(sqrt(9+16)) = 5
#   2→3: round(sqrt(9+16)) = 5
#   1→3: round(sqrt(36))   = 6


def _load_minimal() -> ttplib.TTPInstance:
    return ttplib.TTPInstance.from_dict(_MINIMAL)


# ===========================================================================
# Catalog tests — no network required
# ===========================================================================

class TestListInstances(unittest.TestCase):
    def test_total_count(self):
        self.assertEqual(len(ttplib.list_instances()), 9720)

    def test_returns_list_of_strings(self):
        names = ttplib.list_instances()
        self.assertIsInstance(names, list)
        self.assertTrue(all(isinstance(n, str) for n in names))

    def test_filter_by_base(self):
        names = ttplib.list_instances(base="berlin52")
        self.assertGreater(len(names), 0)
        self.assertTrue(all(n.startswith("berlin52_") for n in names))

    def test_filter_by_item_type_uncorr(self):
        names = ttplib.list_instances(item_type="uncorr")
        self.assertGreater(len(names), 0)
        self.assertTrue(all("_uncorr_" in n for n in names))

    def test_filter_by_item_type_similar_weights(self):
        names = ttplib.list_instances(item_type="uncorr-similar-weights")
        self.assertGreater(len(names), 0)
        self.assertTrue(all("_uncorr-similar-weights_" in n for n in names))

    def test_filter_by_item_type_bounded(self):
        names = ttplib.list_instances(item_type="bounded-strongly-corr")
        self.assertGreater(len(names), 0)
        self.assertTrue(all("_bounded-strongly-corr_" in n for n in names))

    def test_filter_by_n_items(self):
        names = ttplib.list_instances(n_items=51)
        self.assertGreater(len(names), 0)
        self.assertTrue(all("_n51_" in n for n in names))

    def test_combined_filters_give_10_seeds(self):
        # berlin52, n51, uncorr → exactly 10 seeds (01–10)
        names = ttplib.list_instances(base="berlin52", item_type="uncorr", n_items=51)
        self.assertEqual(len(names), 10)
        self.assertTrue(all(n.startswith("berlin52_n51_uncorr_") for n in names))

    def test_unknown_base_returns_empty(self):
        self.assertEqual(ttplib.list_instances(base="does_not_exist_xyz"), [])

    def test_unknown_type_returns_empty(self):
        self.assertEqual(ttplib.list_instances(item_type="no-such-type"), [])

    def test_known_instance_in_catalog(self):
        self.assertIn(TEST_INSTANCE, ttplib.list_instances())


class TestListBases(unittest.TestCase):
    def test_count(self):
        self.assertEqual(len(ttplib.list_bases()), 81)

    def test_no_duplicates(self):
        bases = ttplib.list_bases()
        self.assertEqual(len(bases), len(set(bases)))

    def test_contains_known_bases(self):
        bases = ttplib.list_bases()
        for name in ("berlin52", "kroA100", "a280"):
            self.assertIn(name, bases)

    def test_toy_bases_absent(self):
        bases = ttplib.list_bases()
        for toy in ("toy-10", "toy-20", "toy-30", "toy-40"):
            self.assertNotIn(toy, bases)

    def test_all_strings(self):
        self.assertTrue(all(isinstance(b, str) for b in ttplib.list_bases()))


# ===========================================================================
# Offline instance tests — no network required
# ===========================================================================

class TestMinimalInstanceAttributes(unittest.TestCase):
    def setUp(self):
        self.inst = _load_minimal()

    def test_returns_ttpinstance(self):
        self.assertIsInstance(self.inst, ttplib.TTPInstance)

    def test_name(self):
        self.assertEqual(self.inst.name, "test_n2_uncorr_01")

    def test_dimension(self):
        self.assertEqual(self.inst.dimension, 3)

    def test_num_items(self):
        self.assertEqual(self.inst.num_items, 2)

    def test_capacity(self):
        self.assertEqual(self.inst.capacity, 100)

    def test_speed_bounds_ordered(self):
        self.assertLess(self.inst.min_speed, self.inst.max_speed)

    def test_knapsack_type(self):
        self.assertEqual(self.inst.knapsack_type, "uncorr")

    def test_edge_weight_type(self):
        self.assertEqual(self.inst.edge_weight_type, "EUC_2D")

    def test_str_contains_name(self):
        self.assertIn("test_n2_uncorr_01", str(self.inst))


class TestMinimalGraph(unittest.TestCase):
    def setUp(self):
        self.inst = _load_minimal()

    def test_node_count(self):
        self.assertEqual(self.inst.graph.number_of_nodes(), 3)

    def test_edge_count_complete(self):
        self.assertEqual(self.inst.graph.number_of_edges(), 3)

    def test_nodes_have_x_y_pos(self):
        for _, attrs in self.inst.graph.nodes(data=True):
            self.assertIn("x", attrs)
            self.assertIn("y", attrs)
            self.assertIn("pos", attrs)

    def test_all_edges_have_positive_weight(self):
        for _, _, data in self.inst.graph.edges(data=True):
            self.assertGreater(data["weight"], 0)


class TestMinimalDistanceMethods(unittest.TestCase):
    def setUp(self):
        self.inst = _load_minimal()

    def test_get_distance_known_value(self):
        # city 1=(0,0) → city 2=(3,4): EUC_2D = round(5.0) = 5
        self.assertEqual(self.inst.get_distance(1, 2), 5)

    def test_get_distance_symmetric(self):
        self.assertEqual(self.inst.get_distance(1, 2), self.inst.get_distance(2, 1))
        self.assertEqual(self.inst.get_distance(1, 3), self.inst.get_distance(3, 1))

    def test_distance_matrix_shape(self):
        mat = self.inst.get_distance_matrix()
        self.assertEqual(mat.shape, (3, 3))

    def test_distance_matrix_zero_diagonal(self):
        mat = self.inst.get_distance_matrix()
        np.testing.assert_array_equal(np.diag(mat), 0)

    def test_distance_matrix_symmetric(self):
        mat = self.inst.get_distance_matrix()
        np.testing.assert_array_almost_equal(mat, mat.T)

    def test_distance_matrix_consistent_with_get_distance(self):
        mat = self.inst.get_distance_matrix()
        # nodes sorted: [1, 2, 3] → mat[0,1] == get_distance(1,2)
        self.assertAlmostEqual(mat[0, 1], self.inst.get_distance(1, 2))
        self.assertAlmostEqual(mat[0, 2], self.inst.get_distance(1, 3))

    def test_calculate_tour_distance(self):
        # 1→2→3→1: 5 + 5 + 6 = 16
        self.assertAlmostEqual(self.inst.calculate_tour_distance([1, 2, 3]), 16.0)

    def test_calculate_tour_distance_two_cities(self):
        d = self.inst.get_distance(1, 2)
        self.assertAlmostEqual(self.inst.calculate_tour_distance([1, 2]), 2 * d)


class TestMinimalItems(unittest.TestCase):
    def setUp(self):
        self.inst = _load_minimal()

    def test_item_count(self):
        self.assertEqual(len(self.inst.items), 2)

    def test_item_type(self):
        for item in self.inst.items.values():
            self.assertIsInstance(item, ttplib.Item)

    def test_item_attributes(self):
        item = self.inst.items[1]
        self.assertEqual(item.index, 1)
        self.assertAlmostEqual(item.profit, 10.0)
        self.assertEqual(item.weight, 5)
        self.assertEqual(item.assigned_node, 2)

    def test_profit_weight_ratio(self):
        self.assertAlmostEqual(self.inst.items[1].profit_weight_ratio, 2.0)
        self.assertAlmostEqual(self.inst.items[2].profit_weight_ratio, 2.0)

    def test_zero_weight_ratio(self):
        item = ttplib.Item(index=99, profit=5.0, weight=0, assigned_node=1)
        self.assertEqual(item.profit_weight_ratio, 0.0)

    def test_get_items_at_node_with_items(self):
        items = self.inst.get_items_at_node(2)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].index, 1)

    def test_get_items_at_empty_node(self):
        self.assertEqual(self.inst.get_items_at_node(1), [])

    def test_get_items_by_city_keys(self):
        by_city = self.inst.get_items_by_city()
        self.assertEqual(set(by_city.keys()), {1, 2, 3})

    def test_get_items_by_city_total_count(self):
        by_city = self.inst.get_items_by_city()
        self.assertEqual(sum(len(v) for v in by_city.values()), 2)

    def test_get_item_parameters_by_city(self):
        p_ik, w_ik, m_i = self.inst.get_item_parameters_by_city()
        self.assertEqual(sum(m_i.values()), 2)
        self.assertEqual(p_ik[2], [10.0])
        self.assertEqual(w_ik[2], [5])
        self.assertEqual(m_i[1], 0)

    def test_summary_keys(self):
        s = self.inst.summary()
        for key in ("name", "dimension", "num_items", "capacity",
                    "avg_items_per_city", "total_weight", "total_profit"):
            self.assertIn(key, s)

    def test_summary_values(self):
        s = self.inst.summary()
        self.assertEqual(s["total_weight"], 15)
        self.assertAlmostEqual(s["total_profit"], 30.0)
        self.assertAlmostEqual(s["avg_items_per_city"], 2 / 3)


class TestLoadFile(unittest.TestCase):
    def test_load_file_returns_correct_instance(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(_MINIMAL, f)
            tmp = f.name
        try:
            inst = ttplib.load_file(tmp)
            self.assertIsInstance(inst, ttplib.TTPInstance)
            self.assertEqual(inst.name, "test_n2_uncorr_01")
            self.assertEqual(inst.dimension, 3)
            self.assertEqual(len(inst.items), 2)
        finally:
            os.unlink(tmp)


# ===========================================================================
# Network tests
# ===========================================================================

class TestNetworkLoad(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if SKIP_NETWORK:
            raise unittest.SkipTest("Network tests skipped (TTPLIB_SKIP_NETWORK=1)")
        ttplib.clear_cache()
        cls.inst = ttplib.load(TEST_INSTANCE)

    def test_returns_ttpinstance(self):
        self.assertIsInstance(self.inst, ttplib.TTPInstance)

    def test_name(self):
        # problem_name in the JSON stores the base name, e.g. "berlin52-TTP"
        self.assertEqual(self.inst.name, "berlin52-TTP")

    def test_dimension(self):
        self.assertEqual(self.inst.dimension, 52)

    def test_num_items(self):
        self.assertEqual(self.inst.num_items, 51)

    def test_capacity_positive(self):
        self.assertGreater(self.inst.capacity, 0)

    def test_speed_bounds(self):
        self.assertGreater(self.inst.min_speed, 0)
        self.assertGreater(self.inst.max_speed, self.inst.min_speed)

    def test_renting_ratio_positive(self):
        self.assertGreater(self.inst.renting_ratio, 0)

    def test_knapsack_type_valid(self):
        # The JSON uses full words: "uncorrelated", "uncorrelated similar weights",
        # "bounded strongly corr" — not the abbreviated filename tokens.
        valid = {"uncorrelated", "uncorrelated similar weights", "bounded strongly corr"}
        self.assertIn(self.inst.knapsack_type, valid)

    def test_edge_weight_type_valid(self):
        self.assertIn(self.inst.edge_weight_type, {"CEIL_2D", "EUC_2D"})

    def test_graph_node_count(self):
        self.assertEqual(self.inst.graph.number_of_nodes(), 52)

    def test_graph_complete(self):
        self.assertEqual(self.inst.graph.number_of_edges(), 52 * 51 // 2)

    def test_item_count(self):
        self.assertEqual(len(self.inst.items), 51)

    def test_items_assigned_to_valid_nodes(self):
        for item in self.inst.items.values():
            self.assertGreaterEqual(item.assigned_node, 1)
            self.assertLessEqual(item.assigned_node, 52)

    def test_distance_matrix_symmetric(self):
        mat = self.inst.get_distance_matrix()
        np.testing.assert_array_almost_equal(mat, mat.T)

    def test_tour_distance_positive(self):
        nodes = sorted(self.inst.graph.nodes())
        self.assertGreater(self.inst.calculate_tour_distance(nodes), 0)

    def test_str_output(self):
        s = str(self.inst)
        self.assertIn("berlin52", s)
        self.assertIn("52", s)


class TestNetworkCaching(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if SKIP_NETWORK:
            raise unittest.SkipTest("Network tests skipped (TTPLIB_SKIP_NETWORK=1)")

    def test_memory_cache_returns_same_object(self):
        ttplib.clear_cache()
        inst1 = ttplib.load(TEST_INSTANCE)
        inst2 = ttplib.load(TEST_INSTANCE)
        self.assertIs(inst1, inst2)

    def test_clear_cache_empties_mem_cache(self):
        ttplib.load(TEST_INSTANCE)
        ttplib.clear_cache()
        self.assertEqual(len(_mem_cache), 0)

    def test_load_no_cache_returns_valid_instance(self):
        ttplib.clear_cache()
        inst = ttplib.load(TEST_INSTANCE, cache=False)
        self.assertIsInstance(inst, ttplib.TTPInstance)
        self.assertEqual(inst.name, "berlin52-TTP")


class TestNetworkErrors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if SKIP_NETWORK:
            raise unittest.SkipTest("Network tests skipped (TTPLIB_SKIP_NETWORK=1)")

    def test_load_invalid_name_raises_runtime_error(self):
        with self.assertRaises(RuntimeError):
            ttplib.load("this_instance_does_not_exist_xyz_abc")


if __name__ == "__main__":
    unittest.main(verbosity=2)
