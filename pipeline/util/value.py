from dataclasses import dataclass
from typing import List


@dataclass
class Value:
    def __init__(self, primary_value: str, secondary_value=None):
        if secondary_value is None:
            secondary_value = []
        self.primary_value = primary_value
        self.secondary_value = secondary_value
