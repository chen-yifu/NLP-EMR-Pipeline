import re
from typing import List, Tuple, Union, Dict

from pipeline.util.import_tools import import_pdf_human_cols, table
from pipeline.util.utils import import_pdf_human_cols_as_dict, get_full_path


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


def convert_to_regex(list_of_words: List[Union[str, List[str]]]) -> str:
    """
    Helper function to convert a string into regex

    :param list_of_words:
    :return:
    """
    result = ""
    for word in list_of_words[:-1]:
        if isinstance(word, list):
            result += "".join([add_asterisk(or_word) + "|" for or_word in word])
        elif word == " ":
            result += " "
        else:
            result += add_asterisk(word) + ".*"

    last_word = list_of_words[-1]
    if isinstance(last_word, list):
        result += "".join([add_asterisk(or_word) + "|" for or_word in last_word[:-1]]) + add_asterisk(last_word[-1])
    else:
        result += add_asterisk(last_word)
    return result


def add_asterisk(word: str) -> str:
    """
    Adds asterisk where appropriate
    :param word:
    :return:
    """
    letters = list(word)
    result = ""
    for index in range(len(letters) - 1):
        curr = letters[index]
        next = letters[index + 1]
        if curr != " " and next != " ":
            curr += " *"
        result += curr
    result += letters[-1]
    if letters[0] == "-" and letters[1] == " ":
        result = "-+ *" + result[2:]
    elif letters[0] == " ":
        result = " *" + result[1:]
    elif letters[0] == "-":
        result = "-+" + result[1:]
    return re.sub(' +', ' ', result)


def capture_laterality() -> str:
    return "yeet"


def to_camel_or_underscore(col: str) -> str:
    col = col.strip()
    camelCase = ""
    if len(col) > 32:
        skip_curr = False
        for index in range(len(col)):
            if not skip_curr and index < 32:
                curr_l = col[index]
                try:
                    next_l = col[index + 1]
                except IndexError:
                    next_l = ""
                if curr_l == " ":
                    camelCase += next_l.upper()
                    skip_curr = True
                else:
                    camelCase += curr_l
                    skip_curr = False
            else:
                skip_curr = False
                continue
        return camelCase.translate(table)
    return col.lower().replace(" ", "_").translate(table)


def prepend_punc(str_with_punc: str) -> str:
    fixed_str = ""
    punc = ("?", "(", ")")
    for l in str_with_punc:
        if l in punc:
            fixed_str += "\\" + l + "*"
        else:
            fixed_str += l
    return fixed_str


def synoptic_capture_regex(columns: Dict[str, List[str]], ignore_caps: bool = True,
                           capture_only_first_line: bool = True, last_word: str = "",
                           add_generic_capture: bool = False) -> Tuple[str, dict]:
    col_keys = list(columns.keys())
    length_of_keys = len(col_keys)
    template_regex = r""
    mappings_to_regex_vals = {}
    cols_to_avoid = ""
    for index in range(length_of_keys - 1):
        curr_cols = columns[col_keys[index]]
        next_cols = columns[col_keys[index + 1]]
        curr_col = prepend_punc("|".join(curr_cols))
        next_col = prepend_punc("|".join(next_cols))
        end_cap = ".+)"
        variablefied = to_camel_or_underscore(curr_col)
        cols_to_avoid += curr_col + "|"
        if not capture_only_first_line:
            end_cap = r"((?!{next_col})[\s\S])*)".format(next_col=next_col + "")
        front_cap = r"{curr_col}(?P<{curr_col_no_space}>".format(
            curr_col=curr_col if len(curr_cols) == 1 else "(" + curr_col + ")",
            curr_col_no_space=variablefied)
        template_regex += front_cap + end_cap + "|"
        mappings_to_regex_vals[variablefied] = curr_cols

    # do last one
    last_one = prepend_punc(":|".join(columns[col_keys[-1]]))
    if last_word == "":
        template_regex += r"{last_one}(?P<{last_no_space}>.+)".format(last_one=last_one,
                                                                      last_no_space=to_camel_or_underscore(last_one))
    else:
        end_cap = r"((?!{next_col})[\s\S])*)".format(next_col=last_word)
        front_cap = r"{curr_col}:(?P<{curr_col_no_space}>".format(curr_col=last_one,
                                                                  curr_col_no_space=to_camel_or_underscore(last_one))
        template_regex += front_cap + end_cap

    if add_generic_capture:
        template_regex += "|" + r"(?P<column>[^-:]*(?=:)):(?P<value>(?:(?!{cols_to_avoid})[\s\S])*)".format(
            cols_to_avoid=cols_to_avoid)

    return "(?i)" + template_regex if ignore_caps else template_regex, mappings_to_regex_vals


