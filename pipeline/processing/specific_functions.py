import re
from typing import Dict, List

import pandas as pd
from nltk import edit_distance

from pipeline.utils.report import Report


def categories(stages_path: str) -> dict:
    """
    :param stages_path: str
    :return categories: dict
    """
    categories_csv = pd.read_csv(stages_path)
    return {"T": [t for t in categories_csv["T"].tolist() if "T" in str(t)],
            "N": [n for n in categories_csv["N"].tolist() if "N" in str(n)],
            "M": [m for m in categories_csv["M"].tolist() if "M" in str(m)]}


def find_category(index: int, category_dict: list, stage: str) -> (str, int):
    """
    given a stage, compute the edit distance for it based on the category
    :param category_dict: dict
    :param index: str                   current index
    :param stage: str                   the original word
    :return edited_stage_category: str  the edited stage that it most likely the closest via edit distance
    :return to_skip: int                how much overlap there is, return  [mpT1a ]pN1mi
                                                                           [mpTla] pNlmi -> skip 1
    """
    if index + 4 <= len(stage):
        supposed_category = stage[index:index + 4].replace("l", "1").replace("O", "0")
        for category in category_dict:
            if edit_distance(supposed_category, category) == 0:
                return category + " ", len(supposed_category) - 1
    if index + 3 <= len(stage):
        supposed_category = stage[index:index + 3].replace("l", "1").replace("O", "0")
        for category in category_dict:
            if edit_distance(supposed_category, category) == 0:
                return category + " ", len(supposed_category) - 1
    # case 2: T1a, etc
    # take two more letters and try the edit distance, if any are 1, then return
    if index + 2 <= len(stage):
        supposed_category = stage[index:index + 2].replace("l", "1").replace("O", "0")
        for category in category_dict:
            if edit_distance(supposed_category, category) == 0:
                return category + " ", len(supposed_category) - 1
    # case 1: T0, T1, MX
    if index + 1 <= len(stage):
        supposed_category = stage[index:index + 1].replace("l", "1").replace("O", "0")
        for category in category_dict:
            if edit_distance(supposed_category, category) == 0:
                return category + " ", len(supposed_category) - 1
    # case 3: none of the matches
    return stage[index], 0


def find_pathologic_stage(stage: str, paths: Dict[str,str]) -> str:
    """
    :param paths:
    :param stage: str
    :return edited_stage: str
    """
    path_to_stages = paths["stages"]
    stage = stage.replace("\n", " ").strip()
    categories_dict = categories(path_to_stages)
    edited_stage = ""
    to_skip = 0
    for index, letter in enumerate(stage):
        if letter == "T":  # tumor
            category_skip = find_category(index, categories_dict["T"], stage)
            edited_stage += category_skip[0]
            to_skip = category_skip[1]
        elif letter == "N":
            category_skip = find_category(index, categories_dict["N"], stage)
            edited_stage += category_skip[0]
            to_skip = category_skip[1]
        elif letter == "M":
            category_skip = find_category(index, categories_dict["M"], stage)
            edited_stage += category_skip[0]
            to_skip = category_skip[1]
        elif to_skip != 0:
            to_skip -= 1
            continue
        else:
            edited_stage += letter
    return ' '.join(edited_stage.split())


def duplicate_lymph_nodes(report: str, result: dict, generic_pairs: dict):
    if (result["number of lymph nodes examined"] != ""):
        result["number of lymph nodes examined (sentinel and nonsentinel)"] = result["number of lymph nodes examined"]
        del result["number of lymph nodes examined"]


def find_num_foci(report: str, result: dict, generic_pairs: dict):
    if result["number of foci"] == "":
        result["number of foci"] = result["tumour focality"]


def in_situ(report: str, result: dict, generic_pairs: dict):
    if result["histologic type"].lower() == "ductal carcinoma in situ":
        # if in situ type is not found, use histologic type
        if result["in situ component type"] == "":
            result["in situ component type"] = result["histologic type"]
        # if in situ component is not found, use histologic type
        if result["in situ component"] == "":
            result["in situ component"] = result["histologic type"]


def filter_report(reports: List[Report], column: str, value: List[str], report_ending: str) -> List[Report]:
    cleaned_reports = []
    skip = False
    for index, report in enumerate(reports):
        extractions = report.extractions
        if column in extractions.keys() and not skip:
            if extractions[column] not in value:
                cleaned_reports.append(report)
            elif extractions[column] in value:
                prev_index = index - 1 if index - 1 > 0 else False
                next_index = index + 1 if index + 1 < len(reports) else False
                prev_report_id = "".join(
                    [l for l in list(reports[prev_index].report_id) if not l.isalpha()]) if prev_index else -1
                next_report_id = "".join(
                    [l for l in list(reports[next_index].report_id) if not l.isalpha()]) if prev_index else -1
                curr_id = "".join([l for l in list(report.report_id) if not l.isalpha()])
                if curr_id == prev_report_id:
                    prev_report = reports[prev_index]
                    prev_report.report_id = curr_id + report_ending[:-4]
                elif curr_id == next_report_id:
                    next_report = reports[next_index]
                    next_report.report_id = curr_id + report_ending[:-4]
                    cleaned_reports.append(next_report)
                    skip = True
        else:
            skip = False
    return cleaned_reports


