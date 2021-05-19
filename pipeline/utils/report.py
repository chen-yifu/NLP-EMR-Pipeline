"""
2021 Yifu (https://github.com/chen-yifu) and Lucy (https://github.com/lhao03)
This file includes code that represents a Report object.
"""

from typing import Union, List, Dict

from pipeline.utils.value import Value
from pipeline.utils.report_type import ReportType


class Report:
    """
    Represents information extracted and manipulated from a scanned pdf report.
    """

    def __init__(self, text: str, report_id: str, extractions: Dict[str, Union[str, Value]] = None,
                 laterality: str = "", not_found: list = None, encoded: Dict[str, str] = None,
                 report_type: ReportType = None):
        """
        :param report_type: the type of report, is an enumeration
        :param text:        the literal report
        :param report_id:   the id of the report
        :param laterality:  laterality of breast for report
        :param not_found:   columns that are not found
        :param encoded:     encoded extractions
        :param extractions: the extracted values
        """
        if encoded is None:
            self.encoded = {}
        if extractions is None:
            self.extractions = {}
        if not_found is None:
            self.not_found = []
        self.report_type = report_type
        self.text = text
        self.report_id = report_id
        self.laterality = laterality
        self.not_found = not_found
        self.encoded = encoded
        self.extractions = extractions
