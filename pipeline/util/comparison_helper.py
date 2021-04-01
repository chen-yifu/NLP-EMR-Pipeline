"""
ComparisonHelper is a dataclass that holds information about a comparison between pipeline and human value.
"""

from dataclasses import dataclass


@dataclass
class ComparisonHelper:
    """
    Data Class used for returning information needed in creating excel sheet
    """

    def __init__(self, value: str, missing: bool, wrong: bool, correct: bool):
        self.value = value
        self.missing = missing
        self.wrong = wrong
        self.correct = correct
