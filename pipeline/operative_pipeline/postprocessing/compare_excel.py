from typing import List, Dict
import pandas as pd
from pipeline.util.report import Report
from pipeline.util.utils import get_current_time
from pipeline.util.comparisonhelpertype import ComparisonHelperType


def compare_baseline_pipeline_val(baselineval, pipelineval) -> ComparisonHelperType:
    """
    :param baselineval:
    :param pipelineval:
    :return:
    """
    str_baselineval = str(baselineval) if str(baselineval) != "nan" else ""
    str_pipelineval = str(pipelineval) if str(pipelineval) != "nan" else ""
    # both vals are null
    if pd.isna(baselineval) and pd.isna(pipelineval):
        return ComparisonHelperType(value="", correct=True, missing=False, wrong=False)
    # baseline is null and pipeline return ""
    elif pd.isna(baselineval) and str(pipelineval) == "":
        return ComparisonHelperType(value="", correct=True, missing=False, wrong=False)
    # pipeline is null and baseline returned ""
    elif pd.isna(pipelineval) and str(baselineval) == "":
        return ComparisonHelperType(value="", correct=True, missing=False, wrong=False)

    # try turning the inputs into ints
    try:
        # both can be converted to ints and they are the same
        if int(baselineval) == int(pipelineval):
            return ComparisonHelperType(value=str(baselineval), correct=True, missing=False, wrong=False)
        # both can be converted to int but do not equal each other
        elif int(baselineval) != int(pipelineval):
            return ComparisonHelperType(value=str_baselineval + "|" + str_pipelineval, correct=False,
                                        missing=False if str_pipelineval != "" else True, wrong=True)
    except Exception:
        # both can be converted to str and they are the same
        if str_baselineval == str_pipelineval:
            return ComparisonHelperType(value=str_baselineval, correct=True, missing=False, wrong=False)
        # both can be converted to str but do not equal each other
        elif str_baselineval != str_pipelineval:
            return ComparisonHelperType(value=str_baselineval + "|" + str_pipelineval, correct=False,
                                        missing=False if str_pipelineval != "" else True, wrong=True)
        # baseline is null but pipeline got a value
        elif pd.isnull(baselineval):
            return ComparisonHelperType(value="|" + str_pipelineval, correct=False, missing=False, wrong=True)
        else:
            # pipeline did not get a value but there is a value in baseline
            return ComparisonHelperType(value=str_baselineval + "|", correct=False,
                                        missing=False if str_pipelineval != "" else True, wrong=True)


def compare_dataframes_dev(baseline_version: str, pipeline_dataframe: pd.DataFrame, baseline_path: str,
                           path_to_outputs: str) -> pd.DataFrame:
    """
    :param path_to_outputs:
    :param baseline_version:
    :param pipeline_dataframe:
    :param baseline_path:
    :return:
    """
    # read in baseline as dataframe
    baseline_dataframe = pd.read_csv(baseline_path + baseline_version + ".csv")

    # get dataframe from reports that is not yet excel
    # check has the same cols
    if len(baseline_dataframe.columns) != len(pipeline_dataframe.columns):
        print("The baseline dataframe and pipeline dataframe do not have the same cols!")
        return

    # compare
    comparison_dataframe = baseline_dataframe.compare(pipeline_dataframe)
    comparison_dataframe.to_excel(
        path_to_outputs + "compare-dev/compare_with_" + baseline_version + str(get_current_time()) + ".xlsx")
    return comparison_dataframe


def make_custom_id_dict(id_col: str, id_col_dict: dict, old_dict: dict) -> Dict[str, dict]:
    """
    Makes an dictionary with the values in the id column as keys and the rest of the columns as the dictionary values.

    | id| a | b |
    |---|---|---|
    | 1 | 3 | 5 |
    | 4 | 4 | 4 |

    becomes {"1":{"a":3, "b":5}, "4":{"a":4, "b":4}}

    :param id_col:
    :param id_col_dict:
    :param old_dict:
    :return:
    """
    custom_id_dict = {}
    for index, id_col_val in id_col_dict.items():
        row = {}
        for col, values in old_dict.items():
            if col == id_col:
                continue
            else:
                row[col] = values[index]
        custom_id_dict[id_col_val] = row
    return custom_id_dict