def generic_capture_regex(negative_lookahead: str) -> str:
    return r"(?i)(?P<column>[^-:]*(?=:)):(?P<value>(?:(?!{negative_lookahead})[\s\S])*)".format(
        negative_lookahead=negative_lookahead)


def capture_double_regex(starting_word: List[Union[str, List[str]]],
                         ending_word: List[Union[str, List[str]]],
                         capture_first_line: bool = False,
                         capture_last_line: bool = False,
                         ignore_capials: bool = True) -> str:
    """
    for spaces:
    ["cat dog"],["fish"], True ->  r"(?i)c *a *t d *o *g(?P<capture>(?:(?!f *i *s *h.*)[\s\S])+)"
    ["cat dog"],["fish"], True ->  r"(?i)c *a *t d *o *g.+(?P<capture>(?:(?!f *i *s *h)[\s\S])+)"
    ["cat dog"],["fish"] ->        r"(?i)c *a *t d *o *g(?P<capture>(?:(?!f *i *s *h)[\s\S])+)"
    ["cat"," ","dog"],["fish"] ->  r"(?i)c *a *t.* d *o *g(?P<capture>(?:(?!f *i * s *h)[\s\S])+)"
    ["cat "," ","dog"],["fish"] -> r"(?i)c *a *t .* d *o *g(?P<capture>(?:(?!f *i * s *h)[\s\S])+)"
    ["cat"," dog"],["fish"] ->     r"(?i)c *a *t.* *d *o *g(?P<capture>(?:(?!f *i * s *h)[\s\S])+)"

    :param ignore_capials:          whether or not you want be capital sensitive
    :param capture_last_line:       whether or not you want your regex to capture everything after the last word
    :param capture_first_line:      whether or not you want your regex to capture everything after the first word
    :param starting_word:           the first word to look for
    :param ending_word:             the word to stop at
    :return:
    """
    modified_starting_word = convert_to_regex(starting_word)
    if capture_first_line:
        modified_starting_word += ".+"
    modified_ending_word = convert_to_regex(ending_word)
    if capture_last_line:
        modified_ending_word += ".*"
    modified_regex = r"{capitalize}{starting_word}(?P<capture>(?:(?!{ending_word})[\s\S])+)".format(
        capitalize="(?i)" if ignore_capials else "",
        starting_word=modified_starting_word,
        ending_word=modified_ending_word)
    return modified_regex


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
# https://regex101.com/r/XWffCF/1
export_operative_synoptic_regex, export_mappings_to_regex_vals = synoptic_capture_regex(
    import_pdf_human_cols_as_dict(get_full_path("data/utils/operative_column_mappings.csv"),
                                  skip=["Immediate Reconstruction Mentioned",
                                        "Laterality"]),
    capture_only_first_line=False)

# https://regex101.com/r/XWffCF/1
# print(synoptic_capture_regex(import_pdf_human_cols_as_dict("../../data/utils/operative_column_mappings.csv",
#                                                            skip=["Immediate Reconstruction Mentioned", "Laterality"]),
#                              capture_only_first_line=False))

# https://regex101.com/r/aIH7z7/1
export_generic_negative_lookahead = generic_capture_regex("[0-9]+\\.|\n+\\. .+")

# https://regex101.com/r/lLvPFh/1
export_single_generic = generic_capture_regex("^\\n")
