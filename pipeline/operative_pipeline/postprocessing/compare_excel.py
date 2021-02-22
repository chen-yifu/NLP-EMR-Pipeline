import pandas as pd
from pipeline.util.utils import get_current_time
from pipeline.util.value import Value


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


def nice_compare(baseline_version: str, pipeline_dataframe: pd.DataFrame, baseline_path: str,
                 path_to_outputs: str) -> dict:
    """
    :param path_to_outputs:
    :param baseline_version:
    :param pipeline_dataframe:
    :param baseline_path:
    :return:
    """
    baseline_dataframe = pd.read_csv(baseline_path + baseline_version)
    list_cols = list(baseline_dataframe.columns)
    baseline_dict = baseline_dataframe.to_dict()
    pipeline_dict = pipeline_dataframe.to_dict()
    comparison_dict = {}
    wrong_missing_correct_dict = {}

    def compare_baseline_pipeline_val(index, baselineval, pipelineval) -> Value:
        """
        :param baselineval:
        :param pipelineval:
        :return:
        """
        str_baselineval = str(baselineval) if str(baselineval) != "nan" else ""
        str_pipelineval = str(pipelineval) if str(pipelineval) != "nan" else ""
        # both vals are null
        if pd.isna(baselineval) and pd.isna(pipelineval):
            return Value(value="", correct=True, missing=False, wrong=False)
        # baseline is null and pipeline return ""
        elif pd.isna(baselineval) and str(pipelineval) == "":
            return Value(value="", correct=True, missing=False, wrong=False)
        # pipeline is null and baseline returned ""
        elif pd.isna(pipelineval) and str(baselineval) == "":
            return Value(value="", correct=True, missing=False, wrong=False)

        # try turning the inputs into ints
        try:
            # both can be converted to ints and they are the same
            if int(baselineval) == int(pipelineval):
                return Value(value=str(baselineval), correct=True, missing=False, wrong=False)
            # both can be converted to int but do not equal each other
            elif int(baselineval) != int(pipelineval):
                return Value(value=str_baselineval + "|" + str_pipelineval, correct=False,
                             missing=False if str_pipelineval != "" else True, wrong=True)
        except Exception:
            # both can be converted to str and they are the same
            if str_baselineval == str_pipelineval:
                return Value(value=str_baselineval, correct=True, missing=False, wrong=False)
            # both can be converted to str but do not equal each other
            elif str_baselineval != str_pipelineval:
                return Value(value=str_baselineval + "|" + str_pipelineval, correct=False,
                             missing=False if str_pipelineval != "" else True, wrong=True)
            # baseline is null but pipeline got a value
            elif pd.isnull(baselineval):
                return Value(value="|" + str_pipelineval, correct=False, missing=False, wrong=True)
            else:
                # pipeline did not get a value but there is a value in baseline
                return Value(value=str_baselineval + "|", correct=False,
                             missing=False if str_pipelineval != "" else True, wrong=True)

    for column_name in list_cols:
        total_count = 0
        correct = 0
        missing = 0
        wrong = 0
        baseline = baseline_dict[column_name]
        pipeline = pipeline_dict[column_name]
        len_values = len(baseline)
        for index in range(len_values):
            baseline_val = baseline[index]
            pipeline_val = pipeline[index]
            result = compare_baseline_pipeline_val(index, baseline_val, pipeline_val)
            if column_name not in comparison_dict:
                comparison_dict[column_name] = {}
            comparison_dict[column_name][index] = result.value
            total_count += 1
            correct += 1 if result.correct else 0
            missing += 1 if result.missing else 0
            wrong += 1 if result.wrong else 0
        wrong_missing_correct_dict[column_name] = {"Total": total_count, "Correct": correct, "Missing": missing,
                                                   "Wrong": wrong, "Accuracy": correct / total_count}

    comparison_dataframe = pd.DataFrame(comparison_dict)
    wrong_missing_correct_df = pd.DataFrame(wrong_missing_correct_dict)

    coloring_comparison_dataframe = (
        comparison_dataframe.style.applymap(
            lambda v: 'background-color: %s' % 'yellow' if len(v) > 0 and "|" == v[-1] else "").applymap(
            lambda v: 'background-color: %s' % 'red' if len(v) > 0 and "|" in v and v[-1] != "|" else ""))

    current_time = str(get_current_time())
    coloring_comparison_dataframe.to_excel(
        path_to_outputs + "compare/compare_with_" + baseline_version[:-4] + current_time + ".xlsx")
    wrong_missing_correct_df.to_excel(
        path_to_outputs + "compare/accuracy_results_" + baseline_version[:-4] + current_time + ".xlsx")

    return wrong_missing_correct_dict