def no_lymph_node(report: str, result: dict, generic_pairs: dict):
    spaceless_synoptic_report = report.replace(" ", "")
    if "Nolymphnodespresent" in spaceless_synoptic_report:
        result["number of lymph nodes examined (sentinel and nonsentinel)"] = "0"
        result["number of sentinel nodes examined"] = "0"
        result["micro / macro metastasis"] = None
        result["number of lymph nodes with micrometastases"] = None
        result["number of lymph nodes with macrometastases"] = None
        result["size of largest metastatic deposit"] = None


def no_dcis_extent(report: str, result: dict, generic_pairs: dict):
    if "dcis extent" not in result.keys() and "dcis extent" not in generic_pairs.keys():
        try:
            result["dcis extent"] = generic_pairs["dcis estimated size"]
        except:
            pass


def negative_for_dcis(report: str, result: dict, generic_pairs: dict):
    cleaned_report = report.lower().strip()
    match1 = re.search(r"(?i)- *N *e *g *a *t *i *v *e  *f *o *r  *D *C *I *S", cleaned_report)

    if match1:
        result["distance from closest margin"] = None
        result["closest margin"] = None
        try:
            result["distance of dcis from closest margin"] = generic_pairs["distance from closest margin"]
        except KeyError:
            pass
        try:
            result["closest margin1"] = generic_pairs["closest margin"]
        except KeyError:
            pass


def do_nothing(value: str, encodings_so_far: Dict[str, str] = {}) -> str:
    """

    :param value:
    :param encodings_so_far:
    :return:
    """
    if "l" in value and len(value.strip()) < 3:
        return value.replace("l", "1")
    return value


def nottingham_score(encodings_so_far: Dict[str, str] = {}) -> str:
    """
    :param encodings_so_far:
    :return:
    """
    glandular = str(encodings_so_far["Glandular Differentiation"])
    nuclear_p = str(encodings_so_far["Nuclear Pleomorphism"])
    mitotic = str(encodings_so_far["Mitotic Rate"])
    try:
        glandular = int(glandular)
    except Exception:
        if "3" in glandular:
            glandular = 3
        elif "2" in glandular:
            glandular = 2
        elif "1" in glandular:
            glandular = 1
        else:
            glandular = 0
    try:
        nuclear_p = int(nuclear_p)
    except Exception:
        if "3" in nuclear_p:
            nuclear_p = 3
        elif "2" in nuclear_p:
            nuclear_p = 2
        elif "1" in nuclear_p:
            nuclear_p = 1
        else:
            nuclear_p = 0
    try:
        mitotic = int(mitotic)
    except Exception:
        if "3" in mitotic:
            mitotic = 3
        elif "2" in mitotic:
            mitotic = 2
        elif "1" in mitotic:
            mitotic = 1
        else:
            mitotic = 0

    score = glandular + nuclear_p + mitotic

    return str(score) if score > 0 else ""


def process_mm_val(value: str, encodings_so_far: Dict[str, str] = {}) -> str:
    """
    mm
    :param value:        unprocessed data
    """
    value = str(value).lower().replace(" ", "")
    # regex demo: https://regex101.com/r/FkMTtr/1
    regex = re.compile(r"([\<\>]? ?\d+\.?\d*)")
    matches = re.findall(regex, value)
    if matches:
        return matches[0]


def number_of_foci(num_foci: str, encodings_so_far: Dict[str, str] = {}) -> str:
    focality = encodings_so_far["Tumour Focality"]
    if focality == "1":
        return "1"
    raw = str(num_foci)
    value = str(num_foci).lower().replace(" ", "")
    regex = re.compile(r"(\d+)")
    matches = re.findall(regex, value)
    if "single" in value:
        return "1"
    elif matches:
        return matches[0]
    elif "cannotbedetermined" in value:
        return "cannot be determined"


def tumour_site(value: str, encodings_so_far: Dict[str, str] = {}) -> str:
    """
    clock orientation
    :param value:           unprocessed data
    """
    value_copy = str(value)
    value = str(value).lower().replace(" ", "")
    # if "mm" is in value, the correct column is tumour size, not tumour site
    if "mm" in value:
        return ""
    regex_full = re.compile(r"(\d+:\d+)")  # 12:00
    regex_part = re.compile(r"(\d+)")  # 12 o' clock
    matches_full = re.findall(regex_full, value)
    matches_part = re.findall(regex_part, value)
    if matches_full:
        if len(matches_full[0]) == 4:
            value = "0" + matches_full[0]
        else:
            value = matches_full[0]
    elif matches_part:
        if len(matches_part[0]) == 1:
            value = str(matches_part[0]) + " o'clock"
        elif len(matches_part[0]) >= 2:
            value = str(matches_part[0]) + " o'clock"
            if int(matches_part[0]) > 12:
                value = ""
    else:
        value = value_copy
    return value


def archtectural_patterns(value: str, encodings_so_far: Dict[str, str] = {}) -> str:
    """
    :param encodings_so_far:
    :param value:      unprocessed data
    """
    value = str(value)
    regex = re.compile(r" {2,}")
    value = re.sub(regex, " ", value)
    if value != "nan":
        return value
    else:
        return ""


def immediate_reconstruction_mentioned(encodings_so_far: Dict[str, str] = {}) -> str:
    val_depends_on = encodings_so_far["Immediate Reconstruction Type"]
    return "0" if val_depends_on == "0" or val_depends_on == "" else "1"