def nice_compare(baseline_version: str, pipeline_dataframe: pd.DataFrame, baseline_path: str,
                 path_to_outputs: str, id_col: str = "Study #") -> pd.DataFrame:
    """
    :param path_to_outputs:
    :param baseline_version:
    :param pipeline_dataframe:
    :param baseline_path:
    :return:
    """

    baseline_dataframe = pd.read_csv(baseline_path)
    baseline_dataframe_cols = (set(baseline_dataframe.columns))

    pipeline_dataframe_cols = set(pipeline_dataframe.columns)

    if baseline_dataframe_cols != pipeline_dataframe_cols:
        extra_cols = baseline_dataframe_cols - pipeline_dataframe_cols
        print("Here are the column differences:")
        print("Baseline extra columns:", baseline_dataframe_cols - pipeline_dataframe_cols)
        print("Pipeline extra columns:", pipeline_dataframe_cols - baseline_dataframe_cols)
        print("Will delete the extra columns from the pipeline dataframe.")
        for extra_col in extra_cols:
            try:
                del pipeline_dataframe[extra_col]
            except Exception:
                pass

    baseline_dataframe_cols = list(baseline_dataframe_cols)
    baseline_unchanged_dict = baseline_dataframe.to_dict()
    baseline_dict = make_custom_id_dict(id_col, baseline_unchanged_dict[id_col], baseline_unchanged_dict)

    pipeline_unchanged_dict = pipeline_dataframe.to_dict()
    pipeline_dict = make_custom_id_dict(id_col, pipeline_unchanged_dict[id_col], pipeline_unchanged_dict)
    comparison_list = []

    baseline_ids = baseline_dict.keys()
    pipeline_ids = pipeline_dict.keys()
    missing_from_pipeline = set(pipeline_ids) - set(baseline_ids)
    missing_from_baseline = set(baseline_ids) - set(pipeline_ids)

    default_col_comparison_dict = {"Total": 0, "Correct": 0, "Missing": 0, "Wrong": 0, "Accuracy": 0}
    wrong_missing_correct_dict = dict.fromkeys(baseline_dataframe_cols, default_col_comparison_dict)

    for baseline_id in baseline_ids:
        comparison_report_dict = dict.fromkeys(baseline_dataframe_cols, "")
        comparison_report_dict[id_col] = baseline_id
        if baseline_id in pipeline_ids:
            baseline_cols_vals = baseline_dict[baseline_id]
            pipeline_cols_vals = pipeline_dict[baseline_id]
            for col in baseline_dataframe_cols:
                baseline_val = baseline_cols_vals[col]
                pipeline_val = pipeline_cols_vals[col]
                result = compare_baseline_pipeline_val(baseline_val, pipeline_val)
                wrong_missing_correct_dict[col]["Total"] += 1
                comparison_report_dict[col] = result.value
                if result.missing:
                    wrong_missing_correct_dict[col]["Missing"] += result.missing
                if result.wrong:
                    wrong_missing_correct_dict[col]["Wrong"] += result.wrong
                if result.correct:
                    wrong_missing_correct_dict[col]["Correct"] += result.correct

                csf = wrong_missing_correct_dict[col]["Correct"]
                tsf = wrong_missing_correct_dict[col]["Total"]
                wrong_missing_correct_dict[col]["Accuracy"] = csf / tsf
        comparison_list.append(comparison_report_dict)

    # add missing ones
    for missing_from_pipeline_id in missing_from_pipeline:
        print("")
    for missing_from_baseline_id in missing_from_baseline:
        print("")

    current_time = str(get_current_time())
    comparison_df = pd.DataFrame(comparison_list)
    comparison_df.sort_values(id_col)
    comparison_df.to_excel(
        path_to_outputs + "compare/compare_with_" + baseline_version[:-4] + current_time + ".xlsx")

    wrong_missing_correct_df = pd.DataFrame(wrong_missing_correct_dict)
    wrong_missing_correct_df.to_excel(
        path_to_outputs + "compare/accuracy_results_" + baseline_version[:-4] + current_time + ".xlsx")
