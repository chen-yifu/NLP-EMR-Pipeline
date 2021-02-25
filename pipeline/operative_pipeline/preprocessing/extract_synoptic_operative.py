import re
from typing import Tuple, List
from pipeline.util.regex_tools import preoperative_rational_regex, operative_breast_regex, operative_axilla_regex, \
    right_operative_report, left_operative_report, pathology_synoptic_regex, export_operative_regex, \
    export_pathology_regex
from pipeline.util.report import Report
from pipeline.util.report_type import ReportType


def regex_extract(regex: str, uncleaned_txt: str) -> list:
    return re.findall(re.compile(regex), uncleaned_txt)


def find_laterality(laterality: List[List[str]]) -> str:
    """
    Determines laterality of a report

    :param laterality:      list of regex results. regex results is a list of string
    :return:                the laterality the pipeline found
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


def find_left_right_label_synoptic(string, study_id, print_debug=True):
    """
    given the synoptic report, detect it's about the left or right breast
    :param study_id:    string;           study id of report
    :param string:      string;           input synoptic report
    :param print_debug: boolean;          print debug statements if True
    :return:            string;           suffix, one of "L", "R", or "_laterality_undetected"
    """
    string = string.lower()

    # regex demo: https://regex101.com/r/FX8VfI/8
    regex = re.compile(
        r"p *a *r *t *\( *s *\) *i *n *v *o *l *v *e *d *: *\n.*(?P<laterality>l *e *f *t *|r *i *g *h *t *).*")
    match = re.search(regex, string)

    try:
        laterality = match.group("laterality")
        laterality = laterality.replace(" ", "").strip()
        if laterality == "left":
            return "L"
        else:
            return "R"
    except AttributeError:
        return "unknown"


# if the regex is able to find two preoperative, two operative breast/axilla it means that the report is bilateral
def extract_laterality(uncleaned_txt: str) -> str:
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


def extract_section(regexs: List[Tuple[str, str]], uncleaned_txt: str) -> list:
    """
    General function that takes in a list of regex and returns the first one that returns a result

    :param uncleaned_txt:
    :param regexs:            list of tuple(regex,to_append) and the list should ne entered in priority
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


def extract_synoptic_report(uncleaned_txt: str, report_id: str, report_type: ReportType,
                            list_of_regex: List[List[Tuple[str, str]]],
                            lat: str = "",
                            is_bilateral=False) -> List[Report]:
    """
    Takes in a single report and extracts useful sections as well as laterality of report.

    :param list_of_regex:
    :param is_bilateral:
    :param report_id:
    :param lat:                the laterality associated with a report
    :param uncleaned_txt:      just a string of the pdf text
    :return:                   list of tuple of a dictionary of extracted sections and report laterality, if found
    """

    def split_report_find_left_right_pathlogy(matches: List[str]) -> List[Report]:
        reports_to_return = []
        for m in matches:
            label = report_id + find_left_right_label_synoptic(m, report_id)
            reports_to_return.append(Report(text=m, report_id=label))
        return reports_to_return

    def split_report_find_left_right_operative(preoperative_rational: List[str], operative_breast: List[str],
                                               operative_axilla: List[str]) -> List[Report]:
        """
        Splits a report into right and left breast if it is found that there are two synoptic reports

        :return:
        """
        reports_to_return = []
        # len(preoperative_rational) == len(operative_breast) == len(operative_axilla)
        if False:  # todo: implement this
            for index in range(len(preoperative_rational)):
                reports_to_return.append(
                    Report(text=[preoperative_rational[index] + operative_breast[index] + operative_axilla[index]]))
        else:
            left_breast = extract_section(left_operative_report, uncleaned_txt)
            right_breast = extract_section(right_operative_report, uncleaned_txt)

            return extract_synoptic_report(left_breast[0] if len(left_breast) > 0 else "",
                                           report_id=report_id, lat="left",
                                           is_bilateral=True, list_of_regex=list_of_regex,
                                           report_type=report_type) + extract_synoptic_report(
                right_breast[0] if len(right_breast) > 0 else "", report_id=report_id, lat="right", is_bilateral=True,
                list_of_regex=list_of_regex,
                report_type=report_type)

    # pathology report
    pathology_report = extract_section(pathology_synoptic_regex, uncleaned_txt)

    # operative report
    preoperative_rational = extract_section(preoperative_rational_regex, uncleaned_txt)
    operative_breast = extract_section(operative_breast_regex, uncleaned_txt)
    operative_axilla = extract_section(operative_axilla_regex, uncleaned_txt)

    is_pathology = len(pathology_report) > 0
    is_operative = len(preoperative_rational) == 1 or len(operative_breast) == 1 or len(operative_axilla) == 1

    # means multiple
    if len(preoperative_rational) > 1:
        return split_report_find_left_right_operative(preoperative_rational, operative_breast, operative_axilla)

    if len(pathology_report) > 1:
        return split_report_find_left_right_pathlogy(pathology_report)

    if is_operative:
        laterality = lat if lat != "" else extract_laterality(uncleaned_txt)
        to_append = laterality[0].upper() if len(laterality) > 0 else ""
        return [Report(text=preoperative_rational + operative_breast + operative_axilla,
                       report_id=report_id + to_append if is_bilateral else report_id,
                       laterality=laterality)]

    elif is_pathology:
        return [Report(text=pathology_report[0], report_id=report_id)]

    else:
        return report_id


def clean_up_reports(emr_text: List[Report]) -> Tuple[List[Report], List[str]]:
    """
    Wrapper function to clean up list of reports

    :param emr_text:              list of reports that is currently not sorted or filtered
    :return cleaned_reports:      returns list of reports that have been separated into preoperative breast, operative breast and operative axilla
    """
    ids_without_synoptic = []
    report_and_id = []
    for report in emr_text:
        text = report.text
        list_of_regex = export_operative_regex if report.report_type is ReportType.OPERATIVE else export_pathology_regex
        extracted_reports = extract_synoptic_report(uncleaned_txt=text, report_id=report.report_id,
                                                    list_of_regex=list_of_regex, report_type=report.report_type)
        if isinstance(extracted_reports, str):
            ids_without_synoptic.append(extracted_reports)
        else:
            for cleaned_report in extracted_reports:
                report_and_id.append(cleaned_report)
    return report_and_id, ids_without_synoptic
