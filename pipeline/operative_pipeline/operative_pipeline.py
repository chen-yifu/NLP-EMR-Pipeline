import os
from typing import List

from pipeline.operative_pipeline.postprocessing.compare_excel import nice_compare
from pipeline.operative_pipeline.postprocessing.to_spreadsheet import reports_to_spreadsheet, change_unfiltered_to_dict, \
    raw_reports_to_spreadsheet, add_report_id
from pipeline.operative_pipeline.preprocessing.extract_cols import extract_cols
from pipeline.operative_pipeline.preprocessing.extract_synoptic import clean_up_reports
from pipeline.operative_pipeline.preprocessing.scanned_pdf_to_text import load_in_pdfs, load_in_txts
from pipeline.operative_pipeline.processing.encode_extractions import code_extractions
from pipeline.operative_pipeline.processing.extract_extractions import get_general_extractions


def run_operative_pipeline(start: int, end: int, skip: List[int],
                           path_to_outputs: str = "../data/outputs/",
                           path_to_ocr: str = "../data/outputs/results_many/",
                           path_to_reports: str = "../data/reports_many/",
                           path_to_code_book: str = "../data/inputs/operative_code_book.ods",
                           path_to_pdf_human_cols: str = "../data/inputs/pdf_cols_human_cols.ods",
                           baseline_version: str = "data_collection_baseline_VZ_48",
                           baseline_path: str = "../data/inputs/baselines/",
                           path_to_weights: str = "../data/outputs/training_metrics/params/tuning.csv",
                           substitution_cost: int = 1,
                           largest_cost: int = 4) -> dict:
    """
    :param path_to_ocr:
    :param path_to_weights:
    :param substitution_cost:
    :param largest_cost:
    :param skip:
    :param baseline_path:
    :param baseline_version:
    :param path_to_code_book:
    :param path_to_pdf_human_cols:
    :param path_to_outputs:
    :param start:
    :param end:
    :param path_to_reports:
    """
    # this only needed to run once. converts pdfs to images that can be changed to text with ocr
    if not os.path.exists(path_to_ocr):
        load_in_pdfs(start=start, end=end, skip=skip, path_to_reports=path_to_reports, path_to_ocr=path_to_ocr)

    uncleaned_emr = load_in_txts(start=start, end=end, skip=skip,
                                 path_to_txt=path_to_ocr)  # returns list[Report] with only report and id

    cleaned_emr = clean_up_reports(emr_text=uncleaned_emr)  # returns list[Report] with everything but laterality,

    # and all the subsections are lists
    studies_with_general_extractions = get_general_extractions(list_reports=cleaned_emr)

    # raw to spreadsheet, no altering has been done
    reports_to_spreadsheet(studies_with_general_extractions, type_of_report="unfiltered_reports",
                           path_to_output=path_to_outputs,
                           function=change_unfiltered_to_dict)

    for report in studies_with_general_extractions:
        print(report.report_id)
        print(report.preoperative_breast)
        print(report.operative_breast)
        print(report.operative_axilla)
        print(report.advanced)

    studies_with_cleaned_extractions = extract_cols(reports=studies_with_general_extractions,
                                                    pdf_human_cols_path=path_to_pdf_human_cols)
    # turning raw text values into spreadsheet
    raw_reports_to_spreadsheet(reports=studies_with_cleaned_extractions, pdf_human_cols_path=path_to_pdf_human_cols)

    # changing the raw text into codes
    encoded_reports = code_extractions(reports=studies_with_cleaned_extractions, substitution_cost=substitution_cost,
                                       largest_cost=largest_cost, code_book_path=path_to_code_book,
                                       path_to_weights=path_to_weights)

    # turning coded to spreadsheets
    dataframe_coded = reports_to_spreadsheet(reports=encoded_reports, path_to_output=path_to_outputs,
                                             type_of_report="coded", function=add_report_id)

    # doing nice comparison
    training_dict = nice_compare(baseline_version=baseline_version, pipeline_dataframe=dataframe_coded,
                                 baseline_path=baseline_path,
                                 path_to_outputs=path_to_outputs)

    return training_dict
