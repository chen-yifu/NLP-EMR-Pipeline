from collections import defaultdict
import pandas as pd
from pipeline.processing import columns

zero_empty_columns = columns.get_zero_empty_columns()


def highlight_csv_differences(csv_path_coded: str, csv_path_human: str, output_excel_path: str, report_type: str,
                              print_debug=True, id_col: str = "Study #"):
    """
    given two csv files to compare, merge the data into a xlsx file, while highlighting the cells that are different

    :param csv_path_coded:             path to csv file that has been codified
    :param csv_path_human:             path to csv file that is human-annotated baseline
    :param output_excel_path:          path to save the highlighted excel file
    :param print_debug:                print debug statements in Terminal if True
    :return:                           None
    """
    df_coded = pd.read_csv(csv_path_coded, dtype=str)
    df_human = pd.read_csv(csv_path_human, dtype=str)

    # matching up the columns from baseline with pipeline so it can be compared
    df_coded = df_coded.reindex(columns=list(df_human.columns))

    # if the two dataframes are having different columns, stop and return

    if (df_coded.columns != df_human.columns).any():
        s = "The resulting csv file have different columns than human baseline, couldn't compare the results."
        print(s)
        return

    # compare the two dataframe to determine the number of same/different/missing/extra cells
    overall_accuracy, column_accuracies = calculate_statistics(df_coded, df_human)
    num_same, num_different, num_missing, num_extra = overall_accuracy

    # rename the output path to show overall_accuracy
    output_path = output_excel_path.replace("STAT",
                                            "s{}_d{}_m{}_e{}".format(num_same, num_different, num_missing, num_extra))

    # create xlsx writer object, tutorial link: https://xlsxwriter.readthedocs.io/working_with_pandas.html
    writer = pd.ExcelWriter(output_path, engine='xlsxwriter')

    workbook = writer.book
    worksheet = workbook.add_worksheet(name=report_type)

    color_palette = {
        "pink": "#FFC0CD",
        "orange": "#FFD7BD",
        "yellow": "#FFF1C3",
        "green": "#E9FFC2",
        "blue": "#B3FFED",
        "light green": "#D0FFE4",
        "light blue": "#ebfcfc",
        "gray": "#E3E3E3",
    }

    # use this format to highlight the differences in the two csv files
    no_highlight = workbook.add_format({
        'text_wrap': True,
    })

    highlight_coded_cell_extra = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'fg_color': color_palette["light green"]
    })

    highlight_coded_cell_missing = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'fg_color': color_palette["pink"]
    })

    highlight_different_cells = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'fg_color': color_palette["yellow"]
    })

    highlight_empty_or_zero_cells = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'fg_color': color_palette["light blue"]
    })

    highlight_empty_and_empty_cells = workbook.add_format({
        'fg_color': color_palette["gray"]
    })

    # write headers
    for col_index, col_name in enumerate(df_coded.columns):
        worksheet.write(0, col_index, col_name)

    # iterate through each cell of two csv files, copy values if they are same; highlight values if they are different
    for row_index in range(df_coded.shape[0]):  # TODO compare and copy/highlight
        for col_index, col_name in enumerate(df_coded.columns):
            # resolve possibly redundant ID suffixes. For example, if we have 101L, but 101 is available, then use 101
            coded_id = df_coded[id_col][row_index]

            coded_val = str(df_coded[col_name][row_index])
            try:
                human_val = str(df_human[df_human[id_col] == coded_id][col_name].values[0])
            except IndexError:
                human_val = ""
            if coded_val == "nan":
                coded_val = ""
            if human_val == "nan":
                human_val = ""

            highlight_style = None
            # if exactly the same
            if (coded_val == "" and human_val == "") or \
                    ((coded_val == "" and human_val == "0") or (
                            coded_val == "0" and human_val == "") and col_name in zero_empty_columns) or \
                    not are_different(coded_val, human_val):
                highlight_style = no_highlight
            # if human-annotated value is present but coded value is missing
            elif human_val != "" and coded_val == "":
                highlight_style = highlight_coded_cell_missing
            # if coded value is present but human-annotated value is missing
            elif coded_val != "" and human_val == "" and (
                    are_different(coded_val, 0) or col_name in zero_empty_columns):
                highlight_style = highlight_coded_cell_extra
            # if the values are different, highlight the difference, and put human-annotated values in bracket
            elif are_different(coded_val, human_val):
                highlight_style = highlight_different_cells
            else:
                raise ValueError("Should not reach this branch")
            # enter the value
            worksheet.write(row_index + 1, col_index, coded_val + "\n[{}]".format(human_val), highlight_style)

    for col_index, col_name in enumerate(df_coded.columns):
        statistics_labels = ["num_same", "num_different", "num_missing",
                             "num_extra"]  # , "num_empty_zeros", "num_empty"]
        if col_index == 0:
            for row_index in range(df_coded.shape[0], df_coded.shape[0] + len(statistics_labels)):
                worksheet.write(row_index + 1, col_index, statistics_labels.pop(0))
        else:
            for row_index in range(df_coded.shape[0], df_coded.shape[0] + len(statistics_labels)):
                worksheet.write(row_index + 1, col_index, column_accuracies[col_name][statistics_labels.pop(0)])

    # add a last row that calculates the accuracy using formula:
    # (num_same + num_empty) / (num_same + num_different + num_missing)
    statistics_labels = ["num_same", "num_different", "num_missing", "num_extra"]
    for col_index, col_name in enumerate(df_coded.columns):
        if col_index == 0:
            worksheet.write(df_coded.shape[0] + len(statistics_labels) + 1, col_index,
                            "(same + empty) / (all except extra)")
            continue
        temp = column_accuracies[col_name]
        # accuracy = (same + empty-empty) / (all except extra)
        accuracy = (temp["num_same"]) / (sum(temp.values()) - temp["num_extra"])
        accuracy = round(accuracy, 2)  # round to 2 decimal places
        worksheet.write(df_coded.shape[0] + len(statistics_labels) + 1, col_index, accuracy)

    # write same/difference/missing/extra overall_accuracy in a second excel sheet
    stat_worksheet = workbook.add_worksheet(name="Statistics")
    stat_worksheet.write(0, 0, "Same")
    stat_worksheet.write(0, 1, num_same)
    stat_worksheet.write(1, 0, "Different")
    stat_worksheet.write(1, 1, num_different)
    stat_worksheet.write(2, 0, "Missing")
    stat_worksheet.write(2, 1, num_missing)
    stat_worksheet.write(3, 0, "Extra")
    stat_worksheet.write(3, 1, num_extra)
    # stat_worksheet.write(4, 0, "Zero/Empty")
    # stat_worksheet.write(4, 1, num_empty_zeros)

    writer.save()

    if print_debug:
        s = """
By comparing the extracted annotations by human and this converter, we found:\n
        {} Excel cells are identical in both human and converter annotations    (e.g. human=A, converter=A)\n
        {} cells are missed by converter but annotated by human                 (e.g. human=A, converter=None)\n
        {} cells are annotated by both human and converter, but are different   (e.g. human=A, converter=B)\n
        {} cells are found by converter but human did not annotate              (e.g. human=None, converter=A)\n""" \
            .format(num_same,
                    num_missing,
                    num_different,
                    num_extra)
        # following is deprecated
        # {} cells are empty by human but '0' by converter, or vise versa.       (e.g. human=0/None, converter=None/0)\n
        # {} cells are empty in both human and converter annotations             (e.g. human=None, converter=None)""" \
        # num_empty_zeros,
        # num_empty_empty)
        print(s)

    stats = (num_same, num_different, num_missing, num_extra)  # , num_empty_zeros, num_empty_empty)
    return stats


