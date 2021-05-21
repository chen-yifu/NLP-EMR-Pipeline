"""
2021 Yifu (https://github.com/chen-yifu) and Lucy (https://github.com/lhao03)
This file includes code that encodes extractions based on the respective code book. Functions must
be in a certain form:

def function_name(value: str="", encodings_so_far: Dict[str, str] = {}):
    do stuff

value is the current string to be encoded
encodings_so_far are the encodings that have been processed so far
"""

import re
from typing import Dict


def nottingham_score(value: str = "", encodings_so_far: Dict[str, str] = {}) -> str:
    """
    :param value:
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


def process_mm_val(value: str = "", encodings_so_far: Dict[str, str] = {}) -> str:
    """
    mm
    :param encodings_so_far:
    :param value:
    """
    value = str(value).lower().replace(" ", "")
    # regex demo: https://regex101.com/r/FkMTtr/1
    regex = re.compile(r"([\<\>]? ?\d+\.?\d*)")
    matches = re.findall(regex, value)
    if matches:
        return matches[0]


def number_of_foci(value: str = "", encodings_so_far: Dict[str, str] = {}) -> str:
    """
    :param value:
    :param encodings_so_far:
    :return:
    """
    focality = encodings_so_far["Tumour Focality"]
    if focality == "1":
        return "1"
    raw = str(value)
    value = str(value).lower().replace(" ", "")
    regex = re.compile(r"(\d+)")
    matches = re.findall(regex, value)
    if "single" in value:
        return "1"
    elif matches:
        return matches[0]
    elif "cannotbedetermined" in value:
        return "cannot be determined"


def tumour_site(value: str = "", encodings_so_far: Dict[str, str] = {}) -> str:
    """
    clock orientation
    :param encodings_so_far:
    :param value:
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


def archtectural_patterns(value: str = "", encodings_so_far: Dict[str, str] = {}) -> str:
    """
    :param encodings_so_far:
    :param value:
    """
    value = str(value)
    regex = re.compile(r" {2,}")
    value = re.sub(regex, " ", value)
    if value != "nan":
        return value
    else:
        return ""


def immediate_reconstruction_mentioned(value: str = "", encodings_so_far: Dict[str, str] = {}) -> str:
    """
    :param value:
    :param encodings_so_far:
    :return:
    """
    val_depends_on = encodings_so_far["Immediate Reconstruction Type"]
    return "0" if val_depends_on == "0" or val_depends_on == "" else "1"
