"""
2021 Yifu (https://github.com/chen-yifu) and Lucy (https://github.com/lhao03)
This file includes code that deals with utilities such as time and paths.
"""
import collections
import os
import re
from copy import copy
from datetime import datetime
from typing import List

from nltk.corpus import words
from pathlib import Path
from string import punctuation


def get_current_time():
    """
    :return:
    """
    timestamp = datetime.now().strftime("%d-%m-%Y~%H%M")
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
        if freq >= min_freq and not any(l in word for l in punctuation) and all(l.isalpha() for l in word):
            result.append(word)
    english_words = [w.lower() for w in words.words() if len(w) > 1] + ["a", "i"]
    non_english_words = list(set([w.lower() for w in result]) - set(english_words))
    non_english_words = [w for w in non_english_words if len(w) > 3]
    if print_debug:
        s = "Found these {} non-english words with" \
            "frequent occurrences in all PDFs (min_freq={}): {}".format(len(non_english_words),
                                                                        min_freq,
                                                                        non_english_words)
        print(s)
    return non_english_words


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
    """
    :param path:
    :return:
    """
    full_path = os.path.join(get_project_root(), path)
    return path


def create_rules(front_cap_rules: List[str], add_to_col_rules: List[str], end_cap_rules: List[str]) -> List[dict]:
    """
    :param front_cap_rules:
    :param add_to_col_rules:
    :param end_cap_rules:
    """
    front_rules = []
    end_rules = []
    possible_tf = 2 ** len(add_to_col_rules)
    col_rules = [{} for i in range(possible_tf)]

    # front cap: only one can be true at all times
    # add to col: all can be true at one time
    # end cap: only one can be true at all times

    for front_cap_rule in front_cap_rules:
        front_cap_dict = {rule: False for rule in front_cap_rules}
        front_cap_dict[front_cap_rule] = True
        front_rules.append(front_cap_dict)

    counter = 0
    for add_to_col_rule in add_to_col_rules:
        if counter % 2 == 1:
            i = 0
            for col_rule in col_rules:
                if i % 2 == 1:
                    col_rule[add_to_col_rule] = False
                else:
                    col_rule[add_to_col_rule] = True
                i += 1

        elif counter % 2 == 0:
            i = 0
            for col_rule in col_rules:
                if i < possible_tf / 2:
                    col_rule[add_to_col_rule] = True
                    i += 1
                else:
                    col_rule[add_to_col_rule] = False
        counter += 1

    for end_cap_rule in end_cap_rules:
        end_cap_dict = {rule: False for rule in end_cap_rules}
        end_cap_dict[end_cap_rule] = True
        end_rules.append(end_cap_dict)

    half_rules = []
    for front_rule in front_rules:
        for col_rule in col_rules:
            front_rule_copy = copy(front_rule)
            col_rule_copy = copy(col_rule)
            front_rule_copy.update(col_rule_copy)
            half_rules.append(front_rule_copy)

    rules = []
    for half_rule in half_rules:
        for end_rule in end_rules:
            half_rule_copy = copy(half_rule)
            end_rule_copy = copy(end_rule)
            half_rule_copy.update(end_rule_copy)
            half_rule_copy.update({"same": 0, "missing": 0})
            rules.append(half_rule_copy)

    return rules


create_rules(["val on same line", "val on next line"], ["add anchor", "add separator to col name"],
             ["capture to end of val", "capture up to line with separator", "capture up to keyword"])
