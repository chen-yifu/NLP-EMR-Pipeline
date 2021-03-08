import collections
import os
import re
from datetime import datetime
from typing import List, Tuple, Dict, OrderedDict
import pandas as pd
from nltk.corpus import words
from pathlib import Path
from string import punctuation


def import_pdf_human_cols_as_dict(pdf_human_excel_sheet: str, skip=None) -> Dict[str, List[str]]:
    """
    :param pdf_human_excel_sheet:
    :param skip:
    :return:
    """
    if skip is None:
        skip = []
    pdf_cols_human_cols_dict = {}
    pdf_cols_human_cols = pd.read_csv(pdf_human_excel_sheet)
    for index, row in pdf_cols_human_cols.iterrows():
        human_col = row[1]
        if human_col in skip:
            continue
        else:
            pdf_cols = row[0]
            pdf_cols_list = pdf_cols.split(",")
            cleaned_pdf_col_list = [p.strip() for p in pdf_cols_list]
            pdf_cols_human_cols_dict[human_col] = cleaned_pdf_col_list
    return pdf_cols_human_cols_dict


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
        if freq >= min_freq and not any(l in word for l in punctuation) and all(l.isalpha() for l in word):
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
