"""
2021 Yifu (https://github.com/chen-yifu) and Lucy (https://github.com/lhao03)
This file includes code represents a Encoding object.
"""
from dataclasses import dataclass
from typing import List


@dataclass
class Encoding:
    """
    Dataclass used to hold a value's encoding and its extracted value
    """
    def __init__(self, val: List[str], num: int):
        self.val = val
        self.num = num
