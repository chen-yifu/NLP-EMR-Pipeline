"""
2021 Yifu (https://github.com/chen-yifu) and Lucy (https://github.com/lhao03)
This file includes code that writes dataframes to csv or excel sheet.
"""
import os
from typing import List, Tuple, Dict
import pandas as pd

from pipeline.utils.column import Column
from pipeline.utils.report import Report
from pipeline.utils.utils import get_current_time


def to_spreadsheet(dataframe: pd.DataFrame, type_of_output: str, path_to_output: str):
    """
    Takes a dataframe and changes it into a spreadsheet.
    :param path_to_output:      the path where you want to save the spreadsheet
    :param dataframe:           a dataframe that is ready to be converted to excel
    :param type_of_output:      the report type
    """
    if not os.path.exists(path_to_output + "raw/"):
        os.makedirs(path_to_output + "raw/")
    dataframe.to_excel(path_to_output + "raw/" + type_of_output + str(get_current_time()) + ".xlsx", index=False)


def add_report_id(report: Report) -> dict:
    """
    Adds report id and laterality to a dictionary
    :param report:      a single report
    :return:
    """
    new_dict = {"Study #": report.report_id, "Laterality": report.laterality}
    new_dict.update(report.encoded)
    return new_dict


def change_unfiltered_to_dict(report) -> dict:
    """
    Changing the report into one dictionary to be converted into a dataframe
    :param report:      a single report
    :return:
    """
    new_dict = {"Study #": report.report_id, "Laterality": report.laterality}
    new_dict.update(report.extractions)
    return new_dict


def reports_to_spreadsheet(reports: List[Report], path_to_output: str, type_of_report: str, function) -> pd.DataFrame:
    """
    Converts a general extraction to spreadsheet.
    :param function:            depending on the report type, there is a different function to clean up the reports
    :param type_of_report:      unfiltered, cleaned, encoded, etc
    :param path_to_output:      path to where the spreadsheet should be saved
    :param reports:             list of reports
    :return:
    """

    if not os.path.exists(path_to_output + "raw"):
        os.makedirs(path_to_output + "raw")

    dataframe_coded = pd.DataFrame([function(report) for report in reports])

    dataframe_coded.to_excel(
        path_to_output + "raw/" + type_of_report + "_output" + str(get_current_time()) + ".xlsx", index=False)

    return dataframe_coded


def raw_reports_to_spreadsheet(reports: List[Report], pdf_human_cols: List[Tuple[str, str]], path_to_output: str):
    """
    Filters the unfiltered extractions and turns into a spreadsheet.
    :param pdf_human_cols:
    :param path_to_output:
    :param reports:
    :return:
    """

    def to_dataframe() -> (pd.DataFrame, list):
        """
        :return:
        """
        not_found = []
        cols = [human_col for pdf_col, human_col in pdf_human_cols]
        rows_list = []
        for report in reports:
            report_id = report.report_id
            not_found_per_report = {report_id: []}
            row_dict = {"Study #": report_id, "Laterality": report.laterality}
            for col_name in cols:
                extracted = report.extractions
                if col_name in extracted:
                    row_dict[col_name] = extracted[col_name]
                else:
                    not_found_per_report[report_id].append(col_name)
            rows_list.append(row_dict)
        dataframe = pd.DataFrame(rows_list)
        return dataframe, not_found

    to_spreadsheet(to_dataframe()[0], type_of_output="raw_output", path_to_output=path_to_output)


def save_dictionaries_into_csv_raw(reports: List[Report], column_mapping: Dict[str, Column], csv_path: str,
                                   print_debug=True) -> pd.DataFrame:
    """
    given a list of reports, keeping only the targeted columns in column_mapping, save them to a csv file
    i.e., even if we extracted other columns, if it's not a target column, we don't keep it
    :param reports:
    :param column_mapping:
    :param csv_path:                                     path to output csv
    :param print_debug:                                  print debug statements and resulting dataframe if True
    """

    report_cols = []
    human_cols = []
    for human_col, report_col in column_mapping.items():
        human_cols.append(human_col)
        report_cols += report_col.primary_report_col
        report_cols += report_col.alternative_report_col

    pd.options.mode.chained_assignment = None  # default="warn"
    pd.options.display.width = 0

    to_encode = []
    for report in reports:
        to_encode_dict = {}
        for col, extract in report.extractions.items():
            to_encode_dict[col] = extract.primary_value + str(
                extract.alternative_value) if extract.alternative_value != [] else extract.primary_value
        to_encode_dict.update({"Study #": report.report_id})
        to_encode.append(to_encode_dict)

    unique_cols = []
    [unique_cols.append(col) for col in human_cols if col not in unique_cols]
    df = pd.DataFrame(to_encode, columns=unique_cols)

    df.to_csv(csv_path, index=False)

    if print_debug:
        s = df.loc[:].to_string()
        print(s)
        print("\nDone saving the results to {}\n".format(csv_path))

    return df
