import collections
import os
import re
from datetime import datetime
from typing import List

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


def convert_to_regex(list_of_words: List[str]) -> str:
    """
    Helper function to convert a string into regex
    :param list_of_words:
    :return:
    """
    result = ""
    for word in list_of_words[:-1]:
        if word == " ":
            result += " "
        else:
            result += add_asterisk(word) + ".*"
    result += add_asterisk(list_of_words[-1])
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


def capture_double_regex(starting_word: List[str], ending_word: List[str], capture_first_line: bool = False,
                         capture_last_line: bool = False) -> str:
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
    modified_regex = r"(?i){starting_word}(?P<capture>(?:(?!{ending_word})[\s\S])+)".format(
        starting_word=modified_starting_word, ending_word=modified_ending_word)
    return modified_regex


# print(capture_double_regex(["Synoptic Report: "], ["- End of Synoptic"], True))


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
