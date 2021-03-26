from dataclasses import dataclass


@dataclass
class Value:
    def __init__(self, primary_value, secondary_value):
        self.primary_value = primary_value
        self.secondary_value = secondary_value
