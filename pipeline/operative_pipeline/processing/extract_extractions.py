import string
from typing import List

from pipeline.util.report import Report

table = str.maketrans(dict.fromkeys(string.punctuation))


def clean_up_txt(txt: str) -> str:
    """
    :param txt:
    :return:
    """
    cleaned_txt = txt.lower().translate(table).strip()
    return " ".join([v for v in cleaned_txt.split() if len(v) > 1])


def remove_nums(txt: str) -> str:
    """
    :param txt:
    :return:
    """
    return " ".join([l for l in txt.split() if l.isalpha()])


def replace_is_with_colon(txt: str) -> str:
    """
    :param txt:
    :return:
    """
    if "is" in txt and txt[-1] == ".":
        return " ".join([word if word != "is" else ":" for word in txt.split()])
    return txt


def clean_up_txt_list(uncleaned_txt: List[str]) -> List[str]:
    """
    :param uncleaned_txt:
    :return:
    """
    # need a way to keep n/a
    keep_na_list = ["na" if v.lower() == "n/a" else v for v in uncleaned_txt]
    remove_spaces_list = [v for v in keep_na_list if v.strip() != '']
    remove_is_list = [replace_is_with_colon(v) for v in remove_spaces_list]
    return [v for v in remove_is_list if
            "\\" not in v and v != "\x0c" and "2020" not in v and "page" not in v.lower()]


def general_extraction_per_subsection(unfiltered_str: list) -> dict:
    """
    :param unfiltered_str:
    :return:
    """
    unfiltered_extractions = {}
    for subsection in unfiltered_str:
        lines = clean_up_txt_list(subsection.split('\n')) + ["buffer"]
        len_subsection = len(lines)
        index = 0
        rsf = ""
        curr_col = ""
        while index < len_subsection - 1:
            curr_line = lines[index]
            next_line = lines[index + 1]
            colon_curr = curr_line.find(":")
            colon_next = next_line.find(":")
            # if both are not -1: this means both are col:val
            if colon_curr != -1 and colon_next != -1:
                unfiltered_extractions[remove_nums(clean_up_txt(curr_line[0:colon_curr]))] = clean_up_txt(
                    curr_line[colon_curr + 1:])
            # if current is negative -1 and next is positive
            elif colon_curr == -1 and colon_next != -1:
                rsf += " " + curr_line
                unfiltered_extractions[remove_nums(clean_up_txt(curr_col))] = clean_up_txt(rsf)
                rsf = ""
                curr_col = ""
            # current is not -1 and if next is negative -1
            elif colon_curr != -1 and colon_next == -1:
                curr_col = curr_line[0:colon_curr]
                rsf += curr_line[colon_curr + 1:]
            # both are -1
            elif colon_curr == -1 and colon_next == -1:
                rsf += " " + curr_line
            # increment list lmao
            index += 1
        if rsf != "" and curr_col != "":
            unfiltered_extractions[remove_nums(clean_up_txt(curr_col))] = clean_up_txt(
                rsf)
    return unfiltered_extractions


def get_general_extractions(list_reports: List[Report]) -> List[Report]:
    """
    :param list_reports:
    :return:
    """

    for study in list_reports:
        raw_preoperative = study.preoperative_breast
        raw_operative_breast = study.operative_breast
        raw_operative_axilla = study.operative_axilla
        study.preoperative_breast = general_extraction_per_subsection(raw_preoperative)
        study.operative_breast = general_extraction_per_subsection(raw_operative_breast)
        study.operative_axilla = general_extraction_per_subsection(raw_operative_axilla)
    return list_reports