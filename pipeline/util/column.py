from dataclasses import dataclass
from typing import List


@dataclass
class Column:
    def __init__(self, human_col: str, primary_report_col: List[str], alternative_report_col: List[str]):
        self.human_col = human_col
        self.primary_report_col = primary_report_col
        self.alternative_report_col = alternative_report_col
