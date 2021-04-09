"""
this file performs training on the pipeline to determine the best threshold value for the pipeline per column
"""
from typing import List, Set

import pandas as pd


def param_fitting_scispacy(extracted_df_path: str, baseline_df_path: str, code_book_path: str, start: float, end: float,
                           interval: float, report_id_col: str = "Study #") -> pd.DataFrame:
    """
    :param end:
    :param start:
    :param report_id_col:
    :param baseline_df_path:
    :param extracted_df_path:
    :param interval:
    """
    extracted_df = pd.read_csv(extracted_df_path)
    baseline_df = pd.read_csv(baseline_df_path)
    # try out threshold values per column.
    # will only use report ids that exist in both extracted df and baseline df
    extracted_report_ids = set(extracted_df[report_id_col])
    baseline_report_ids = set(baseline_df[report_id_col])
    common_report_ids = list(extracted_report_ids & baseline_report_ids)

    # dropping all row ids that are not common in extracted df and baseline
    cleaned_extracted_df = extracted_df[extracted_df[report_id_col].isin(common_report_ids)]
    cleaned_baseline_df = baseline_df[baseline_df[report_id_col].isin(common_report_ids)]


param_fitting_scispacy("../../../data/output/pathology_results/csv_files/raw_09-04-2021~1645.csv",
                       "../../../data/baselines/pathology_VZ.csv",
                       .6,
                       1,
                       .1)
param_fitting_scispacy("../../../data/output/operative_results/csv_files/raw_09-04-2021~1649.csv",
                       "../../../data/baselines/operative_VZ.csv",
                       .6,
                       1,
                       .1)
