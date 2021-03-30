from dataclasses import dataclass
from typing import List


@dataclass
class Encoding:
    def __init__(self, val: List[str], num: int):
        self.val = val
        self.num = num
