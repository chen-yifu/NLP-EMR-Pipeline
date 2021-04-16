import string
from dataclasses import dataclass
from typing import List

table = str.maketrans(dict.fromkeys(string.punctuation))


@dataclass
class Column:
    """ Dataclass used to represent a column in a report and its relationship with the excel file
    """

    def __init__(self, human_col: str, primary_report_col: List[str], alternative_report_col: List[str],
                 threshold: float, remove_stopwords: bool = False):
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
        self.remove_stopwords = remove_stopwords
