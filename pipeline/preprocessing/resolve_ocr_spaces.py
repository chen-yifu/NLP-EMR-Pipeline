"""
2021 Yifu (https://github.com/chen-yifu) and Lucy (https://github.com/lhao03)
This file includes code that resolves errors that occur from optical character recognition (OCR).
"""
import re
from nltk.corpus import stopwords
from pipeline.utils import utils


def preprocess_resolve_ocr_spaces(strings_and_ids, medical_vocabulary=[], print_debug=True,
                                  log_box=None, app=None):
    """
    given a list of strings and ids, using a english vocabulary, resolve redundant white spaces from OCR.
    Example: "Inv asive Carcinoma" should be corrected as "Invasive Carcinoma" because "Inv" and "Asive" are not in the
    vocabulary, but the joint words_list of "Invasive" is in the vocabulary, so we should join the fragments together.
    This function cannot resolve missing white spaces, for example "InvasiveCarninoma".

    :param strings_and_ids:         a list of (str, str) tuples;        represents the strings and study_ids of PDFs
    :param medical_vocabulary:      a list of str;                      a list of valid english words_list common to PDFs
    :param print_debug:             boolean;                            print debug statements in Terminal if true
    :return:
    """

    def resolve_ocr(raw_string, medical_vocabulary=[]):
        """
        resolve extra white space in raw string by merging two fragments
        :param medical_vocabulary:
        :param raw_string:          str;        raw string
        :return:                    str;        resolved string
        """

        # words_list = [w.lower() for w in re.findall(r'\S+|\n', raw_string)]  # make everything lowercase
        # demo: (?<=[ \n\W])|(?=[ \n\W])
        # equivalent to string.split(), but retains linebreaks
        words_list = re.split("(?<=[ \n\W])|(?=[ \n\W])", raw_string)

        # common (frequency > min_freq) vocabularies specific to the PDFs, keep only long words (exclude punctuations)
        medical_vocabulary = [w for w in medical_vocabulary if len(w) > 2]

        # vocabularies in english dictionaries, words must be longer than 2
        eng_vocab = [w for w in utils.get_english_dictionary_as_list() if len(w) > 2]  # only words longer than 2
        eng_vocab += list(stopwords.words('english'))  # add stop words
        eng_vocab.remove("i")  # lower case "i" is a common cause of extra white space
        vocab = set(medical_vocabulary + eng_vocab)
        result_words = []
        skip = 0
        for i, word in enumerate(words_list):
            if not word.strip().isalpha():
                result_words.append(word)
                continue
            # if this words_list need to be skipped, or if this word is last word in list, don't process it
            # word = word.strip()
            if skip > 0:
                skip -= 1
            elif word.lower().strip() not in vocab:
                candidate_word = ""
                for next_word in words_list[i:]:
                    if not next_word.strip().isalpha():
                        continue
                    candidate_word += next_word
                    skip += 1
                    if candidate_word.lower().strip() in vocab:
                        skip -= 1
                        break
                    else:
                        if next_word.lower().strip() in vocab:
                            skip = 0
                            break
                        else:
                            continue

                if candidate_word.lower().strip() in vocab:
                    result_words.append(candidate_word)
                else:
                    result_words.append(word)
                    skip = 0

            else:
                if skip == 0:
                    result_words.append(word)
        resolved_words = "".join(result_words)
        return resolved_words

    result = []
    for index, report in enumerate(strings_and_ids):
        resolved_string = resolve_ocr(report.text, medical_vocabulary=medical_vocabulary)
        resolved_string = re.sub(" +", " ", resolved_string)
        report.text = resolved_string
        result.append(report)

    return result



