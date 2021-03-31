"""
The pipeline for EMR
"""
import copy

from pandas import DataFrame
from pipeline.operative_pipeline.postprocessing.compare_excel import nice_compare
from pipeline.operative_pipeline.postprocessing.to_spreadsheet import reports_to_spreadsheet, change_unfiltered_to_dict, \
    add_report_id
from pipeline.postprocessing.encode_extractions import encode_extractions
from pipeline.preprocessing.extract_synoptic import clean_up_reports
from pipeline.preprocessing.scanned_pdf_to_text import convert_pdf_to_text, load_in_reports
from pipeline.pathology_pipeline.postprocessing.highlight_differences import highlight_csv_differences
from pipeline.pathology_pipeline.postprocessing.write_excel import save_dictionaries_into_csv_raw
from pipeline.pathology_pipeline.preprocessing.isolate_sections import isolate_final_diagnosis_sections
from pipeline.preprocessing.resolve_ocr_spaces import preprocess_resolve_ocr_spaces
from pipeline.pathology_pipeline.processing.encode_extractions import encode_extractions_to_dataframe
from pipeline.processing.process_synoptic_general import process_synoptics_and_ids
from pipeline.processing.turn_to_values import turn_reports_extractions_to_values
from pipeline.util.import_tools import import_pdf_human_cols_tuples, get_input_paths, import_code_book, import_columns
from pipeline.util.paths import get_paths
from pipeline.util.regex_tools import synoptic_capture_regex
from pipeline.util.report_type import ReportType
from pipeline.util.utils import find_all_vocabulary, get_current_time


