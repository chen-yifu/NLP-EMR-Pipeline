"""
Tuning is a dataclass that holds information about tuning.
"""
from dataclasses import dataclass


@dataclass
class Tuning:
    """
    Represents information needed to be used in tuning.
    """

    def __init__(self, col_name: str, sub_cost: int, large_cost: int):
        self.col_name = col_name
        self.sub_cost = sub_cost
        self.large_cost = large_cost
