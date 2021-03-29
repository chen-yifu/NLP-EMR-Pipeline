from dataclasses import dataclass
from typing import List


@dataclass
class Value:
    def __init__(self, primary_value: str, alternative_value: List[str] = None):
        if alternative_value is None:
            alternative_value = []
        self.primary_value = primary_value
        self.alternative_value = alternative_value
