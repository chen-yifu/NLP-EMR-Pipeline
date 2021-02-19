import collections
import re
from datetime import datetime
from nltk.corpus import words


def add_asterisk(word: str) -> str:
    """
    :param word:
    :return:
    """
    return "".join([l + " *" if l != " " else l for l in word.split()])


def capture_singular_regex(starting_word: str) -> str:
    modified_starting_word = add_asterisk(starting_word)
    modified_regex = r"[\n\r](?i) *{modified_starting_word}\s*([^\n\r]*)".format(
        modified_starting_word=modified_starting_word)
    return modified_regex


def capture_between_regex(starting_word: str, ending_word: str) -> str:
    """
    :param starting_word:
    :param ending_word:
    :return:
    """
    modified_starting_word = add_asterisk(starting_word)
    modified_ending_word = add_asterisk(ending_word)
    modified_regex = r"(?i){starting_word}(?P<capture>(?:(?!{ending_word})[\s\S])+)".format(
        starting_word=modified_starting_word, ending_word=modified_ending_word)
    return modified_regex


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
