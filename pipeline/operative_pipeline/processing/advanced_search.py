from typing import Tuple, Any, Union
import re
from util.report import Report
from util.import_tools import import_other_cols
from util.utils import capture_between_regex


def extensive_search(report: Report, path_to_other_cols: str = "data/inputs/other_cols_human_cols.xlsx"):
    """
    :param report:
    :param path_to_other_cols:
    """
    other_cols = import_other_cols(path_to_other_cols)
    for human_col, tuple_other in other_cols.items():
        start, end = tuple_other
        found, result = unstructured_search(report.report, capture_between_regex(start, end))
        report.advanced[human_col] = result if found else ""


def unstructured_search(txt_to_search: str, regex: str) -> Union[Tuple[bool, Any], Tuple[bool, str]]:
    """
    :param txt_to_search:
    :param regex:
    :return:
    """
    regex_to_search = re.compile(regex)
    result = re.findall(regex_to_search, txt_to_search)
    return (True, result[0]) if len(result) > 0 else (False, "")
