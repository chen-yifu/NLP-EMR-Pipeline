"""
this file performs training on the pipeline to determine the best threshold value for the pipeline per column
"""
from typing import List, Set

import pandas as pd
import spacy

from pipeline.processing.encode_extractions import try_clean
from pipeline.utils.utils import get_current_time


def param_fitting_scispacy(extracted_df_path: str, baseline_df_path: str, code_book_path: str, start: float, end: float,
                           interval: float, report_id_col: str = "Study #",
                           results_path: str = "results_{}.xlsx".format(get_current_time()),
                           model: str = "en_core_sci_lg") -> pd.DataFrame:
    """
    :param results_path:
    :param end:
    :param start:
    :param report_id_col:
    :param baseline_df_path:
    :param extracted_df_path:
    :param interval:
    """
    nlp = spacy.load(model)
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

    # now need to do the same thing with columns
    extracted_cols = set(cleaned_extracted_df.columns)
    baseline_cols = set(cleaned_baseline_df.columns)
    common_cols = list(extracted_cols & baseline_cols)
    cleaned_extracted_df = cleaned_extracted_df.drop(
        columns=[col for col in cleaned_extracted_df if col not in common_cols])
    cleaned_baseline_df = cleaned_baseline_df.drop(
        columns=[col for col in cleaned_extracted_df if col not in common_cols])
    cleaned_extracted_df = cleaned_extracted_df.reindex(columns=common_cols)
    cleaned_baseline_df = cleaned_baseline_df.reindex(columns=common_cols)

    # now try to encode each column
    encoding_dict = []
    for column in common_cols:
        threshold = start
        while threshold <= end:
            metrics = {"column": column, "correct": 0, "different": 0, "missing": 0, "extra": 0, "total": 0}
            print("Now encoding {} at a threshold of {}".format(column, threshold))
            extracted_col = cleaned_extracted_df[column]
            baseline_col = cleaned_baseline_df[column]
            zipped_vals = zip(baseline_col, extracted_col)
            for extracted_val, baseline_val in zipped_vals:
                metrics["total"] += 1
                extracted_is_nan = pd.isna(extracted_val)
                baseline_is_nan = pd.isna(baseline_val)
                cleaned_extracted_val = try_clean(extracted_val)
                cleaned_baseline_val = try_clean(baseline_val)
                if cleaned_extracted_val == cleaned_baseline_val:
                    metrics["correct"] += 1
                elif extracted_is_nan:
                    metrics["missing"] += 1
                elif baseline_is_nan:
                    metrics["extra"] += 1
                else:
                    metrics["different"] += 1
            accuracy = metrics["correct"] / metrics["total"]
            print(
                "Using threshold of {}, {} correct, {} different, {} missing, {} extra, {} total -> {} accurate.".format(
                    threshold, metrics["correct"], metrics["different"], metrics["missing"], metrics["extra"],
                    metrics["total"], accuracy))
            encoding_dict.append(metrics)
            threshold += interval
    encoding_df = pd.DataFrame(encoding_dict)
    encoding_df.to_excel(results_path)
    return encoding_df


param_fitting_scispacy("../../../data/output/pathology_results/csv_files/raw_09-04-2021~1645.csv",
                       "../../../data/baselines/pathology_VZ.csv",
                       "../../../data/utils/operative_code_book.ods",
                       .6,
                       1,
                       .1)
param_fitting_scispacy("../../../data/output/operative_results/csv_files/raw_09-04-2021~1649.csv",
                       "../../../data/baselines/operative_VZ.csv",
                       "../../../data/utils/pathology_code_book.ods",
                       .6,
                       1,
                       .1)
