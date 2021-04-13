"""
🧬 file that contains the function that runs the emr pipeline
"""

from typing import List

import pandas as pd

from pipeline.archive.operative_pipeline.postprocessing.to_spreadsheet import reports_to_spreadsheet, add_report_id
from pipeline.archive.pathology_pipeline.preprocessing.isolate_sections import isolate_final_diagnosis_sections
from pipeline.archive.pathology_pipeline.processing.encode_extractions import encode_extractions_to_dataframe
from pipeline.postprocessing.highlight_differences import highlight_csv_differences
from pipeline.postprocessing.write_excel import save_dictionaries_into_csv_raw
from pipeline.preprocessing.extract_synoptic import clean_up_reports
from pipeline.preprocessing.resolve_ocr_spaces import preprocess_resolve_ocr_spaces
from pipeline.preprocessing.scanned_pdf_to_text import load_reports_into_pipeline
from pipeline.processing.encode_extractions import encode_extractions
from pipeline.processing.process_synoptic_general import process_synoptics_and_ids
from pipeline.processing.turn_to_values import turn_reports_extractions_to_values
from pipeline.utils.import_tools import get_input_paths, import_code_book, import_columns
from pipeline.utils.paths import get_paths
from pipeline.utils.regex_tools import synoptic_capture_regex
from pipeline.utils.report_type import ReportType
from pipeline.utils.utils import find_all_vocabulary, get_current_time


