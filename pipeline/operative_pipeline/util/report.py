from typing import Union


class Report:
    def __init__(self, report: str, report_id: str, operative_breast: Union[dict, list] = None,
                 operative_axilla: Union[dict, list] = None, preoperative_breast: Union[dict, list] = None,
                 laterality: str = "", not_found: list = None, encoded=None, advanced=None):
        """
        :param report:
        :param report_id:
        :param operative_breast:
        :param operative_axilla:
        :param preoperative_breast:
        :param laterality:
        :param not_found:
        :param encoded:
        """
        if advanced is None:
            self.advanced = {}
        if encoded is None:
            self.encoded = {}
        if not_found is None:
            self.not_found = []
        if operative_breast is None:
            self.operative_breast = []
        if preoperative_breast is None:
            self.preoperative_breast = []
        if operative_axilla is None:
            self.operative_axilla = []
        self.report = report
        self.report_id = report_id
        self.laterality = laterality
        self.preoperative_breast = preoperative_breast
        self.operative_breast = operative_breast
        self.operative_axilla = operative_axilla
        self.not_found = not_found
        self.encoded = encoded
