"""ttplib — Travelling Thief Problem instance library.

Load any of the 9,720 benchmark TTP instances directly from the network:

    import ttplib

    problem = ttplib.load("berlin52_n51_uncorr_01")
    print(problem)

    names = ttplib.list_instances(base="berlin52")
"""

from .instance import Item, TTPInstance
from .remote import BASE_URL, clear_cache, list_bases, list_instances, load, load_file

__all__ = [
    "TTPInstance",
    "Item",
    "load",
    "load_file",
    "list_instances",
    "list_bases",
    "clear_cache",
    "BASE_URL",
]

__version__ = "0.1.0"