class EMRPipeline:
    """
    class representing a pipeline that can parse information from synoptic report
    """

    def __init__(self, start: int, end: int, report_name: str, report_ending: str, report_type: ReportType,
                 other_paths: dict = {}):
        """
        :param other_paths:
        :param report_ending:                      the file endings of the reports, all must be same
        :param report_name:                        what is the type of the report? pathology, surgical, operative
        :param start:                              the first report id
        :param end:                                the last report id
        :param report_type:                        the type of report being analyzed, is an Enum
        """
        self.start = start
        self.end = end
        self.report_name = report_name
        self.report_ending = report_ending
        self.other_paths = other_paths
        self.paths = get_paths(report_name, other_paths)
        self.code_book = import_code_book(self.paths["path to code book"])
        self.column_mappings = import_columns(self.paths["path to mappings"])
        self.pickle_path = self.paths["pickle path"] if "pickle path" in self.paths else None
        self.paths_to_pdfs = get_input_paths(start, end, path_to_reports=self.paths["path to reports"],
                                             report_str="{} " + report_ending)
        self.report_type = report_type
        if report_type is ReportType.ALPHA:
            report_ending = report_ending[:-3] + "txt"
        self.paths_to_reports_to_read_in = get_input_paths(start, end, path_to_reports=self.paths["path to reports"],
                                                           report_str="{} " + report_ending)

    def run_pipeline(self, baseline_versions: List[str], anchor: str, single_line_list: list = [], separator: str = ":",
                     use_separator_to_capture: bool = False, add_anchor: bool = False, multi_line_cols: list = [],
                     cols_to_skip: list = [], contained_capture_list: list = [], no_anchor_list: list = [],
                     anchor_list: list = [], print_debug: bool = True, max_edit_distance_missing: int = 5,
                     tools: dict = {}, max_edit_distance_autocorrect: int = 5, sep_list: list = [],
                     substitution_cost: int = 2, resolve_ocr: bool = True, do_training: bool = False,
                     start_threshold: float = .75, end_threshold: float = 1,
                     threshold_interval: float = .05) -> pd.DataFrame:
        """
        The starting function of the EMR pipeline. Reports must be preprocessed by Adobe OCR before being loaded into the
        pipeline if the values to be extracted are mostly numerical. Reports with values that are mostly alphabetical do not
        need to be preprocessed, as the pytesseract library will turn them into .txt files.

        :param threshold_interval:
        :param do_training:
        :param end_threshold:
        :param start_threshold:
        :param single_line_list:                   columns that have their values on the same line as the column (single line)
        :param use_separator_to_capture:           whether or not you want to use the separator for the regular pattern
        :param sep_list:                           columns that you want to use the separator to capture the value
        :param anchor_list:                        columns to add anchor to. use if add_anchor is False
        :param no_anchor_list:                     columns to not add anchor to. use if add_anchor is True
        :param anchor:                             the anchor that the regular pattern will look for to anchor to the start of page
        :param contained_capture_list:             columns that you want to use contained capture on
        :param add_anchor:                         whether or not you want to add anchor, default is False
        :param separator:                          what is used to separate the column and value, ex -> invasive carcinoma : negative
        :param tools:                              functions that other columns need for cleansing
        :param baseline_versions:                  the baseline version to compare to
        :param cols_to_skip:                       which columns to not put in the regex
        :param multi_line_cols:                    the columns in the report that span two lines
        :param print_debug:                        print debug statements in Terminal if True
        :param max_edit_distance_missing:          the maximum edit distance for searching for missing cell values
        :param max_edit_distance_autocorrect:      the maximum edit distance for autocorrecting extracted pairs for pathology
        :param substitution_cost:                  the substitution cost for edit distance for pathology
        :param resolve_ocr:                        resolve ocr white space if true
        :return:
        """
        timestamp = get_current_time()

        # try to read in the reports. if there is exception this is because the pdfs have to be turned into text
        # files first then try to read in again.

        reports_loaded_in_str = load_reports_into_pipeline(self.paths["path to input"], self.paths_to_pdfs,
                                                           self.paths_to_reports_to_read_in, self.start)

        medical_vocabulary = find_all_vocabulary([report.text for report in reports_loaded_in_str],
                                                 print_debug=print_debug, min_freq=40)

        if resolve_ocr:
            reports_loaded_in_str = preprocess_resolve_ocr_spaces(reports_loaded_in_str, print_debug=print_debug,
                                                                  medical_vocabulary=medical_vocabulary)

        # returns list[Report] with everything BUT encoded and not_found initialized
        cleaned_emr, ids_without_synoptic = clean_up_reports(emr_text=reports_loaded_in_str)

        synoptic_regex, regex_variable_mappings = synoptic_capture_regex(
            {k: v for k, v in self.column_mappings.items() if k.lower() not in cols_to_skip},
            capture_till_end_of_val_list=single_line_list,
            use_seperater_for_contained_capture=use_separator_to_capture,
            contained_capture_list=contained_capture_list,
            multi_line_cols_list=multi_line_cols,
            no_anchor_list=no_anchor_list,
            anchor=anchor,
            sep_list=sep_list,
            anchor_list=anchor_list,
            is_anchor=add_anchor)

        # this is the str of PDFs that do not contain any Synoptic Report section
        without_synoptics_strs_and_ids = [report for report in cleaned_emr if report.report_id in ids_without_synoptic]

        # If the PDF doesn't contain a synoptic section, use the Final Diagnosis section instead
        # this part is in development
        final_diagnosis_reports, ids_without_final_diagnosis = isolate_final_diagnosis_sections(
            without_synoptics_strs_and_ids,
            print_debug=print_debug)

        if print_debug:
            if len(ids_without_final_diagnosis) > 0:
                s = "Study IDs with neither Synoptic Report nor Final Diagnosis: {}".format(ids_without_final_diagnosis)
                print(s)

        filtered_reports, autocorrect_df = process_synoptics_and_ids(cleaned_emr,
                                                                     self.column_mappings,
                                                                     synoptic_regex,
                                                                     r"(?P<column>.*){}(?P<value>.*)".format(separator),
                                                                     print_debug=print_debug,
                                                                     max_edit_distance_missing=max_edit_distance_missing,
                                                                     max_edit_distance_autocorrect=max_edit_distance_autocorrect,
                                                                     substitution_cost=substitution_cost,
                                                                     tools=tools,
                                                                     regex_mappings=regex_variable_mappings,
                                                                     pickle_path=self.pickle_path)

        reports_with_values = turn_reports_extractions_to_values(filtered_reports, self.column_mappings)

        df_raw = save_dictionaries_into_csv_raw(reports_with_values, self.column_mappings,
                                                csv_path=self.paths["csv path raw"],
                                                print_debug=print_debug)

        if do_training:
            self.train_pipeline(baseline_versions, end_threshold, print_debug, self.report_name, reports_with_values,
                                start_threshold, threshold_interval, timestamp, tools)

        encoded_reports = encode_extractions(reports=reports_with_values, code_book=self.code_book, tools=tools,
                                             threshold=start_threshold)

        dataframe_coded = reports_to_spreadsheet(reports=encoded_reports, path_to_output=self.paths["path to output"],
                                                 type_of_report="coded", function=add_report_id)

        # this is just for now: to compare to the old encoding
        if self.report_type is ReportType.NUMERICAL:
            # https://regex101.com/r/RBWwBE/1
            # https://regex101.com/r/Gk4xv9/1

            dataframe_coded_old = encode_extractions_to_dataframe(df_raw, print_debug=print_debug)

            dataframe_coded_old.to_csv("../data/output/pathology_results/csv_files/old_encoding.csv", index=False)

            for baseline_version in baseline_versions:
                stats = highlight_csv_differences(
                    csv_path_coded="../data/output/pathology_results/csv_files/old_encoding.csv",
                    csv_path_human=self.paths["path to baselines"] + baseline_version,
                    output_excel_path="../data/output/pathology_results/excel_files/old_encoding_w_{}_{}.xlsx".format(
                        baseline_version[-6:-4],
                        timestamp),
                    report_type="Pathology", print_debug=print_debug)

                if print_debug:
                    print("\nOld encoding code 🧬 compared to {} -> Pipeline process finished.\nStats:{}".format(
                        baseline_version, stats))

        dataframe_coded.to_csv(self.paths["csv path coded"], index=False)

        for baseline_version in baseline_versions:
            compare_file_path = "compare_{}_{}_corD{}_misD{}_subC{}.xlsx".format(baseline_version[-6:-4],
                                                                                 timestamp,
                                                                                 max_edit_distance_autocorrect,
                                                                                 max_edit_distance_missing,
                                                                                 substitution_cost)

            output_excel_path = self.paths["path to output excel"] + compare_file_path

            stats, column_accuracies = highlight_csv_differences(csv_path_coded=self.paths["csv path coded"],
                                                                 csv_path_human=self.paths[
                                                                                    "path to baselines"] + baseline_version,
                                                                 report_type=self.report_name[
                                                                                 0].upper() + self.report_name[1:],
                                                                 output_excel_path=output_excel_path,
                                                                 print_debug=print_debug)

            if print_debug:
                print("\nUsing spacy, and {} with upper threshold of {} -> Stats: {}".format(baseline_version,
                                                                                             start_threshold,
                                                                                             stats))

        return autocorrect_df

    def train_pipeline(self, baseline_versions, end_threshold, print_debug, report_name,
                       reports_with_values, start_threshold, threshold_interval, timestamp, tools):
        """
        :param baseline_versions:
        :param end_threshold:
        :param print_debug:
        :param report_name:
        :param reports_with_values:
        :param start_threshold:
        :param threshold_interval:
        :param timestamp:
        :param tools:
        """
        threshold = start_threshold
        while threshold < end_threshold:
            for baseline_version in baseline_versions:
                print("Starting to encode with threshold of {}".format(threshold))
                encoded_reports = encode_extractions(reports=reports_with_values, code_book=self.code_book, tools=tools,
                                                     threshold=threshold)

                dataframe_coded = reports_to_spreadsheet(reports=encoded_reports,
                                                         path_to_output=self.paths["path to output"],
                                                         type_of_report="coded", function=add_report_id)

                dataframe_coded.to_csv(self.paths["csv path coded"], index=False)

                compare_file_path = "compare_{}_threshold_{}_{}.xlsx".format(baseline_version[-6:-4],
                                                                             threshold, timestamp)

                output_excel_path = self.paths["path to output excel"] + compare_file_path

                stats, column_accuracies = highlight_csv_differences(csv_path_coded=self.paths["csv path coded"],
                                                                     csv_path_human=self.paths[
                                                                                        "path to baselines"] + baseline_version,
                                                                     report_type=report_name[0].upper() + report_name[
                                                                                                          1:],
                                                                     output_excel_path=output_excel_path,
                                                                     print_debug=print_debug)

                if print_debug:
                    debug = "\nUsing spacy, and {} with upper threshold of {} -> Stats: {}"
                    print(debug.format(baseline_version, threshold, stats))
            threshold += threshold_interval
