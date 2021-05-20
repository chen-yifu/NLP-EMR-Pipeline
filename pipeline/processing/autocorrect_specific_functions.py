"""
2021 Yifu (https://github.com/chen-yifu) and Lucy (https://github.com/lhao03)
This file includes code autocorrects specific features of interest. Every function must have this format:
def autocorrect_function(val: str, paths: Dict[str,str]) -> str:
    # do stuff
"""
from typing import Dict
import pandas as pd
from nltk import edit_distance


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


def find_pathologic_stage(stage: str, paths: Dict[str, str]) -> str:
    """
    :param paths:
    :param stage: str
    :return edited_stage: str
    """
    path_to_stages = paths["stages"]
    stage = stage.replace("\n", " ").strip()
    categories_dict = categories(path_to_stages)
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
