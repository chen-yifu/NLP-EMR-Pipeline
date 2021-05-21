"""
2021 Yifu (https://github.com/chen-yifu) and Lucy (https://github.com/lhao03)
This file includes code represents a Column object
"""

import string
from dataclasses import dataclass
from typing import List

table = str.maketrans(dict.fromkeys(string.punctuation))


@dataclass
class Column:
    """ Dataclass used to represent a column in a report and its relationship with the excel file
    """

    def __init__(self, human_col: str, primary_report_col: List[str], regular_pattern_rules: dict = {},
                 alternative_report_col: List[str] = [], threshold: float = 0.75,
                 zero_empty: bool = False,
                 # regex rules stat

                 # front cap rules
                 val_on_same_line: bool = True,
                 val_on_next_line: bool = False,

                 # end cap rules
                 capture_up_to_separator: bool = True,
                 capture_up_to_keyword: bool = False,
                 capture_up_to_end_of_line: bool = False,

                 # front cap col rules
                 add_separator_in_front_cap: bool = False,
                 add_anchor: bool = True):
        """
        :param human_col:              The column that the individual wants the extracted information to be under
        :param primary_report_col:     The most likely column in the report in which we can find the information
        :param alternative_report_col: Sometimes information can be found in two columns, put the second most likely one here
        :param threshold:
        """
        self.human_col = human_col
        self.primary_report_col = [col.strip() for col in primary_report_col]
        self.alternative_report_col = [col.strip() for col in alternative_report_col]
        # List of primary columns stripped of punctuation, spaces and lowercased
        self.cleaned_primary_report_col = [" ".join(col.translate(table).lower().strip().split()) for col in
                                           primary_report_col]
        # List of alternative columns stripped of punctuation, spaces and lowercased
        self.cleaned_alternative_report_col = [" ".join(col.translate(table).lower().strip().split()) for col in
                                               alternative_report_col]
        self.spacy_threshold = threshold
        self.zero_empty = zero_empty
        self.regular_pattern_rules = regular_pattern_rules if regular_pattern_rules != {} else {
            "val on same line": val_on_same_line, "val on next line": val_on_next_line,
            "add anchor": add_anchor, "add separator to col name": add_separator_in_front_cap,
            "capture to end of val": capture_up_to_end_of_line,
            "capture up to line with separator": capture_up_to_separator,
            "capture up to keyword": capture_up_to_keyword}
        self.found_during_execution = []