def are_different(val1, val2):
    """
    given two values, check if they are equivalent:
    - if the values can be converted to numbers, check if the numeric value are equal
    - if the values are strings, check if lower-cased formats are different or one string is substring of another
    - if the values are different, return False
    :param val1:        str;        value to be compared
    :param val2:        str;        value to be compared
    :return:            boolean;    return True if values are equivalent
    """
    val1_str = str(val1).lower()
    val2_str = str(val2).lower()
    if val1 == val2:
        return False  # they are NOT different
    try:
        return float(val1) != float(val2)  # try to cast them into floats and compare
    except ValueError:
        val1_str = val1_str.replace(" ", "")
        val2_str = val2_str.replace(" ", "")
        if len(val1_str) and len(val2_str):
            return not (val1_str in val2_str or val2_str in val1_str)
        else:
            return True


def calculate_statistics(df_coded, df_human, id_col: str = "Study #"):
    """
    calculate the overall accuracy, as well as accuracy for each column
    :return: int, int, int, int, int, int;  num_same, num_different, num_missing, num_extra, num_empty_zeros, num_empty
    dict of {column: accuracy_dict}; each accuracy_dict represents the accuracy statistics for one column (6 ints)
    """
    # some counters to print in terminal
    num_same = 0
    num_different = 0
    num_missing = 0
    num_extra = 0
    num_empty_zeros = 0
    num_empty = 0

    baseline_report_ids = set(df_human[id_col])
    pipeline_report_ids = set(df_coded[id_col])
    # get reports that exist in pipeline but not in baseline
    report_ids_missing_from_baseline = list(pipeline_report_ids - baseline_report_ids)

    # get reports that exist in baseline but not in pipeline
    report_ids_missing_from_pipeline = list(baseline_report_ids - pipeline_report_ids)
    report_ids_missing_from_pipeline_no_laterality = ["".join([l for l in list(report_id) if not l.isalpha()]) for
                                                      report_id in report_ids_missing_from_pipeline]
    print("Reports missing from baseline", report_ids_missing_from_baseline, "\n")
    print("Reports missing from pipeline", report_ids_missing_from_pipeline, "\n")

    column_accuracy_dict = defaultdict(lambda: defaultdict(int))
    # iterate through each cell of two csv files, copy values if they are same; highlight values if they are different
    for row_index in range(df_coded.shape[0]):  # TODO compare and copy/highlight
        for col_index, col_name in enumerate(df_coded.columns):
            # resolve possibly redundant ID suffixes. For example, if we have 101L, but 101 is available, then use 101
            coded_id = df_coded[id_col][row_index]
            # check if the report is missing from the pipeline. In that case do nothing
            if coded_id in report_ids_missing_from_pipeline:
                continue
            # check if the report is missing from the baseline.
            # check if there is a version (R or L) in reports missing from pipeline, but not missing in baseline
            # and use that baseline version to check accuracy
            if coded_id in report_ids_missing_from_baseline:
                coded_id_no_lat = "".join([l for l in list(coded_id) if not l.isalpha()])
                for index, report_id in enumerate(report_ids_missing_from_pipeline_no_laterality):
                    if coded_id_no_lat == report_id:
                        coded_id = report_ids_missing_from_pipeline[index]

            coded_val = str(df_coded[col_name][row_index])
            try:
                human_val = str(df_human[df_human[id_col] == coded_id][col_name].values[0])
            except IndexError:
                human_val = ""
            if coded_val == "nan" or coded_val == None:
                coded_val = ""
            if human_val == "nan" or human_val == None:
                human_val = ""

            # if both pathology_pipeline and human extracted empty cells
            if (coded_val == "" and human_val == "") or \
                    ((coded_val == "" and human_val == "0") or (
                            coded_val == "0" and human_val == "") and col_name in zero_empty_columns) or \
                    not are_different(coded_val, human_val):
                num_same += 1
                column_accuracy_dict[col_name]["num_same"] += 1
            # if
            elif human_val != "" and coded_val == "":
                num_missing += 1
                column_accuracy_dict[col_name]["num_missing"] += 1
            # if coded value is present but human-annotated value is missing
            elif coded_val != "" and human_val == "" and (
                    are_different(coded_val, 0) or col_name in zero_empty_columns):
                num_extra += 1
                column_accuracy_dict[col_name]["num_extra"] += 1
            # if the values are different, highlight the difference, and put human-annotated values in bracket
            elif are_different(coded_val, human_val):
                num_different += 1
                column_accuracy_dict[col_name]["num_different"] += 1
            else:
                raise ValueError("Should not reach this branch.")

    # for study_id that are in human-annotated but not in difference, count the entire row as missing
    coded_ids = list(df_coded[id_col])
    human_ids = list(df_human[id_col])
    print("There are {} rows extracted by humans, and {} rows by the pathology_pipeline".format(len(human_ids),
                                                                                                len(coded_ids)))

    statistics = (num_same, num_different, num_missing, num_extra)

    return statistics, column_accuracy_dict
