import os
from typing import List
import pandas as pd

from pipeline.operative_pipeline.util import import_tools
from pipeline.operative_pipeline.util.report import Report
from pipeline.operative_pipeline.util.utils import get_current_time


def to_spreadsheet(dataframe: pd.DataFrame, type_of_output: str):
    """
    :param dataframe:
    :param type_of_output:
    """
    if not os.path.exists("data/outputs/raw"):
        os.makedirs("data/outputs/raw")
    dataframe.to_excel("data/outputs/raw/" + type_of_output + str(get_current_time()) + ".xlsx", index=False)


def add_report_id(report: Report) -> dict:
    """
    :param report:
    :return:
    """
    new_dict = {"Study #": report.report_id, "Laterality": report.laterality}
    new_dict.update(report.encoded)
    return new_dict


def change_unfiltered_to_dict(report):
    """
    :param report:
    :return:
    """
    new_dict = {"Study #": report.report_id, "Laterality": report.laterality}
    new_dict.update(report.preoperative_breast)
    new_dict.update(report.operative_breast)
    new_dict.update(report.operative_axilla)
    return new_dict


def reports_to_spreadsheet(reports: List[Report], path_to_output: str, type_of_report: str, function) -> pd.DataFrame:
    """
    :param function:
    :param type_of_report:
    :param path_to_output:
    :param reports:
    :return:
    """

    if not os.path.exists(path_to_output + "raw"):
        os.makedirs(path_to_output + "raw")

    dataframe_coded = pd.DataFrame([function(report) for report in reports])

    dataframe_coded.to_excel(
        path_to_output + "raw/" + type_of_report + "_output" + str(get_current_time()) + ".xlsx", index=False)

    return dataframe_coded


def raw_reports_to_spreadsheet(reports: List[Report], pdf_human_cols_path: str):
    """
    :param reports:
    :param pdf_human_cols_path:
    :return:
    """
    cols_to_find = import_tools.import_pdf_human_cols(pdf_human_cols_path)  # this is a dict

    def to_dataframe() -> (pd.DataFrame, list):
        """
        :return:
        """
        not_found = []
        cols = list(cols_to_find.values())
        rows_list = []
        for report in reports:
            report_id = report.report_id
            not_found_per_report = {report_id: []}
            row_dict = {"Study #": report_id, "Laterality": report.laterality}
            for col_name in cols:
                preop = report.preoperative_breast
                op_b = report.operative_breast
                op_ax = report.operative_axilla
                if col_name in preop:
                    row_dict[col_name] = preop[col_name]
                elif col_name in op_b:
                    row_dict[col_name] = op_b[col_name]
                elif col_name in op_ax:
                    row_dict[col_name] = op_ax[col_name]
                else:
                    not_found_per_report[report_id].append(col_name)
            rows_list.append(row_dict)
        dataframe = pd.DataFrame(rows_list)
        return dataframe, not_found

    to_spreadsheet(to_dataframe()[0], type_of_output="raw_output")
