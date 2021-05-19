"""
helper regex functions
"""
import random
import re
from typing import List, Tuple, Union, Dict
from pipeline.utils.column import Column
from pipeline.utils.import_tools import table


def regex_extract(regex: str, text: str) -> list:
    """
    Helper function to execute extraction based on inputted regex pattern.

    :param regex:           regular pattern you want to use on text
    :param text:            text to have extractions done on
    :return:
    """
    return re.findall(re.compile(regex), text)


def extract_section(regexs: List[Tuple[str, str]], text: str) -> list:
    """
    General function that takes in a list of regex and returns the first one that returns a result.

    :param text:          string to use regex on
    :param regexs:        list of tuple(regex,to_append) and the list should be entered in priority
    :return:              the first extraction to be found. If to_append is not "", then it will append that string to the found extraction. if no extraction is found, [] is returned
    """
    for regex, to_append in regexs:
        extraction_result = regex_extract(regex, text)
        if len(extraction_result) != 0:
            if to_append == "":
                return extraction_result
            result = to_append + extraction_result[0]
            return [result]
    return []


def add_asterisk_and_ors(list_of_words: List[Union[str, List[str]]]) -> str:
    """
    Helper function to convert a list of string into regular pattern with OR between the words.
    - [cat] becomes c * a * t
    - [cat,dog] becomes (c *a *t|d *o *g)
    :param list_of_words:   words you want to concat together with | (or)
    :return:                the regular pattern
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

    :param word: the string to be changed
    :return:  changed string
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
    """
    Since regular pattern needs variable names, we change the columns into variables names.
    Example:

    - indication -> indication (stays as is)
    - pathologic stage -> pathologic_stage (space is converted into _)
    - incision and its relation to tumour -> incisionAndItsRelationToTumour (if it is longer than 32 chars with spaces it becomes camelCase instead of underscore.

    :param col:          the column to change into a variable name
    :param seen:         set with previously generated variable names, regular pattern does not allow duplicate variable names
    :return:
    """
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
                elif not curr_l.isalpha():
                    continue
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
    """
    Changes punctuation in a word so regex pattern will interpret it literally.
    Example:
    - indication? -> indication\?

    :param str_with_punc:
    :return:
    """
    fixed_str = ""
    punc = ("?", "(", ")", "\\", "/")
    for l in str_with_punc:
        if l in punc:
            fixed_str += "\\" + l + "*"
        else:
            fixed_str += l
    return fixed_str


def synoptic_capture_regex(columns: Dict[str, Column], ignore_caps: bool = True, anchor_list: List[str] = [],
                           capture_till_end_of_val_list=[], stop_capture_at_end_of_value: bool = True, anchor: str = "",
                           is_anchor: bool = False, use_seperater_for_contained_capture: bool = True,
                           multi_line_cols_list: List[str] = [], no_anchor_list: List[str] = [],
                           contained_capture_list: List[str] = [], separator: str = ":", no_sep_list: List[str] = [],
                           add_sep: bool = False, sep_list: List[str] = []) -> Tuple[str, Dict[str, List[str]]]:
    """
    Based on a regex pattern template, turns a list of columns into a regex that can capture the values associated with
    those columns.

    :param use_seperater_for_contained_capture:  whether or not to use the separator as part of regular pattern
    :param capture_till_end_of_val_list:  columns that have their values on the same line (single value)
    :param columns:                       the columns that you want to capture
    :param ignore_caps:                   False if you want the regex to be case sensitive, True (default) otherwise: https://regex101.com/r/G44Egb/1
    :param anchor_list:                   list of columns you want to match to the start of the line.
    :param stop_capture_at_end_of_value:  If you know the value only spans one line, leave this as True. Otherwise change to False: https://regex101.com/r/xDrHz4/1
    :param anchor:                        What position is being matched before the column: https://regex101.com/r/JGWIKB/1
    :param is_anchor:                     Whether or not you want to match at the start of the line. Default is False.
    :param multi_line_cols_list:          Columns that you know have values that span two lines: https://regex101.com/r/pgzUuH/1
    :param no_anchor_list:                Columns you do not want to have the anchor
    :param contained_capture_list:        Columns you want the capture to be between columns: https://regex101.com/r/akxofC/1
    :param separator:                     The punctuation or letters that separates a column and value. Default is :
    :param no_sep_list:                   Columns which you do not want the separator to be used in the regex
    :param add_sep:                       Whether or not you want the separator to be included in the regex. Default is False.
    :param sep_list:                      Columns where you want the separator to be added to the regex.
    :return:                              A regex pattern
    """

    def process_columns_to_regex_str(cols: List[str]) -> str:
        """
        :param cols:
        """
        # adding separator into regex
        if add_sep and not dont_add_seperator or add_seperater:
            # ["col1","col2"] -> ["col1:","col2:"]
            cols = [c + separator for c in cols if c not in no_sep_list]
        cols_str = make_punc_regex_literal("|".join(cols))
        if len(cols) > 1:
            return "(" + cols_str + ")"
        return cols_str

    def create_regex_str(col: str, col_var: str, end_cap: str, front_cap: str = r"{col}(?P<{col_var}>",
                         no_or: bool = False) -> str:
        """
        Generic function to create a capture regular pattern. See examples in above links under synoptic_capture_regex

        :param no_or:     whether or not to add a OR (|) to the end of the regular pattern
        :param col:       column we are capturing
        :param col_var:   the column but as a variable, previously generated
        :param end_cap:   the end of the regular pattern, variations can be seen under synoptic_capture_regex
        :param front_cap: the front of the regular pattern, variations can be seen under synoptic_capture_regex
        :return:          regular pattern
        """
        front_cap = front_cap.format(col=col, col_var=col_var)
        return front_cap + end_cap if no_or else front_cap + end_cap + "|"

    col_keys = list(columns.keys())
    template_regex = r""
    mappings_to_regex_vals = {}
    seen = set()
    for index in range(len(col_keys) - 1):
        curr_col_key = col_keys[index].lower()  # grabs the human column name
        current_col = columns[col_keys[index]]  # grabs the associated pdf columns in Column object

        # checking if we should contain, add anchor and add seperator
        is_contained_capture = curr_col_key in contained_capture_list
        dont_add_anchor, add_anchor = curr_col_key in no_anchor_list, curr_col_key in anchor_list
        dont_add_seperator, add_seperater = curr_col_key not in no_sep_list, curr_col_key in sep_list
        single_line = curr_col_key in capture_till_end_of_val_list

        # all the columns we might use
        primary_curr_cols = current_col.primary_report_col
        alternative_curr_cols = current_col.alternative_report_col
        primary_next_cols = columns[col_keys[index + 1]].primary_report_col

        # adding symbolic OR between words and making punctuation regexible
        # ["col1","col2"] -> "(col1|col2)"
        primary_curr_col_str = process_columns_to_regex_str(primary_curr_cols)
        alternative_curr_col_str = process_columns_to_regex_str(alternative_curr_cols)
        primary_next_col_str = make_punc_regex_literal("|".join(primary_next_cols))

        # this is for only capturing a single line
        end_cap = ".+)"

        # if we want to capture up to a keyword
        if not stop_capture_at_end_of_value or is_contained_capture and not use_seperater_for_contained_capture:
            end_cap = r"((?!{next_col})[\s\S])*)".format(next_col=primary_next_col_str)
        elif use_seperater_for_contained_capture and not single_line:
            end_cap = r"((?!.+{sep}\?*)[\s\S])*)".format(sep=separator)

        # column has been converted to variable and seen is list of already used variable names
        # regex variable names must be unique
        # ex: pathologic stage -> pathologicStage
        # ex: tumor site -> tumor_site
        primary_variablefied, seen = to_camel_or_underscore(primary_curr_cols[0], seen)

        # if we want to "anchor" the word to the start of the document
        if is_anchor and not dont_add_anchor or add_anchor:
            primary_curr_col_str = r"{anchor}({curr_col})".format(anchor=anchor, curr_col=primary_curr_col_str)

        primary_col_regex = create_regex_str(primary_curr_col_str, primary_variablefied, end_cap)

        # make alternative column regex if needed
        alternative_col_reg = r""
        if len(alternative_curr_cols) != 0:
            alternative_variablefied, seen = to_camel_or_underscore(alternative_curr_cols[0], seen)
            end_cap = r"((?!.+{sep}\?*)[\s\S])*)".format(sep=separator)
            alternative_col_reg = create_regex_str(alternative_curr_col_str, alternative_variablefied, end_cap)
            mappings_to_regex_vals[alternative_variablefied] = alternative_curr_cols

        template_regex += primary_col_regex + alternative_col_reg

        # adding variable name so we can use for later
        mappings_to_regex_vals[primary_variablefied] = primary_curr_cols

    # do last column
    last_col_key = col_keys[-1]
    if add_sep and last_col_key.lower() not in no_sep_list or last_col_key.lower() in sep_list:
        last_col = [c + separator for c in columns[last_col_key].primary_report_col if c not in no_sep_list]
    else:
        last_col = columns[last_col_key].primary_report_col

    last_one = make_punc_regex_literal("|".join(last_col))
    last_one_variable, seen = to_camel_or_underscore(last_one, seen)
    if use_seperater_for_contained_capture:
        end_cap = r"((?!.+{sep}\?*)[\s\S])*)".format(sep=separator)
    else:
        end_cap = r".+)"
    template_regex += r"{last_one}(?P<{last_no_space}>{end_cap}".format(last_one=last_one,
                                                                        last_no_space=last_one_variable,
                                                                        end_cap=end_cap)

    mappings_to_regex_vals[last_one_variable] = columns[last_col_key].primary_report_col

    # this is for any columns that have the column on the first line and value on the second line
    if len(multi_line_cols_list) > 0:
        for col in multi_line_cols_list:
            multi_col_var, seen = to_camel_or_underscore(col, seen)
            multi_col_str = make_punc_regex_literal(col.lower())
            multi_line_regex = r"{column}\s*-*(?P<{multi_col_var}>.+)".format(column=multi_col_str,
                                                                              multi_col_var=multi_col_var)
            template_regex += "|" + multi_line_regex
            mappings_to_regex_vals[multi_col_var] = [col.lower()]

    return "(?i)" + template_regex if ignore_caps else template_regex, mappings_to_regex_vals


def generic_capture_regex(negative_lookahead: str) -> str:
    """
    Creates a general capturing regex based on an input of what you are looking behind.

    :param negative_lookahead:
    :return:
    """
    return r"(?i)(?P<column>[^-:]*(?=:)):(?P<value>(?:(?!{negative_lookahead})[\s\S])*)*".format(
        negative_lookahead=negative_lookahead)


# todo: this function is pretty confusing
def capture_double_regex(starting_word: List[Union[str, List[str]]],
                         ending_word: List[Union[str, List[str]]],
                         capture_first_line: bool = False,
                         capture_last_line: bool = False,
                         ignore_capials: bool = True) -> str:
    """
    Creates a regex pattern that captures between two words or phrases.

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
    :return:                        a regex pattern
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


def synoptic_capture_regex_(columns: Dict[str, Column], val_on_same_line_cols_to_add: list = [],
                            val_on_next_line_cols_to_add: list = [], anchor: str = "",
                            ignore_caps: bool = True, separator: str = ":") -> Tuple[str, Dict[str, List[str]]]:
    """
    Based on a regex pattern template, turns a list of columns into a regex that can capture the values associated with
    those columns.
    :param val_on_same_line_cols_to_add:
    :param ignore_caps:
    :param columns:                       the columns that you want to capture
    :param anchor:                        What position is being matched before the column: https://regex101.com/r/JGWIKB/1
    :param separator:                     The punctuation or letters that separates a column and value. Default is :
    :return:                              A regex pattern
    """
    val_on_same_line_cols_to_add = {col: Column(human_col=col, primary_report_col=[col], regular_pattern_rules={}) for
                                    col in val_on_same_line_cols_to_add}
    val_on_next_line_cols_to_add = {col: Column(human_col=col, primary_report_col=[col], val_on_next_line=True) for
                                    col in val_on_next_line_cols_to_add}
    columns.update(val_on_same_line_cols_to_add)
    col_keys = list(columns.keys())
    template_regex = r""
    mappings_to_regex_vals = {}
    seen = set()
    cols_len = len(col_keys)
    for index in range(cols_len):
        current_col = columns[col_keys[index]]  # grabs the associated pdf columns in Column object
        regex_rules = current_col.regular_pattern_rules

        def process_columns_to_regex_str(cols: List[str]) -> str:
            """
            :param cols:
            """
            # adding separator into regex
            if regex_rules["add separator to col name"]:
                # ["col1","col2"] -> ["col1:","col2:"]
                cols = [c + separator for c in cols]
            cols_str = make_punc_regex_literal("|".join(cols))
            if len(cols) > 1:
                return "(" + cols_str + ")"
            return cols_str

        def create_regex_str(col: str, col_var: str, end_cap: str, front_cap: str = r"{col}(?P<{col_var}>",
                             no_or: bool = False) -> str:
            """
            Generic function to create a capture regular pattern. See examples in above links under synoptic_capture_regex

            :param no_or:     whether or not to add a OR (|) to the end of the regular pattern
            :param col:       column we are capturing
            :param col_var:   the column but as a variable, previously generated
            :param end_cap:   the end of the regular pattern, variations can be seen under synoptic_capture_regex
            :param front_cap: the front of the regular pattern, variations can be seen under synoptic_capture_regex
            :return:          regular pattern
            """
            front_cap = front_cap.format(col=col, col_var=col_var)
            return front_cap + end_cap if no_or else front_cap + end_cap + "|"

        if regex_rules["val on next line"]:
            # this is for any columns that have the column on the first line and value on the second line
            col = current_col.primary_report_col[0]
            multi_col_var, seen = to_camel_or_underscore(col, seen)
            multi_col_str = make_punc_regex_literal(col.lower())
            multi_line_regex = r"{column}\s*-*(?P<{multi_col_var}>.+)".format(column=multi_col_str,
                                                                              multi_col_var=multi_col_var)
            template_regex += "|" + multi_line_regex
            mappings_to_regex_vals[multi_col_var] = [col.lower()]

        else:
            end_cap = ".+)"
            # all the columns we might use
            primary_curr_cols = current_col.primary_report_col
            alternative_curr_cols = current_col.alternative_report_col

            # adding symbolic OR between words and making punctuation regexible
            # ["col1","col2"] -> "(col1|col2)"
            primary_curr_col_str = process_columns_to_regex_str(primary_curr_cols)
            alternative_curr_col_str = process_columns_to_regex_str(alternative_curr_cols)

            if index + 1 < cols_len:
                primary_next_cols = columns[col_keys[index + 1]].primary_report_col
                primary_next_col_str = make_punc_regex_literal("|".join(primary_next_cols))

                # if we want to capture up to a keyword
                if regex_rules["capture up to keyword"]:
                    end_cap = r"((?!{next_col})[\s\S])*)".format(next_col=primary_next_col_str)

            # this is for only capturing up to a separator
            if regex_rules["capture up to line with separator"]:
                end_cap = r"((?!.+{sep}\?*)[\s\S])*)".format(sep=separator)

            # column has been converted to variable and seen is list of already used variable names
            # regex variable names must be unique
            # ex: pathologic stage -> pathologicStage
            # ex: tumor site -> tumor_site
            primary_variablefied, seen = to_camel_or_underscore(primary_curr_cols[0], seen)

            # if we want to "anchor" the word to the start of the document
            if regex_rules["add anchor"]:
                primary_curr_col_str = r"{anchor}({curr_col})".format(anchor=anchor, curr_col=primary_curr_col_str)

            primary_col_regex = create_regex_str(primary_curr_col_str, primary_variablefied, end_cap)

            # make alternative column regex if needed
            alternative_col_reg = r""
            if len(alternative_curr_cols) != 0:
                alternative_variablefied, seen = to_camel_or_underscore(alternative_curr_cols[0], seen)
                end_cap = r"((?!.+{sep}\?*)[\s\S])*)".format(sep=separator)
                alternative_col_reg = create_regex_str(alternative_curr_col_str, alternative_variablefied, end_cap)
                mappings_to_regex_vals[alternative_variablefied] = alternative_curr_cols

            template_regex += primary_col_regex + alternative_col_reg

            # adding variable name so we can use for later
            mappings_to_regex_vals[primary_variablefied] = primary_curr_cols

    return "(?i)" + template_regex if ignore_caps else template_regex, mappings_to_regex_vals


# exporting regular patterns for use in pipeline (not all of them are being used):

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
right_operative_report = [(r"(?i)Pertain.*to *.* right(?P<capture>((?!Pertain.*to *.* left\?*)[\s\S])*)", ""),
                          (r"RIGHT BREAST(?P<capture>((?!LEFT BREAST\?*)[\s\S])*)", ""),
                          (capture_double_regex(["Right breast:"], ["Right breast:"]), ""),
                          (capture_double_regex(["PREOPERATIVE EVALUATION", "RATIONALE FOR SURGERY RIGHT BREAST"],
                                                ["PREOPERATIVE EVALUATION", "RATIONALE FOR SURGERY LEFT BREAST"]),
                           "PREOPERATIVE RATIONALE FOR SURGERY")]

# https://regex101.com/r/kT4aT7/1
# https://regex101.com/r/l760jr/1
left_operative_report = [(r"LEFT SIDE(?P<capture>((?!RIGHT BREAST\?*)[\s\S])*)", ""),
                         (r"LEFT SIDE(?P<capture>((?!RIGHT SIDE\?*)[\s\S])*)", ""),
                         (r"(?i)Pertain.*to *.* left(?P<capture>((?!Pertain.*to *.* right\?*)[\s\S])*)", ""),
                         (r"LEFT BREAST(?P<capture>((?!FOLLOW UP\?*)[\s\S])*)", ""),
                         (capture_double_regex(["Left breast:"], ["Right breast:"]), ""),
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
