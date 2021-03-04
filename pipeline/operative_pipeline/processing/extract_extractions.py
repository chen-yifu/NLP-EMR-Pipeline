import re
import string
from typing import List, Dict

from pipeline.util.regex_tools import synoptic_capture_regex, export_operative_synoptic_regex, \
    export_generic_negative_lookahead
from pipeline.util.report import Report
from pipeline.util.utils import import_pdf_human_cols_as_dict, get_full_path

table = str.maketrans(dict.fromkeys(string.punctuation))


def clean_up_txt(txt: str) -> str:
    """
    Removes punctuation and lowers all the letters.

    :param txt:
    :return:
    """
    cleaned_txt = txt.lower().translate(table).strip()
    return " ".join([v for v in cleaned_txt.split() if len(v) > 1])


def remove_nums(txt: str) -> str:
    """
    Removes numbers because there should not be any numbers in operative reports.

    :param txt:
    :return:
    """
    return " ".join([l for l in txt.split() if l.isalpha()])


def replace_is_with_colon(txt: str) -> str:
    """
    Replaces is with :, which is seen in some reports .

    :param txt:
    :return:
    """
    if "is" in txt and txt[-1] == ".":
        return " ".join([word if word != "is" else ":" for word in txt.split()])
    return txt


def clean_up_txt_list(uncleaned_txt: List[str]) -> List[str]:
    """
    Removes punctuation and other info like dates and pages numbers.

    :param uncleaned_txt:
    :return:
    """
    # need a way to keep n/a
    keep_na_list = ["na" if v.lower() == "n/a" else v for v in uncleaned_txt]
    remove_spaces_list = [v for v in keep_na_list if v.strip() != '']
    remove_is_list = [replace_is_with_colon(v) for v in remove_spaces_list]
    return [v for v in remove_is_list if
            "\\" not in v and v != "\x0c" and "2020" not in v and "page" not in v.lower()]


def general_extraction_per_report(unfiltered_str: str) -> dict:
    """
    Separates the string into col val pairs based on a colon.

    :param unfiltered_str:      string that represents one report
    :return:
    """
    unfiltered_extractions = {}
    lines = clean_up_txt_list(unfiltered_str.split('\n')) + ["buffer"]
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


def clean_pairs(filtered_pairs: Dict[str, str]) -> Dict[str, str]:
    for key, val in filtered_pairs.items():
        splited = val.splitlines()
        split_by_newline = " ".join([splited[0]] + [l for l in splited[1:] if len(l) > 1 and ":" not in l])
        strip_stuff = [w.strip().translate(table).lower() for w in split_by_newline.split()]
        strip_not_alpha = " ".join([w for w in strip_stuff if w.isalpha() and len(w) > 1])
        filtered_pairs[key] = strip_not_alpha
    return filtered_pairs


def get_extraction_via_regex(unfiltered_str: str) -> dict:
    generic_extraction = re.compile(export_generic_negative_lookahead)
    synoptic_report_regex = re.compile(export_operative_synoptic_regex)
    generic_pairs = [(m.groupdict()) for m in generic_extraction.finditer(unfiltered_str)]
    pairs = [(m.groupdict()) for m in synoptic_report_regex.finditer(unfiltered_str)]
    filtered_generic_pairs = {}
    for unfiltered_dict in generic_pairs:
        unfiltered_dict = {k: v for k, v in unfiltered_dict.items() if v is not None}
        filtered_generic_pairs.update(unfiltered_dict)
    cleaned_generic_pairs = clean_pairs(filtered_generic_pairs)

    filtered_pairs = {}
    for unfiltered_dict in pairs:
        unfiltered_dict = {k: v for k, v in unfiltered_dict.items() if v is not None}
        filtered_pairs.update(unfiltered_dict)
    cleaned_pairs = clean_pairs(filtered_pairs)
    print("generic")
    print(generic_pairs)
    print("specific")
    print(cleaned_pairs)


def get_general_extractions(list_reports: List[Report]) -> List[Report]:
    """
    Gets all the column:value pairs out of the report

    :param list_reports:      list of reports, in one large string
    :return:
    """

    for study in list_reports:
        raw_extractions = study.text
        get_extraction_via_regex(raw_extractions)
        study.extractions = general_extraction_per_report(raw_extractions)
        print("old\n" + str(study.extractions))
    return list_reports
