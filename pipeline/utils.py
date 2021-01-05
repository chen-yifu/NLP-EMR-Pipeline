import collections
import os
import re
from datetime import datetime
from nltk.corpus import words
from pathlib import Path


def get_current_time():
    timestamp = datetime.now().strftime("%Y-%m-%d~%H:%M")
    return timestamp


def util_resolve_ocr_spaces(regex):
    def replace_helper(match):
        match = match.group()
        return "[ ]*" + match + "[ ]*"

    # FIXME check this regex - (Yifu Jan 4)
    regex = re.sub(r"[A-OQ-VX-Za-mo-rt-vx-z]", replace_helper, regex)
    regex = re.sub(r"(\\\()[^\?]", replace_helper, regex)
    regex = re.compile(regex)
    return regex


def find_all_vocabulary(list_of_strings, print_debug=True, min_freq=2):
    """
    find all non-rare words in a list of strings. The results will be used to autocorrect text
    :param list_of_strings:     a list of str;              strings of PDFs
    :param print_debug:         boolean;                    print debug statements in Terminal if true
    :param min_freq:            int;                        minimum freq required for a string to be considered valid
    :return:                    a list of str;              a list of vocabulary words that are valid
    """
    from nltk.corpus import words
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
    return full_path

