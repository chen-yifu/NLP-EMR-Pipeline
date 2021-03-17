from typing import Union

from pipeline.util.report_type import ReportType


class Report:

    def __init__(self, text: str, report_id: str, extractions: Union[dict, list] = None, laterality: str = "",
                 not_found: list = None, encoded=None, report_type: ReportType = None):
        """
        :param report_type:
        :param text:
        :param report_id:
        :param laterality:
        :param not_found:
        :param encoded:
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
