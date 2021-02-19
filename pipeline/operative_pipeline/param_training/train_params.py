from typing import List, Tuple
import pandas as pd
from pipeline import run_pipeline
from util.tuning import Tuning
from util.import_tools import import_code_book
from util.utils import get_current_time


def find_cost(col_dict: dict) -> int:
    """
    :param col_dict:
    """
    sorted_dict = dict(sorted(col_dict.items(), key=lambda item: item[1]))
    largest_accuracy_index = 0
    prev = -1
    for ind, acc in sorted_dict.items():
        if prev < acc:
            largest_accuracy_index = ind
        prev = acc
    return largest_accuracy_index


def sub_cost_large_cost_per_vol(training_metrics_dict: dict) -> list:
    """
    :param training_metrics_dict:
    :return:
    """
    code_book = import_code_book("data/inputs/operative_code_book.ods")
    tuning_list = []
    for col_name in code_book:
        index = find_cost(training_metrics_dict[col_name])
        sub_cost = training_metrics_dict["sub cost"][index]
        large_cost = training_metrics_dict["large cost"][index]
        tuning_list.append({"col": col_name, "sub cost": sub_cost, "large cost": large_cost})
    df = pd.DataFrame(tuning_list)
    df.to_csv("data/outputs/training_metrics/params/tuning.csv", index=False)
    return tuning_list


def train_params(substitution_cost: List[int], largest_cost: List[int], skip: List[int], start: int, end: int):
    """
    :param end:
    :param start:
    :param skip:
    :param largest_cost:
    :param substitution_cost:
    """
    accumulated_wrong_missing_correct = []
    for sub_cost in substitution_cost:
        for large_cost in largest_cost:
            result_dict = run_pipeline(start, end, skip, substitution_cost=sub_cost, largest_cost=large_cost)
            iter_dict = {"sub cost": sub_cost, "large cost": large_cost}
            for col, val in result_dict.items():
                iter_dict[col] = val["Accuracy"]
            accumulated_wrong_missing_correct.append(iter_dict)
            print("Finished with sub cost: " + str(sub_cost) + " and largest cost: " + str(large_cost))
    df = pd.DataFrame(accumulated_wrong_missing_correct)
    sub_cost_large_cost_per_vol(df.to_dict())
    df.to_excel("data/outputs/training_metrics/metrics" + get_current_time() + ".xlsx")
