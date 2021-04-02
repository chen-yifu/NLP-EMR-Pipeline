from dataclasses import dataclass
from typing import List


@dataclass
class Value:
    """
    Dataclass that represents a value that is extracted from the report.
    """

    def __init__(self, primary_value: str, alternative_value: List[str] = None):
        """
        :param primary_value:     the value extracted from the primary column
        :param alternative_value: the value extracted from the alternative column
        """
        if alternative_value is None:
            alternative_value = []
        self.primary_value = primary_value
        self.alternative_value = alternative_value
