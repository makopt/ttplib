"""ttplib — Travelling Thief Problem instance library.

Load any of the 9,720 benchmark TTP instances directly from the network:

    import ttplib

    problem = ttplib.load("berlin52_n51_uncorr_01")
    print(problem)

    names = ttplib.list_instances(base="berlin52")

The four instances whose original file gives a renting rate of 0.00 are served in a corrected version by default;
use ttplib.load(name, corrected=False) for the original 2014 file.
"""

from .instance import Item, TTPInstance
from .remote import (BASE_URL, CORRECTED, CORRECTED_URL, clear_cache, is_corrected, list_bases, list_instances,
                     load, load_file)

__all__ = [
    "TTPInstance",
    "Item",
    "load",
    "load_file",
    "list_instances",
    "list_bases",
    "clear_cache",
    "BASE_URL",
    "CORRECTED",
    "CORRECTED_URL",
    "is_corrected",
]

__version__ = "0.2.0"
