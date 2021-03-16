"""
helper regex functions
"""
import random
import re
from typing import List, Tuple, Union, Dict
from pipeline.util.import_tools import table


def regex_extract(regex: str, uncleaned_txt: str) -> list:
    return re.findall(re.compile(regex), uncleaned_txt)


def extract_section(regexs: List[Tuple[str, str]], uncleaned_txt: str) -> list:
    """
    General function that takes in a list of regex and returns the first one that returns a result

    :param uncleaned_txt:     string to use regex on
    :param regexs:            list of tuple(regex,to_append) and the list should be entered in priority
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


def add_asterisk_and_ors(list_of_words: List[Union[str, List[str]]]) -> str:
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


def to_camel_or_underscore(col: str, seen: set) -> Tuple[str, set]:
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
        camelCase = camelCase.translate(table)
    else:
        camelCase = col.lower().translate(table).replace(" ", "_")
    if camelCase not in seen:
        seen.add(camelCase)
        return camelCase, seen
    else:
        while camelCase in seen:
            camelCase += str(random.randint(0, 9))
        seen.add(camelCase)
        return camelCase, seen


def make_punc_regex_literal(str_with_punc: str) -> str:
    fixed_str = ""
    punc = ("?", "(", ")", "\\", "/")
    for l in str_with_punc:
        if l in punc:
            fixed_str += "\\" + l + "*"
        else:
            fixed_str += l
    return fixed_str


def synoptic_capture_regex(columns: Dict[str, List[str]], ignore_caps: bool = True, anchor_list: list = [],
                           capture_only_first_line: bool = True, anchor: str = "", is_anchor: bool = False,
                           last_word: str = "", list_multi_line_cols: list = [], no_anchor_list: list = [],
                           contained_capture_list: list = [], seperator: str = ":", no_sep_list: list = [],
                           add_sep: bool = False, sep_list: list = []) -> Tuple[str, Dict[str, List[str]]]:
    col_keys = list(columns.keys())
    template_regex = r""
    mappings_to_regex_vals = {}
    seen = set()
    for index in range(len(col_keys) - 1):
        col_key = col_keys[index].lower()

        # checking if we should contain, add anchor and add seperator
        is_contained_capture = col_key in contained_capture_list
        dont_add_anchor, add_anchor = col_key in no_anchor_list, col_key in anchor_list
        dont_add_seperator, add_seperater = col_key not in no_sep_list, col_key in sep_list

        curr_cols = columns[col_keys[index]]

        # adding seperator into regex
        if add_sep and not dont_add_seperator or add_seperater:
            curr_cols = [c + seperator for c in curr_cols if c not in no_sep_list]

        next_cols = columns[col_keys[index + 1]]

        # adding symbolic or between words and making punctuation regexible
        curr_col = make_punc_regex_literal("|".join(curr_cols))
        next_col = make_punc_regex_literal("|".join(next_cols))

        # this is for only capturing a single line
        end_cap = ".+)"

        # column has been converted to variable and seen is list of already used variable names
        # regex variable names must be unique
        variablefied, seen = to_camel_or_underscore(curr_col, seen)

        # if we want to capture up to a keyword
        if not capture_only_first_line or is_contained_capture:
            end_cap = r"((?!{next_col})[\s\S])*)".format(next_col=next_col + "")
        # if we want to "anchor" the word to the start of the document
        if is_anchor and not dont_add_anchor or add_anchor:
            capture_anchor = r"{anchor}({curr_col})".format(curr_col=curr_col, anchor=anchor)
            front_cap = r"{capture_anchor}(?P<{curr_col_no_space}>".format(
                capture_anchor=capture_anchor, curr_col_no_space=variablefied)
        else:
            front_cap = r"{curr_col}(?P<{curr_col_no_space}>".format(
                curr_col=curr_col if len(curr_cols) == 1 else "(" + curr_col + ")",
                curr_col_no_space=variablefied)
        template_regex += front_cap + end_cap + "|"

        # adding variable name so we can use for later
        mappings_to_regex_vals[variablefied] = curr_cols

    # do last column
    last_col = col_keys[-1].lower()
    if add_sep and last_col not in no_sep_list or last_col in sep_list:
        last_col = [c + seperator for c in columns[col_keys[-1]] if c not in no_sep_list]
    else:
        last_col = columns[col_keys[-1]]
    last_one = make_punc_regex_literal("|".join(last_col))
    last_one_variable, seen = to_camel_or_underscore(last_one, seen)
    if last_word == "":
        template_regex += r"{last_one}(?P<{last_no_space}>.+)".format(last_one=last_one,
                                                                      last_no_space=last_one_variable)
    else:
        end_cap = r"((?!{next_col})[\s\S])*)".format(next_col=last_word)
        front_cap = r"{curr_col}:(?P<{curr_col_no_space}>".format(curr_col=last_one,
                                                                  curr_col_no_space=last_one_variable)
        template_regex += front_cap + end_cap
    mappings_to_regex_vals[last_one_variable] = columns[col_keys[-1]]

    # this is for any columns that have the column on the first line and value on the second line
    if len(list_multi_line_cols) > 0:
        for col in list_multi_line_cols:
            col_var, seen = to_camel_or_underscore(col, seen)
            multi_line_regex = r"{column}\s*-*(?P<{col_var}>.+)".format(column=make_punc_regex_literal(col.lower()),
                                                                        col_var=col_var)
            template_regex += "|" + multi_line_regex
            mappings_to_regex_vals[col_var] = [col.lower()]

    return "(?i)" + template_regex if ignore_caps else template_regex, mappings_to_regex_vals


def generic_capture_regex(negative_lookahead: str) -> str:
    return r"(?i)(?P<column>[^-:]*(?=:)):(?P<value>(?:(?!{negative_lookahead})[\s\S])*)*".format(
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
    modified_starting_word = add_asterisk_and_ors(starting_word)
    if capture_first_line:
        modified_starting_word += ".+"
    modified_ending_word = add_asterisk_and_ors(ending_word)
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


# https://regex101.com/r/ppQb7E/1
# remove the ^ to remove the left anchor
export_generic_negative_lookahead = generic_capture_regex("^[0-9]+\\.|^\n+\\. .+")

# https://regex101.com/r/lLvPFh/1
export_single_generic = generic_capture_regex("^\\n")

# https://regex101.com/r/013vC1/1
# https://regex101.com/r/r4wOaZ/1
export_anchor_char = generic_capture_regex("^.+")
