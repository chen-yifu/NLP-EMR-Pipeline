import re
import string
from typing import Tuple

table = str.maketrans(dict.fromkeys(string.punctuation))


# todo: be able to clean colons
def cleanse_column(col: str, is_text: bool = False) -> Tuple[str, str]:
    """
    cleanse the column by removing "-" and ":"

    :param is_text:
    :param col:      raw column
    :return:         cleansed column
    """
    col = re.sub(r"^\s*-\s*", "", col)  # remove "-"
    col = re.sub(r":\s*$", "", col)  # remove ":"
    colon_i = col.find(":")
    col = col[:colon_i] if colon_i != -1 else col
    val = col[colon_i + 1:] if colon_i != -1 else ""
    col = " ".join(col.translate(table).lower().strip().split())
    if is_text:
        col = " ".join([w for w in col.split() if w.isalpha()]).lower().strip()
        return col, val
    return col.strip().lower(), val


def remove_new_line_if_colon_present(s: str):
    """
    - When regex is contained capture, it may include information we do not want. For example ->
    column : value \n
    column1 : value \n
    colunm2: value

    - If we decide to capture everything from column to column2 the resulting phrase is ->
    value \n
    column1 : value \n
    colunm

    - This function will strip the phrase to by checking if the next new line contains a colon or not ->
    value

    - Another example ->
    column : value \n
    value value value \n
    colunm2: value

    - becomes ->
    value \n
    value value value

    :param s:  the string you want to clean
    :return:   cleaned string
    """
    split_by_newline = s.split("\n")
    val = split_by_newline[0] + " "
    for line in split_by_newline[1:]:
        if ":" not in line:
            val += line + " "
        else:
            return val
    return val


def cleanse_value(val: str, is_text: bool = False, function=None) -> str:
    """
    Cleanse the captured value according to whether it is text or numerical
    TEXT: removes all punctuation and lowers everything and removes single letters and strips all spaces
    NUMERICAL: only removes colons if the colon is in a position like this -> : value and strips all spaces

    :param is_text:
    :param function:       function to process the value if you do not want it to be cleaned
    :param val:            raw value
    :return:               cleansed value
    """
    if is_text:
        cleaned_val = remove_new_line_if_colon_present(val)
        cleaned_val = cleaned_val.strip().lower().replace("-", " ").replace(".", "")
        return " ".join([w for w in cleaned_val.split() if len(w) > 1])
    colon_index = val.find(":")
    if colon_index != -1:
        val = val[colon_index + 1:]
    val = re.sub(r":\s*$", "", val)  # remove ":"
    return function(val) if function else val.replace("\n", " ").strip()
