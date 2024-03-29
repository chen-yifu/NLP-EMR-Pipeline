"""
2021 Yifu (https://github.com/chen-yifu) and Lucy (https://github.com/lhao03)
This file includes code that preprocesses a report and searches for synoptic sections in a report.
There can be 1 or 2 synoptic sections in a report.
"""
import itertools
import re
from typing import Tuple, List
from pipeline.utils.regex_tools import right_operative_report, left_operative_report, export_operative_regex, \
    export_pathology_regex, extract_section
from pipeline.utils.report import Report
from pipeline.utils.report_type import ReportType


# TODO: This is still pretty bad
def find_left_right_label(string: str, report_type: ReportType, print_debug=True):
    """
    given the synoptic report, detect it's about the left or right breast

    :param report_type:       enum, TEXT or NUMERICAL
    :param string:            input synoptic report
    :param print_debug:       print debug statements if True
    :return:                  suffix, one of "L", "R", or "_laterality_undetected"
    """
    match = ""
    # https://regex101.com/r/ITYrAN/1
    preop_diag = r"PREOPERATIVE DIAGNOSIS[\s\S]*?(?P<laterality>l *e *f *t|r *i *g *h *t|Right|Left).*"
    # https://regex101.com/r/P2KVkz/1
    clinical_pream = r"(?i)CLINICAL PREAMBLE[\s\S]*?(?P<laterality>l *e *f *t|r *i *g *h *t|Right|Left).*"
    op_perforemd = r"OPERATION PERFORMED[\s\S]*?(?P<laterality>l *e *f *t|r *i *g *h *t|Right|Left).*"
    # regex demo: https://regex101.com/r/FX8VfI/8
    parts_involved = r"(?i)p *a *r *t *\( *s *\) *i *n *v *o *l *v *e *d *: *\n.*(?P<laterality>l *e *f *t *|r *i *g " \
                     r"*h *t *).* "
    list_of_laterality_regex = [parts_involved, preop_diag, clinical_pream, op_perforemd]

    for laterality_regex in list_of_laterality_regex:
        laterality_regex = re.compile(laterality_regex)
        match = re.search(laterality_regex, string)
        try:
            laterality = match.group("laterality").replace(" ", "").strip().lower()
            if laterality == "left":
                return "L"
            elif laterality == "right":
                return "R"
            else:
                raise AttributeError
        except AttributeError:
            continue

    try:
        laterality = match.group("laterality").replace(" ", "").strip()
        return "L" if laterality.lower() == "left" else "R"
    except AttributeError:
        return "unknown"


def extract_synoptic_report(uncleaned_txt: str, report_id: str, report_type: ReportType,
                            list_of_regex: List[List[Tuple[str, str]]], lat: str = "",
                            is_bilateral=False) -> List[Report]:
    """
    Takes in a single report and extracts useful sections as well as laterality of report.

    :param report_type:
    :param list_of_regex:
    :param is_bilateral:
    :param report_id:
    :param lat:                the laterality associated with a report
    :param uncleaned_txt:      just a string of the pdf text
    :return:                   list of tuple of a dictionary of extracted sections and report laterality, if found
    """

    def split_report_find_left_right_pathlogy(matches: List[str]) -> List[Report]:
        """
        :param matches:
        :return:
        """
        reports_to_return = []
        for m in matches:
            label = report_id + find_left_right_label(m, report_type=report_type)
            reports_to_return.append(Report(text=m, report_id=label, report_type=report_type))
        return reports_to_return

    def split_report_find_left_right_operative() -> List[Report]:
        """
        :return:
        """
        left_breast = extract_section(left_operative_report, uncleaned_txt)
        left_text = left_breast[0] if len(left_breast) > 0 else ""
        left_text = left_text[0] if isinstance(left_text, tuple) else left_text
        right_breast = extract_section(right_operative_report, uncleaned_txt)
        right_text = right_breast[0] if len(right_breast) > 0 else ""
        right_text = right_text[0] if isinstance(right_text, tuple) else right_text

        return [Report(text=left_text, report_id=report_id + "L", laterality="left", report_type=report_type),
                Report(text=right_text, report_id=report_id + "R", laterality="right", report_type=report_type)]

        # return extract_synoptic_report(left_breast[0] if len(left_breast) > 0 else "",
        #                                report_id=report_id, lat="L",
        #                                is_bilateral=True, list_of_regex=list_of_regex,
        #                                report_type=report_type) + extract_synoptic_report(
        #     right_breast[0] if len(right_breast) > 0 else "", report_id=report_id, lat="R", is_bilateral=True,
        #     list_of_regex=list_of_regex,
        #     report_type=report_type)

    extracted_sections = []
    for regex in list_of_regex:
        uncleaned_txt = uncleaned_txt if isinstance(uncleaned_txt, str) else uncleaned_txt[0]
        extracted_sections.append(extract_section(regex, uncleaned_txt))

    if all(len(single_section) == 0 for single_section in extracted_sections):
        return []

    elif all(len(single_section) == 1 for single_section in extracted_sections):
        merged_extractions = list(itertools.chain(*extracted_sections))
        if report_type is ReportType.ALPHA:
            laterality = lat if lat != "" else find_left_right_label(uncleaned_txt, report_type=report_type)
            return [Report(text="".join(merged_extractions), report_type=report_type,
                           report_id=report_id + laterality if is_bilateral else report_id,
                           laterality="left" if laterality == "L" else "right")]
        elif report_type is ReportType.NUMERICAL:
            return [Report(text=merged_extractions[0], report_type=report_type, report_id=report_id)]

    elif any(len(single_section) > 1 for single_section in extracted_sections):
        if report_type is ReportType.ALPHA:
            return split_report_find_left_right_operative()
        elif report_type is ReportType.NUMERICAL:
            return split_report_find_left_right_pathlogy(extracted_sections[0])


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
        list_of_regex = export_operative_regex if report.report_type is ReportType.ALPHA else export_pathology_regex
        extracted_reports = extract_synoptic_report(uncleaned_txt=text, report_id=report.report_id,
                                                    list_of_regex=list_of_regex, report_type=report.report_type)
        if isinstance(extracted_reports, str):
            ids_without_synoptic.append(extracted_reports)
        else:
            if extracted_reports:
                for cleaned_report in extracted_reports:
                    report_and_id.append(cleaned_report)
            else:
                report_and_id.append(Report(text=text, report_id=report.report_id, report_type=report.report_type))
    return report_and_id, ids_without_synoptic
