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
