import re
from nltk.corpus import stopwords
import pandas as pd
from nltk import edit_distance

from pipeline.util import utils
from pipeline.util.report import Report


def preprocess_resolve_ocr_spaces(strings_and_ids, medical_vocabulary=[], print_debug=True,
                                  log_box=None, app=None):
    """
    given a list of strings and ids, using a english vocabulary, resolve redundant white spaces from OCR.
    Example: "Inv asive Carcinoma" should be corrected as "Invasive Carcinoma" because "Inv" and "Asive" are not in the
    vocabulary, but the joint words_list of "Invasive" is in the vocabulary, so we should join the fargments together.
    This function cannot resolve missing white spaces, for example "InvasiveCarninoma".
    :param strings_and_ids:         a list of (str, str) tuples;        represents the strings and study_ids of PDFs
    :param medical_vocabulary:      a list of str;                      a list of valid english words_list common to PDFs
    :param print_debug:             boolean;                            print debug statements in Terminal if true
    :return:
    """

    def resolve_ocr(raw_string, medical_vocabulary=[]):
        """
        resolve extra white space in raw string by merging two fragments
        :param raw_string:          str;        raw string
        :return:                    str;        resolved string
        """

        # words_list = [w.lower() for w in re.findall(r'\S+|\n', raw_string)]  # make everything lowecase
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
                    candidate_word = candidate_word + next_word
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


def categories(stages_path: str) -> dict:
    """
    :param stages_path: str
    :return categories: dict
    """
    categories_csv = pd.read_csv(stages_path)
    return {"T": [t for t in categories_csv["T"].tolist() if "T" in str(t)],
            "N": [n for n in categories_csv["N"].tolist() if "N" in str(n)],
            "M": [m for m in categories_csv["M"].tolist() if "M" in str(m)]}


def find_category(index: int, category_dict: list, stage: str) -> (str, int):
    """
    given a stage, compute the edit distance for it based on the category
    :param category_dict: dict
    :param index: str                   current index
    :param stage: str                   the original word
    :return edited_stage_category: str  the edited stage that it most likely the closest via edit distance
    :return to_skip: int                how much overlap there is, return  [mpT1a ]pN1mi
                                                                           [mpTla] pNlmi -> skip 1
    """
    if index + 4 <= len(stage):
        supposed_category = stage[index:index + 4].replace("l", "1").replace("O", "0")
        for category in category_dict:
            if edit_distance(supposed_category, category) == 0:
                return category + " ", len(supposed_category) - 1
    if index + 3 <= len(stage):
        supposed_category = stage[index:index + 3].replace("l", "1").replace("O", "0")
        for category in category_dict:
            if edit_distance(supposed_category, category) == 0:
                return category + " ", len(supposed_category) - 1
    # case 2: T1a, etc
    # take two more letters and try the edit distance, if any are 1, then return
    if index + 2 <= len(stage):
        supposed_category = stage[index:index + 2].replace("l", "1").replace("O", "0")
        for category in category_dict:
            if edit_distance(supposed_category, category) == 0:
                return category + " ", len(supposed_category) - 1
    # case 1: T0, T1, MX
    if index + 1 <= len(stage):
        supposed_category = stage[index:index + 1].replace("l", "1").replace("O", "0")
        for category in category_dict:
            if edit_distance(supposed_category, category) == 0:
                return category + " ", len(supposed_category) - 1
    # case 3: none of the matches
    return stage[index], 0


def find_pathologic_stage(stage: str, path_to_stages) -> str:
    """
    :param stage: str
    :return edited_stage: str
    """
    stage = stage.replace("\n", " ").strip()
    categories_dict = categories(path_to_stages)
    # categories("stages.csv")
    edited_stage = ""
    to_skip = 0
    for index, letter in enumerate(stage):
        if letter == "T":  # tumor
            category_skip = find_category(index, categories_dict["T"], stage)
            edited_stage += category_skip[0]
            to_skip = category_skip[1]
        elif letter == "N":
            category_skip = find_category(index, categories_dict["N"], stage)
            edited_stage += category_skip[0]
            to_skip = category_skip[1]
        elif letter == "M":
            category_skip = find_category(index, categories_dict["M"], stage)
            edited_stage += category_skip[0]
            to_skip = category_skip[1]
        elif to_skip != 0:
            to_skip -= 1
            continue
        else:
            edited_stage += letter
    return ' '.join(edited_stage.split())
