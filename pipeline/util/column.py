import string
from dataclasses import dataclass
from typing import List

table = str.maketrans(dict.fromkeys(string.punctuation))


@dataclass
class Column:
    def __init__(self, human_col: str, primary_report_col: List[str], alternative_report_col: List[str]):
        self.human_col = human_col
        self.primary_report_col = [col.strip() for col in primary_report_col]
        self.alternative_report_col = [col.strip() for col in alternative_report_col]
        self.cleaned_primary_report_col = [col.translate(table).lower().strip() for col in primary_report_col]
        self.cleaned_alternative_report_col = [col.translate(table).lower().strip() for col in alternative_report_col]
