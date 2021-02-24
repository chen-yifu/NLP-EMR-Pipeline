import collections
import os
import re
from datetime import datetime
from typing import List, Union
from nltk.corpus import words
from pathlib import Path


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


def capture_singular_regex(starting_word: str) -> str:
    """

    :param starting_word:
    :return:
    """
    modified_starting_word = convert_to_regex(starting_word)
    modified_regex = r"[\n\r](?i) *{modified_starting_word}\s*([^\n\r]*)".format(
        modified_starting_word=modified_starting_word)
    return modified_regex


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


def capture_laterality() -> str:
    print("laterality")


# https://regex101.com/r/2dxpIX/1
# print(capture_double_regex(["Synoptic Report: "], ["- End of Synoptic"], capture_first_line=True, ignore_capials=False))
# print(
#     r"S *y *n *o *p *t *i *c R *e *p *o *r *t *: .+(?P<capture>(?:(?!-+ *E *n *d *of *S *y *n *o *p *t *i *c)[\s\S])+)")
#
# print(capture_double_regex([" FinalDiagnosis"],
#                            [["Comment:", "COMMENT", "ClinicalHistoryas", "CasePathologist:", "Electronicallysignedby"]],
#                            ignore_capials=False))
# print(
#     r" *F *i *n *a *l *D *i *a *g *n *o *s *i *s(?P<capture>(?:(?!C *o *m *m *e *n *t *:|C *O *M *M *E *N *T|C *l *i *n *i *c *a *l *H *i *s *t *o *r *y *a *s|C *a *s *e *P *a *t *h *o *l *o *g *i *s *t *:|E *l *e *c *t *r *o *n *i *c *a *l *l *y *s *i *g *n *e *d *b *y)[\s\S])+)")


def get_current_time():
    """
    :return:
    """
    timestamp = datetime.now().strftime("-%Y-%m-%d~%H%M")
    return timestamp


def util_resolve_ocr_spaces(regex):
    """
    :param regex:
    :return:
    """

    def replace_helper(match):
        """
        :param match:
        :return:
        """
        match = match.group()
        return "[ ]*" + match + "[ ]*"

    # FIXME check this regex - (Yifu Jan 4)
    regex = re.sub(r"[A-OQ-VX-Za-mo-rt-vx-z]", replace_helper, regex)
    regex = re.sub(r"(\\\()[^\?]", replace_helper, regex)
    regex = re.compile(regex)
    return regex


def find_all_vocabulary(list_of_strings, print_debug=True, min_freq=2):
    """
    :param list_of_strings:
    :param print_debug:
    :param min_freq:
    :return:
    """
    total_string = " ".join(list_of_strings)
    total_words = total_string.split()
    counter = collections.Counter(total_words)
    result = []
    for word, freq in counter.items():
        if freq >= min_freq:
            result.append(word)
    english_words = [w.lower() for w in words.words() if len(w) > 1] + ["a", "i"]
    non_english_words = list(set([w.lower() for w in result]) - set(english_words))
    if print_debug:
        s = "Found these {} non-english words with" \
            "frequent occurrences in all PDFs (min_freq={}): {}".format(len(non_english_words),
                                                                        min_freq,
                                                                        non_english_words)
        print(s)
    return result


def get_english_dictionary_as_list():
    """
    get an english dictionary of words
    :return:    list of str;            an english dictionary
    """
    # get all words that are longer than one except "I" and "a"
    res = [w for w in words.words() if len(w) > 1] + ["a", "i"]
    return res


def get_next_col_name(col, keys):
    i = 2
    next_col = col + "{}".format(i)
    while next_col in keys:
        i += 1
        next_col = col + "{}".format(i)
    return next_col


def get_project_root():
    return Path(__file__).parent.parent


def get_full_path(path):
    full_path = os.path.join(get_project_root(), path)
    return "../" + path
