import re
from typing import List, Tuple

from pipeline.util.utils import capture_double_regex

# regex patterns for operative reports
# https://regex101.com/r/kEj3Fs/1
# https://regex101.com/r/HIXlrr/1
preoperative_rational_regex = [(capture_double_regex(["PREOPERATIVE ", " RATIONAL", " ", "FOR SURGERY"],
                                                     ["OPERATIVE DETAILS", " ", "BREAST"]), ""),
                               (capture_double_regex(["Indication"], ["Breast procedure"]), "indication")]

# https://regex101.com/r/YHZjIP/1
# https://regex101.com/r/dTJdh4/1
operative_breast_regex = [
    (capture_double_regex(["OPERATIVE DETAILS", " ", "BREAST"], ["OPERATIVE DETAILS", " ", "AXILLA"]), ""),
    (capture_double_regex(["Breast procedure"], ["Axillary procedure"]), "breast procedure")]

# https://regex101.com/r/0cVC20/1
# https://regex101.com/r/Ew5DMN/1
operative_axilla_regex = [
    (capture_double_regex(["OPERATIVE DETAILS", " ", "AXILLA"], ["PROCEDURE COMPLETION"]), ""),
    (capture_double_regex(["Axillary procedure"], ["Unplanned events"]), "axillary procedure")]

# laterality regex
# https://regex101.com/r/AE3qZs/1
# https://regex101.com/r/rdPUIj/1
right_operative_report = [(capture_double_regex(["Right breast:"], ["Right breast:"]), ""),
                          (capture_double_regex(["PREOPERATIVE EVALUATION", "RATIONALE FOR SURGERY RIGHT BREAST"],
                                                ["PREOPERATIVE EVALUATION", "RATIONALE FOR SURGERY LEFT BREAST"]),
                           "PREOPERATIVE RATIONALE FOR SURGERY")]

# https://regex101.com/r/kT4aT7/1
# https://regex101.com/r/l760jr/1
left_operative_report = [(capture_double_regex(["Left breast:"], ["Right breast:"]), ""),
                         (capture_double_regex(["PREOPERATIVE EVALUATION", "RATIONALE FOR SURGERY LEFT BREAST"],
                                               ["PREOPERATIVE EVALUATION"], capture_last_line=True),
                          "PREOPERATIVE RATIONALE FOR SURGERY")]

# regex patterns for pathology reports
# https://regex101.com/r/2dxpIX/1
pathology_synoptic_regex = [(capture_double_regex(["Synoptic Report: "], ["- End of Synoptic"], capture_first_line=True,
                                                  ignore_capials=False), "")]

export_operative_regex = [preoperative_rational_regex, operative_breast_regex, operative_axilla_regex]
export_pathology_regex = [pathology_synoptic_regex]


def regex_extract(regex: str, uncleaned_txt: str) -> list:
    return re.findall(re.compile(regex), uncleaned_txt)


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