def run_pipeline(start: int, end: int, report_type: ReportType, report_name: str, report_ending: str,
                 baseline_version: str, anchor: str, single_line_list: list = [], seperator: str = ":",
                 other_paths: dict = {}, use_seperator_to_capture: bool = False, is_anchor: bool = False,
                 multi_line_cols: list = [], cols_to_skip: list = [], contained_capture_list: list = [],
                 no_anchor_list: list = [], anchor_list: list = [], print_debug: bool = True,
                 max_edit_distance_missing: int = 5, tools: dict = {}, max_edit_distance_autocorrect_path: int = 5,
                 sep_list: list = [], substitution_cost_path: int = 2, resolve_ocr=True) -> DataFrame:
    """
    :param single_line_list:
    :param use_seperator_to_capture:
    :param sep_list:
    :param anchor_list:
    :param no_anchor_list:
    :param anchor:
    :param contained_capture_list:
    :param is_anchor:
    :param seperator:
    :param tools:                                   functions that other columns need for cleansing
    :param other_paths:                             other more specific paths
    :param baseline_version:                        the baseline version to compare to
    :param cols_to_skip:                            which columns to not put in the regex
    :param multi_line_cols:                         the columns in the report that span two lines
    :param report_ending:                           the file endings of the reports, all must be same
    :param report_name:                             what is the type of the report? pathology, surgical, operative
    :param start:                                   the first report id
    :param end:                                     the last report id
    :param report_type:                             the type of report being analyzed, is an Enum
    :param print_debug:                             print debug statements in Terminal if True
    :param max_edit_distance_missing:               the maximum edit distance for searching for missing cell values
    :param max_edit_distance_autocorrect_path:      the maximum edit distance for autocorrecting extracted pairs for pathology
    :param substitution_cost_path:                  the substitution cost for edit distance for pathology
    :param resolve_ocr:                             resolve ocr white space if true
    :return:
    """

    timestamp = get_current_time()
    paths = get_paths(report_name, baseline_version, other_paths)
    code_book = import_code_book(paths["path to code book"])
    paths_to_pdfs = get_input_paths(start, end, path_to_reports=paths["path to reports"],
                                    report_str="{} " + report_ending)
    if report_type is ReportType.TEXT:
        report_ending = report_ending[:-3] + "txt"

    lmao = "🐄"

    paths_to_reports_to_read_in = get_input_paths(start, end, path_to_reports=paths["path to reports"],
                                                  report_str="{} " + report_ending)

    compare_file_path = "compare_{}_corD{}_misD{}_subC{}_STAT.xlsx".format(timestamp,
                                                                           max_edit_distance_autocorrect_path,
                                                                           max_edit_distance_missing,
                                                                           substitution_cost_path)
    excel_path_highlight_differences = paths["path to output excel"] + compare_file_path

    # try to read in the reports. if there is exception this is because the pdfs have to be turned into text files first
    # then try to read in again.
    try:
        reports_loaded_in_str = load_in_reports(start=start, end=end, paths_to_r=paths_to_reports_to_read_in)
    except FileNotFoundError or Exception:
        convert_pdf_to_text(path_to_input=paths["path to input"], paths_to_pdfs=paths_to_pdfs,
                            paths_to_texts=paths_to_reports_to_read_in)
        reports_loaded_in_str = load_in_reports(start=start, end=end, paths_to_r=paths_to_reports_to_read_in)

    reports_strings_only = [report.text for report in reports_loaded_in_str]
    medical_vocabulary = find_all_vocabulary(reports_strings_only, print_debug=print_debug, min_freq=40)

    if resolve_ocr:
        reports_loaded_in_str = preprocess_resolve_ocr_spaces(reports_loaded_in_str, print_debug=print_debug,
                                                              medical_vocabulary=medical_vocabulary)

    # returns list[Report] with everything BUT encoded and not_found initialized
    cleaned_emr, ids_without_synoptic = clean_up_reports(emr_text=reports_loaded_in_str)

    column_mappings = import_columns(paths["path to mappings"])
    column_mappings_tuples = import_pdf_human_cols_tuples(paths["path to mappings"])

    synoptic_regex, regex_variable_mappings = synoptic_capture_regex(
        {k: v for k, v in column_mappings.items() if k.lower() not in cols_to_skip},
        single_line_list=single_line_list,
        use_seperater_for_contained_capture=use_seperator_to_capture,
        contained_capture_list=contained_capture_list,
        list_multi_line_cols=multi_line_cols,
        no_anchor_list=no_anchor_list,
        anchor=anchor,
        sep_list=sep_list,
        anchor_list=anchor_list,
        is_anchor=is_anchor)

    pickle_path = paths["pickle path"] if "pickle path" in paths else None

    # this is the str of PDFs that do not contain any Synoptic Report section
    without_synoptics_strs_and_ids = [report for report in cleaned_emr if
                                      report.report_id in ids_without_synoptic]

    # If the PDF doesn't contain a synoptic section, use the Final Diagnosis section instead
    final_diagnosis_reports, ids_without_final_diagnosis = isolate_final_diagnosis_sections(
        without_synoptics_strs_and_ids,
        print_debug=print_debug)

    if print_debug:
        if len(ids_without_final_diagnosis) > 0:
            s = "Study IDs with neither Synoptic Report nor Final Diagnosis: {}".format(ids_without_final_diagnosis)
            print(s)

    print(synoptic_regex)

    filtered_reports, autocorrect_df = process_synoptics_and_ids(cleaned_emr,
                                                                 column_mappings,
                                                                 synoptic_regex,
                                                                 r"(?P<column>.*){}(?P<value>.*)".format(seperator),
                                                                 print_debug=print_debug,
                                                                 max_edit_distance_missing=max_edit_distance_missing,
                                                                 max_edit_distance_autocorrect=max_edit_distance_autocorrect_path,
                                                                 substitution_cost=substitution_cost_path,
                                                                 tools=tools,
                                                                 regex_mappings=regex_variable_mappings,
                                                                 pickle_path=pickle_path)
    # split starts here
    if report_type is ReportType.NUMERICAL:
        # https://regex101.com/r/RBWwBE/1
        # https://regex101.com/r/Gk4xv9/1

        # making a deep copy
        reports_to_use_to_turn_into_vals = copy.deepcopy(filtered_reports)

        reports_to_use_to_turn_into_vals = turn_reports_extractions_to_values(reports_to_use_to_turn_into_vals,
                                                                              column_mappings)

        encoded_reports = encode_extractions(reports=reports_to_use_to_turn_into_vals, code_book=code_book, tools=tools)

        # turning coded to spreadsheets
        dataframe_coded = reports_to_spreadsheet(reports=encoded_reports, path_to_output=paths["path to output"],
                                                 type_of_report="coded", function=add_report_id)

        # doing nice comparison
        training_dict = nice_compare(baseline_version=baseline_version, pipeline_dataframe=dataframe_coded,
                                     baseline_path=paths["path to baseline"], path_to_outputs=paths["path to output"])

        print(training_dict)

        final_diagnosis_reports = []

        all_reports = filtered_reports + final_diagnosis_reports
        df_raw = save_dictionaries_into_csv_raw(all_reports,
                                                column_mappings_tuples,
                                                csv_path=paths["csv path raw"],
                                                print_debug=print_debug)

        df_coded = encode_extractions_to_dataframe(df_raw, print_debug=print_debug)

        df_coded.to_csv(paths["csv path coded"], index=False)

        stats = highlight_csv_differences(paths["csv path coded"], paths["path to baseline"],
                                          excel_path_highlight_differences, print_debug=print_debug)

        if print_debug:
            print("\nPipeline process finished.\nStats:{}".format(stats))

        return stats, autocorrect_df

    elif report_type is ReportType.TEXT:
        # https://regex101.com/r/XWffCF/1

        # raw to spreadsheet, no altering has been done
        reports_to_spreadsheet(filtered_reports, type_of_report="unfiltered_reports",
                               path_to_output=paths["path to output"],
                               function=change_unfiltered_to_dict)

        reports_with_values = turn_reports_extractions_to_values(filtered_reports, column_mappings)

        encoded_reports = encode_extractions(reports=reports_with_values, code_book=code_book, tools=tools)

        # turning coded to spreadsheets
        dataframe_coded = reports_to_spreadsheet(reports=encoded_reports, path_to_output=paths["path to output"],
                                                 type_of_report="coded", function=add_report_id)

        # doing nice comparison
        training_dict = nice_compare(baseline_version=baseline_version, pipeline_dataframe=dataframe_coded,
                                     baseline_path=paths["path to baseline"], path_to_outputs=paths["path to output"])

        return training_dict
