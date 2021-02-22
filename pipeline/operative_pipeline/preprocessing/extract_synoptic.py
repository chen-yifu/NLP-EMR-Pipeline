import re
from typing import Tuple, List

from pipeline.util.report import Report
from pipeline.util.utils import capture_double_regex


def find_laterality(laterality: List[List[str]]) -> str:
    """
    :param laterality:
    :return:
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


def extract_synoptic_operative_report(uncleaned_txt: str, lat: str = "") -> List[Tuple[dict, str]]:
    """
    Takes in a single report and extracts useful sections as well as laterality of report.
    :param lat:                the laterality associated with a report
    :param uncleaned_txt:      just a string of the pdf text
    :return:                   list of tuple of a dictionary of extracted sections and report laterality, if found
    """

    def regex_extract(regex: str) -> list:
        """
        :param regex:      a general regex string
        :return:           list of text or empty list if the regex did not find any
        """
        result = re.findall(re.compile(regex), uncleaned_txt)
        return result if len(result) > 0 else []

    # if the regex is able to find two preoperative, two operative breast/axilla it means that the report is bilateral
    def extract_laterality() -> str:
        # TODO: need to fix -> cannot just use operation performed to determine
        """
        :return:      laterality, which can be left, right or bilateral
        """
        # https://rubular.com/r/TAsSFuPoU8X13N
        regex_for_procedure = r"[\n\r](?i) *PROCEDURE*\s*([^\n\r]*)"
        laterality_procedure_upper = regex_extract(regex_for_procedure)

        regex_for_postoperative_diagnosis = r"[\n\r](?i) *POSTOPERATIVE DIAGNOSIS*\s*([^\n\r]*)"
        laterality_postop = regex_extract(regex_for_postoperative_diagnosis)

        # regex is here: https://rubular.com/r/J5CfqTgNj0xo9Q for operation performed
        regex_for_laterality_operation_performed = r"[\n\r](?i) *O *P *E *R *A *T *I *O *N P *E *R *F *O *R *M *E *D *\s*([^\n\r]*)"
        laterality_operation_performed = regex_extract(regex_for_laterality_operation_performed)

        # regex is here: https://rubular.com/r/rj6JsbwydrCW99 for procedure performed
        regex_for_laterality_procedure = r"[\n\r].*(?i)P *r *o *c *e *d *u *r *e *:\s*([^\n\r]*)"
        laterality_procedure = regex_extract(regex_for_laterality_procedure)
        return find_laterality(
            [laterality_operation_performed, laterality_procedure, laterality_postop, laterality_procedure_upper])

    def extract_section(regexs: List[Tuple[str, str]]) -> list:
        """
        :param regexs:      list of tuple(regex,to_append) and the list should ne entered in priority
        :return:
        """
        for regex, to_append in regexs:
            extraction_result = regex_extract(regex)
            if len(extraction_result) != 0:
                if to_append == "":
                    return extraction_result
                result = to_append + extraction_result[0]
                return [result]
        return []

    def extract_preoperative_rational() -> list:
        """
        :return: 
        """
        # regex is here: https://regex101.com/r/DzdwRT/1
        # another regex is here:
        regex_for_preoperative = r"(?i)P *R *E *O *P *E *R *A *T *I *V *E .* *R *A *T *I *O *N *A *L.* F *O *R S *U *R *G *E *R *Y *(?P<capture>(?:(?! *O *P *E *R *A *T *I *V *E *D *E*T *A *I *L *S.* B *R *E *A *S *T)[\s\S])+)"
        preoperatives = regex_extract(regex_for_preoperative)
        if len(preoperatives) == 0:
            # regex i here for preop: https://regex101.com/r/H39XrF/1
            re_preop = r"(?i)I *n *d *i *c *a *t *i *o *n *(?P<capture>(?:(?!B *r *e *a *s *t p *r *o *c *e *d *u *r *e)[\s\S])+)"
            result_preop = regex_extract(re_preop)
            found_preop = "indication " + result_preop[0] if result_preop != [] else ""
            return [found_preop]
        return preoperatives

    def extract_breast_operative() -> list:
        """
        :return:
        """
        # regex is here: https://regex101.com/r/4fFuEH/1
        regex_for_operative_breast = r"(?i)O *P *E *R *A *T *I *V *E  *D *E *T *A *I *L *S.* B *R *E *A *S *T(?P<capture>(?:(?! O *P *E *R *A *T *I *V *E d *e *t *a *i *l *s.* A *X *I *L *L *A)[\s\S])+)"
        breast_operatives = regex_extract(regex_for_operative_breast)
        if len(breast_operatives) == 0:
            # regex for operative breast: https://regex101.com/r/DAcgWC/1
            re_op_b = r"(?i)B *r *e *a *s *t p *r *o *c *e *d *u *r *e *(?P<capture>(?:(?!(?i)A *x *i *l *l *a *r *y p *r *o *c *e *d *u *r *e *)[\s\S])+)"
            result_opb = regex_extract(re_op_b)
            found_op_b = "breast procedure " + result_opb[0] if result_opb != [] else ""
            return [found_op_b]
        return breast_operatives

    def extract_axilla_operative() -> list:
        """
        :return:
        """
        # regex is here: https://regex101.com/r/eCYicM/1
        regex_for_operative_axilla = r"(?i)O *P *E *R *A *T *I *V *E D *E *T *A *I *L *S.* A *X *I *L *L *A *(?P<capture>(?:(?! P *R *O *C *E *D *U *R *E C *O *M *P *L *E *T *I *O *N)[\s\S])+)"
        axilla_operatives = regex_extract(regex_for_operative_axilla)
        if len(axilla_operatives) == 0:
            # regex for operative axilla: https://regex101.com/r/uNtjeI/1
            re_op_a = r"(?i)A *x *i *l *l *a *r *y p *r *o *c *e *d *u *r *e *(?P<capture>(?:(?!(?i)U *n *p *l *a *n *n *e *d e *v *e *n *t *s *)[\s\S])+)"
            result_opa = regex_extract(re_op_a)
            found_op_a = "axillary procedure " + result_opa[0] if result_opa != [] else ""
            return [found_op_a]
        return axilla_operatives

    def extract_section_regex_laterality(regex: str) -> str:
        """
        :param regex:
        :return:
        """
        result = regex_extract(regex)
        return "PREOPERATIVE RATIONALE FOR SURGERY" + result[0] if len(result) == 1 else ""

    def split_report_find_left_right() -> List[Tuple[dict, str]]:
        """
        :return:
        """
        # https://regex101.com/r/kT4aT7/1
        left_regex = r"(?i)L *e *f *t b *r *e *a *s *t *:(?P<capture>(?:(?!(?i)R *i *g *h *t b *r *e *a *s *t *:)[\s\S])+)"
        left_breast = extract_section_regex_laterality(left_regex)
        # https://regex101.com/r/AE3qZs/1
        right_regex = r"(?i)R *i *g *h *t b *r *e *a *s *t *:(?P<capture>(?:(?!(?i)R *i *g *h *t b *r *e *a *s *t *:)[\s\S])+)"
        right_breast = extract_section_regex_laterality(right_regex)

        if left_breast == "" or right_breast == "":
            # https://regex101.com/r/l760jr/1
            left_regex = r"(?i)PREOPERATIVE EVALUATION.*RATIONALE FOR SURGERY LEFT BREAST*(?P<capture>(?:(?!(?i)PREOPERATIVE EVALUATION.*)[\s\S])+)"
            left_breast = extract_section_regex_laterality(left_regex)
            # https://regex101.com/r/rdPUIj/1
            right_regex = r"(?i)PREOPERATIVE EVALUATION.*RATIONALE FOR SURGERY RIGHT BREAST*(?P<capture>(?:(?!(?i)PREOPERATIVE EVALUATION.*RATIONALE FOR SURGERY LEFT BREAST)[\s\S])+)"
            right_breast = extract_section_regex_laterality(right_regex)
        return extract_synoptic_operative_report(left_breast, "left") + extract_synoptic_operative_report(
            right_breast, "right")

    # https://regex101.com/r/kEj3Fs/1
    # https://regex101.com/r/HIXlrr/1
    preoperative_rational_regex = [
        (capture_double_regex(["PREOPERATIVE ", " RATIONAL", " ", "FOR SURGERY"], ["OPERATIVE DETAILS", " ", "BREAST"]),
         ""),
        (capture_double_regex(["Indication"], ["Breast procedure"]), "indication")
    ]

    # https://regex101.com/r/YHZjIP/1
    # https://regex101.com/r/dTJdh4/1
    operative_breast_regex = [
        (capture_double_regex(["OPERATIVE DETAILS", " ", "BREAST"], ["OPERATIVE details", " ", "AXILLA"]), ""),
        (capture_double_regex(["Breast procedure"], ["Axillary procedure"]), "breast procedure")
    ]

    # https://regex101.com/r/0cVC20/1
    # https://regex101.com/r/Ew5DMN/1
    operative_axilla_regex = [
        (capture_double_regex(["OPERATIVE DETAILS", " ", "AXILLA"], ["PROCEDURE COMPLETION"]), ""),
        (capture_double_regex(["Axillary procedure"], ["Unplanned events"]), "axillary procedure")
    ]

    preoperative_rational = extract_section(preoperative_rational_regex)
    operative_breast = extract_section(operative_breast_regex)
    operative_axilla = extract_section(operative_axilla_regex)

    # preoperative_rational = extract_preoperative_rational()
    # operative_breast = extract_breast_operative()
    # operative_axilla = extract_axilla_operative()

    if len(preoperative_rational) > 1:
        return split_report_find_left_right()

    return [({"preoperative rational": preoperative_rational,
              "operative breast details": operative_breast,
              "operative axilla details": operative_axilla,
              "laterality": lat if lat != "" else extract_laterality()}, lat)]


def clean_up_reports(emr_text: List[Report]) -> List[Report]:
    """
    Wrapper function to clean up list of reports
    :param emr_text:              list of reports that is currently not sorted or filtered
    :return cleaned_reports:      returns list of reports that have been separated into preoperative breast, operative breast and operative axilla
    """
    cleaned_reports = []
    for study in emr_text:
        text = study.report
        cleaned_pdf = extract_synoptic_operative_report(text)
        for cleaned_report in cleaned_pdf:
            report_info = cleaned_report[0]
            cleaned_reports.append(Report(report=text,
                                          report_id=str(study.report_id) + cleaned_report[1][0].upper() if len(
                                              cleaned_report[1]) > 0 else str(study.report_id) + cleaned_report[1],
                                          preoperative_breast=report_info["preoperative rational"],
                                          operative_breast=report_info['operative breast details'],
                                          operative_axilla=report_info['operative axilla details'],
                                          laterality=report_info['laterality']))
    return cleaned_reports
