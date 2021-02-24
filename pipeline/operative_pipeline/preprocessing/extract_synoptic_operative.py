import re
from typing import Tuple, List
from pipeline.util.regex_tools import preoperative_rational_regex, operative_breast_regex, operative_axilla_regex, \
    right_operative_report, left_operative_report
from pipeline.util.report import Report
from pipeline.util.report_type import ReportType


def regex_extract(regex: str, uncleaned_txt: str) -> list:
    """
    General function to extract text with regex
    """
    return re.findall(re.compile(regex), uncleaned_txt)


def find_laterality(laterality: List[List[str]]) -> str:
    """
    Determines laterality of a report

    :param laterality:      list of regex results. regex results is a list of string
    :return:                the laterality the pipeine found
    """
    for list_result in laterality:
        for possible_lat in list_result:
            cleaned_possible_lat = possible_lat.lower()
            right = cleaned_possible_lat.find("right")
            left = cleaned_possible_lat.find("left")
            if left == -1 and right == -1:
                continue
            elif right > -1 and left == -1:
                return "right"
            elif left > -1 and right == -1:
                return "left"
            elif right > -1 and left > -1:
                return "bilateral"
    return ""


def extract_synoptic_report(uncleaned_txt: str, lat: str = "") -> List[Tuple[dict, str]]:
    """
    Takes in a single report and extracts useful sections as well as laterality of report.

    :param report_type:
    :param lat:                the laterality associated with a report
    :param uncleaned_txt:      just a string of the pdf text
    :return:                   list of tuple of a dictionary of extracted sections and report laterality, if found
    """

    # if the regex is able to find two preoperative, two operative breast/axilla it means that the report is bilateral
    def extract_laterality() -> str:
        # TODO: need to fix -> cannot just use operation performed to determine
        """
        The function that searches for laterality
        Your list of possible locations of laterality should be in highest priority to lowest priority

        :return:      laterality, which can be left, right or bilateral
        """
        # https://rubular.com/r/TAsSFuPoU8X13N
        regex_for_procedure = r"[\n\r](?i) *PROCEDURE*\s*([^\n\r]*)"
        laterality_procedure_upper = regex_extract(regex_for_procedure, uncleaned_txt)

        regex_for_postoperative_diagnosis = r"[\n\r](?i) *POSTOPERATIVE DIAGNOSIS*\s*([^\n\r]*)"
        laterality_postop = regex_extract(regex_for_postoperative_diagnosis, uncleaned_txt)

        # regex is here: https://rubular.com/r/J5CfqTgNj0xo9Q for operation performed
        regex_for_laterality_operation_performed = r"[\n\r](?i) *O *P *E *R *A *T *I *O *N P *E *R *F *O *R *M *E *D *\s*([^\n\r]*)"
        laterality_operation_performed = regex_extract(regex_for_laterality_operation_performed, uncleaned_txt)

        # regex is here: https://rubular.com/r/rj6JsbwydrCW99 for procedure performed
        regex_for_laterality_procedure = r"[\n\r].*(?i)P *r *o *c *e *d *u *r *e *:\s*([^\n\r]*)"
        laterality_procedure = regex_extract(regex_for_laterality_procedure, uncleaned_txt)
        return find_laterality(
            [laterality_operation_performed, laterality_procedure, laterality_postop, laterality_procedure_upper])

    def extract_section(regexs: List[Tuple[str, str]]) -> list:
        """
        General function that takes in a list of regex and returns the first one that returns a result

        :param regexs:      list of tuple(regex,to_append) and the list should ne entered in priority
        :return:
        """
        for regex, to_append in regexs:
            extraction_result = regex_extract(regex, uncleaned_txt)
            if len(extraction_result) != 0:
                if to_append == "":
                    return extraction_result
                result = to_append + extraction_result[0]
                return [result]
        return []

    def split_report_find_left_right() -> List[Tuple[dict, str]]:
        """
        Splits a report into right and left breast if it is found that there are two synoptic reports

        :return:
        """
        left_breast = extract_section(left_operative_report)
        right_breast = extract_section(right_operative_report)

        return extract_synoptic_report(left_breast[0] if len(left_breast) > 0 else "",
                                       lat="left") + extract_synoptic_report(
            right_breast[0] if len(right_breast) > 0 else "", lat="right")

    preoperative_rational = extract_section(preoperative_rational_regex)
    operative_breast = extract_section(operative_breast_regex)
    operative_axilla = extract_section(operative_axilla_regex)

    if len(preoperative_rational) > 1:
        return split_report_find_left_right()

    return [({"extractions": preoperative_rational + operative_breast + operative_axilla,
              "laterality": lat if lat != "" else extract_laterality()}, lat)]


def clean_up_reports(emr_text: List[Report]) -> List[Report]:
    """
    Wrapper function to clean up list of reports

    :param emr_text:              list of reports that is currently not sorted or filtered
    :return cleaned_reports:      returns list of reports that have been separated into preoperative breast, operative breast and operative axilla
    """
    cleaned_reports = []
    for report in emr_text:
        text = report.text
        cleaned_pdf = extract_synoptic_report(uncleaned_txt=text)
        for cleaned_report in cleaned_pdf:
            report_info = cleaned_report[0]
            cleaned_reports.append(Report(text=text,
                                          report_id=str(report.report_id) + cleaned_report[1][0].upper() if len(
                                              cleaned_report[1]) > 0 else str(report.report_id) + cleaned_report[1],
                                          laterality=report_info['laterality'],
                                          extractions=report_info["extractions"]))
    return cleaned_reports
