"""
2021 Yifu (https://github.com/chen-yifu) and Lucy (https://github.com/lhao03)
This file includes code that represents an EMRPipeline object.
"""
from copy import copy, deepcopy
from typing import List, Any, Tuple, Dict
import os
import pandas as pd
from pipeline.postprocessing.highlight_differences import highlight_csv_differences
from pipeline.postprocessing.write_csv_excel import save_dictionaries_into_csv_raw, reports_to_spreadsheet, \
    add_report_id
from pipeline.preprocessing.extract_synoptic import clean_up_reports
from pipeline.preprocessing.resolve_ocr_spaces import preprocess_resolve_ocr_spaces
from pipeline.preprocessing.scanned_pdf_to_text import load_reports_into_pipeline
from pipeline.processing.clean_text import filter_report
from pipeline.processing.encode_extractions import encode_extractions
from pipeline.processing.process_synoptic_general import process_synoptics_and_ids
from pipeline.processing.turn_to_values import turn_reports_extractions_to_values
from pipeline.utils.column import Column
from pipeline.utils.import_tools import get_input_paths, import_code_book, import_columns, get_acronyms
from pipeline.utils.paths import get_paths
from pipeline.utils.regex_tools import synoptic_capture_regex_
from pipeline.utils.report import Report
from pipeline.utils.report_type import ReportType
from pipeline.utils.utils import find_all_vocabulary, get_current_time, create_rules


class EMRPipeline:
    """
    class representing a pipeline that can parse information from synoptic report.
    """

    def __init__(self, start: int, end: int, report_name: str, report_ending: str, report_type: ReportType,
                 other_paths=None):
        """
        :param other_paths:                        any other paths the pipeline requires that is not in the paths func
        :param report_ending:                      the file endings of the reports, all must be same
        :param report_name:                        what is the type of the report? pathology, surgical, operative
        :param start:                              the first report id
        :param end:                                the last report id
        :param report_type:                        the type of report being analyzed, is an Enum
        """
        self.other_paths = other_paths if other_paths is None else {}
        self.start = start
        self.end = end
        self.report_name = report_name
        self.report_ending = report_ending
        self.other_paths = other_paths
        self.paths = get_paths(report_name, other_paths)
        self.code_book = import_code_book(self.paths["path to code book"])
        self.column_mappings = import_columns(self.paths["path to mappings"], self.paths["path to thresholds"],
                                              self.paths["path to regex rules"])
        self.pickle_path = self.paths["path to autocorrect"] if "path to autocorrect" in self.paths else None
        self.paths_to_pdfs = get_input_paths(start, end, path_to_reports=self.paths["path to reports"],
                                             report_str="{}" + report_ending)
        self.report_type = report_type
        if report_type is ReportType.ALPHA:
            report_ending = report_ending[:-3] + "txt"
        self.paths_to_reports_to_read_in = get_input_paths(start, end, path_to_reports=self.paths["path to reports"],
                                                           report_str="{}" + report_ending)
        flat_los = []
        for encodings in self.code_book.values():
            for encoding in encodings:
                for val in encoding.val:
                    flat_los += val.split()
        self.acronyms = get_acronyms(flat_los)
        self.current_regex_rules = deepcopy(list(list(self.column_mappings.values())[0].regular_pattern_rules.keys()))

    def run_pipeline(self, baseline_versions: List[str], anchor: str, single_line_list: list = [],
                     separator: str = ":", use_separator_to_capture: bool = False, add_anchor: bool = False,
                     val_on_next_line_cols_to_add: list = [], val_on_same_line_cols_to_add: list = [],
                     cols_to_skip: list = [], contained_capture_list: list = [],
                     no_anchor_list: list = [], anchor_list: list = [], print_debug: bool = True,
                     autocorrect_tools: dict = {}, max_edit_distance_missing: int = 5, encoding_tools: dict = {},
                     max_edit_distance_autocorrect: int = 5, sep_list: list = [], substitution_cost: int = 2,
                     resolve_ocr: bool = True, filter_func_args: Tuple = None, train_thresholds: bool = False,
                     train_regex: bool = False, filter_values: bool = False, start_threshold: float = 0.7,
                     end_threshold: float = 1, extraction_tools: list = [],
                     threshold_interval: float = 0.05) -> Tuple[Any, pd.DataFrame]:
        """
        The starting function of the EMR pipeline. Reports must be preprocessed by Adobe OCR before being loaded into
        the pipeline if the values to be extracted are mostly numerical. Reports with values that are mostly
        alphabetical do not need to be preprocessed, as the pytesseract library will turn them into .txt files.

        :param val_on_same_line_cols_to_add:   any columns that are not in the column mappings that you want to add to the regular pattern
        :param autocorrect_tools:              functions that will be used after pipeline has extracted values (to autocorrect extractions)
        :param extraction_tools:               functions to be used in the extraction process
        :param filter_values:                  whether or not to filter reports
        :param filter_func_args:               out of the column mappings, which feature to look for and remove the report from the pipeline process
        :param train_thresholds:               whether or not to train the thresholds
        :param train_regex:                    whether or not to train the regex
        :param threshold_interval:             what interval the pipeline should increment by in training
        :param end_threshold:                  where to stop training
        :param start_threshold:                base threshold for training
        :param single_line_list:               columns that have their values on the same line as the column (same line)
        :param use_separator_to_capture:       whether or not you want to use the separator for the regular pattern
        :param sep_list:                       columns that you want to use the separator to capture the value
        :param anchor_list:                    columns to add anchor to. use if add_anchor is False
        :param no_anchor_list:                 columns to not add anchor to. use if add_anchor is True
        :param anchor:                         the anchor that the regex will look for to anchor to the start of page
        :param contained_capture_list:         columns that you want to use contained capture on
        :param add_anchor:                     whether or not you want to add anchor, default is False
        :param separator:                      what separates the column and value, ex -> invasive carcinoma : negative
        :param encoding_tools:                 functions that other columns need for cleansing
        :param baseline_versions:              the baseline version to compare to
        :param cols_to_skip:                   which columns to not put in the regex
        :param val_on_next_line_cols_to_add:   the columns in the report that span two lines
        :param print_debug:                    print debug statements in Terminal if True
        :param max_edit_distance_missing:      the maximum edit distance for searching for missing cell values
        :param max_edit_distance_autocorrect:  the maximum edit distance for autocorrecting extracted pairs
        :param substitution_cost:              the substitution cost for edit distance
        :param resolve_ocr:                    resolve ocr white space if true
        :return:                               autocorrect results
        """
        timestamp = get_current_time()

        # try to read in the reports. if there is exception this is because the pdfs have to be turned into text
        # files first then try to read in again.

        reports_loaded_in_str = load_reports_into_pipeline(self.paths["path to input"], self.paths_to_pdfs,
                                                           self.paths_to_reports_to_read_in, self.start)

        medical_vocabulary = find_all_vocabulary([report.text for report in reports_loaded_in_str],
                                                 print_debug=print_debug, min_freq=int((self.end - self.start) / 2) - 1)

        if resolve_ocr:
            reports_loaded_in_str = preprocess_resolve_ocr_spaces(reports_loaded_in_str, print_debug=print_debug,
                                                                  medical_vocabulary=medical_vocabulary)

        # returns list[Report] with everything BUT encoded and not_found initialized
        cleaned_emr, ids_without_synoptic = clean_up_reports(emr_text=reports_loaded_in_str)

        if train_regex:
            regex_training_df = self.train_pipeline_regex(
                columns={k: v for k, v in self.column_mappings.items() if k.lower() not in cols_to_skip},
                val_on_same_line_cols_to_add=val_on_same_line_cols_to_add,
                val_on_next_line_cols_to_add=val_on_next_line_cols_to_add,
                anchor=anchor,
                cleaned_reports=cleaned_emr,
                separator=separator,
                max_edit_distance_missing=max_edit_distance_missing,
                max_edit_distance_autocorrect=max_edit_distance_autocorrect,
                substitution_cost=substitution_cost,
                autocorrect_tools=autocorrect_tools,
                extraction_tools=extraction_tools,
                timestamp=timestamp,
                baseline_versions=baseline_versions,
                filter_values=filter_values, start_threshold=start_threshold,
                encoding_tools=encoding_tools,
                filter_func_args=filter_func_args)
            print("Regex Training")
            print(regex_training_df)

        # synoptic_regex, regex_variable_mappings = synoptic_capture_regex(
        #     {k: v for k, v in self.column_mappings.items() if k.lower() not in cols_to_skip},
        #     capture_till_end_of_val_list=single_line_list,
        #     use_seperater_for_contained_capture=use_separator_to_capture,
        #     contained_capture_list=contained_capture_list,
        #     multi_line_cols_list=val_on_next_line_cols_to_add,
        #     no_anchor_list=no_anchor_list,
        #     anchor=anchor,
        #     sep_list=sep_list,
        #     anchor_list=anchor_list,
        #     is_anchor=add_anchor)
        #
        # print(synoptic_regex)
        # print(regex_variable_mappings)

        synoptic_regex, regex_variable_mappings = synoptic_capture_regex_(
            {k: v for k, v in self.column_mappings.items() if k.lower() not in cols_to_skip},
            val_on_same_line_cols_to_add=val_on_same_line_cols_to_add,
            val_on_next_line_cols_to_add=val_on_next_line_cols_to_add,
            anchor=anchor)

        print(synoptic_regex)
        print(regex_variable_mappings)

        filtered_reports, autocorrect_df = process_synoptics_and_ids(
            cleaned_emr,
            self.column_mappings,
            synoptic_regex,
            r"(?P<column>.*){}(?P<value>((?!.+({}|—)\?*)[\s\S])*)".format(separator, separator),
            print_debug=print_debug,
            max_edit_distance_missing=max_edit_distance_missing,
            max_edit_distance_autocorrect=max_edit_distance_autocorrect,
            substitution_cost=substitution_cost,
            autocorrect_tools=autocorrect_tools,
            regex_mappings=regex_variable_mappings,
            pickle_path=self.pickle_path,
            paths=self.paths,
            extraction_tools=extraction_tools)

        for report in filtered_reports:
            old_id = report.report_id
            id_end = self.report_ending[0]
            new_id = old_id + id_end if old_id[-1].isnumeric() else old_id[:-1] + id_end + old_id[-1]
            new_id = "".join(new_id.split())
            report.report_id = new_id

        if filter_func_args:
            filtered_reports = filter_report(filtered_reports, filter_func_args[0], filter_func_args[1],
                                             self.report_ending)

        reports_with_values = turn_reports_extractions_to_values(filtered_reports, self.column_mappings,
                                                                 list(self.acronyms))

        df_raw = save_dictionaries_into_csv_raw(reports_with_values, self.column_mappings,
                                                csv_path=self.paths["csv path raw"],
                                                print_debug=print_debug)

        if train_thresholds:
            threshold_training_df = self.train_pipeline_encodings(
                baseline_versions, end_threshold, print_debug, self.report_name, reports_with_values,
                start_threshold, threshold_interval, timestamp, encoding_tools, self.paths["path to output"],
                filter_values)
            print("Threshold Training")
            print(threshold_training_df)

        encoded_reports = encode_extractions(reports=reports_with_values,
                                             code_book=self.code_book,
                                             tools=encoding_tools,
                                             input_threshold=start_threshold,
                                             training=train_thresholds,
                                             columns=self.column_mappings,
                                             filter_values=filter_values,
                                             acronyms=self.acronyms)

        dataframe_coded = reports_to_spreadsheet(reports=encoded_reports,
                                                 path_to_output=self.paths["path to output"],
                                                 type_of_report="coded",
                                                 function=add_report_id)

        dataframe_coded.to_csv(self.paths["csv path coded"], index=False)

        stats = None

        if not baseline_versions:
            print("Reports have finished encoding.")
            return "Reports have finished encoding, no stats.", autocorrect_df

        for baseline_version in baseline_versions:
            compare_file_path = "compare_{}_{}_corD{}_misD{}_subC{}.xlsx".format(baseline_version[-6:-4],
                                                                                 timestamp,
                                                                                 max_edit_distance_autocorrect,
                                                                                 max_edit_distance_missing,
                                                                                 substitution_cost)

            output_excel_path = self.paths["path to output excel"] + compare_file_path

            stats, column_accuracies = highlight_csv_differences(
                csv_path_coded=self.paths["csv path coded"],
                csv_path_human=self.paths["path to baselines"] + baseline_version,
                report_type=self.report_name[0].upper() + self.report_name[1:],
                output_excel_path=output_excel_path,
                print_debug=print_debug,
                column_mappings=list(self.column_mappings.values()))

            if print_debug:
                print("\nUsing spacy, and compared with {} results are -> Stats: {}".format(baseline_version, stats))

        return stats, autocorrect_df

    def train_pipeline_encodings(self, baseline_versions: List[str], end_threshold: float, print_debug: bool,
                                 report_name: str, reports_with_values: List[Report], start_threshold: float,
                                 threshold_interval: float, timestamp: str, encoding_tools: dict, output_path: str,
                                 filter_values: bool) -> pd.DataFrame:
        """
        :param filter_values:
        :param output_path:
        :param baseline_versions:
        :param end_threshold:
        :param print_debug:
        :param report_name:
        :param reports_with_values:
        :param start_threshold:
        :param threshold_interval:
        :param timestamp:
        :param encoding_tools:
        """
        training = []
        best_thresholds = dict(
            (k, {"column": k,
                 "lowest best threshold": start_threshold,
                 "highest best threshold": start_threshold,
                 "threshold": start_threshold,
                 "same": float("-inf"), "extra": float("+inf"),
                 "remove_stopwords": "False"}) for k in self.code_book.keys())

        threshold = start_threshold
        while threshold < end_threshold:
            for baseline_version in baseline_versions:
                for remove_stopwords in [False]:
                    stopwords_print_debug = "removing stopwords" if remove_stopwords else "keeping stopwords"
                    print("Starting to encode with threshold of {} and {}".format(threshold, stopwords_print_debug))

                    encoded_reports = encode_extractions(reports=reports_with_values, code_book=self.code_book,
                                                         tools=encoding_tools, training=True,
                                                         columns=self.column_mappings,
                                                         input_threshold=threshold,
                                                         filter_values=filter_values)

                    dataframe_coded = reports_to_spreadsheet(reports=encoded_reports,
                                                             path_to_output=self.paths["path to output"],
                                                             type_of_report="coded", function=add_report_id)

                    dataframe_coded.to_csv(self.paths["csv path coded"], index=False)

                    compare_file_path = "compare_{}_threshold_{}_stopwords_{}_{}.xlsx".format(baseline_version[-6:-4],
                                                                                              threshold,
                                                                                              remove_stopwords,
                                                                                              timestamp)

                    output_excel_path = self.paths["path to output excel"] + compare_file_path

                    stats, column_accuracies = highlight_csv_differences(
                        csv_path_coded=self.paths["csv path coded"],
                        csv_path_human=self.paths["path to baselines"] + baseline_version,
                        report_type=report_name[0].upper() + report_name[1:],
                        output_excel_path=output_excel_path,
                        print_debug=print_debug,
                        column_mappings=list(self.column_mappings.values()))

                    if print_debug:
                        debug = "\nUsing spacy, and {} with upper threshold of {} and {} -> Stats: {}"
                        print(debug.format(baseline_version, threshold, stopwords_print_debug, stats))

                    col_acc = column_accuracies.items()

                    num_same = {"num": "num_same", "threshold": threshold}
                    num_same.update({k: acc["num_same"] for k, acc in col_acc if len(acc.keys()) == 4})

                    num_different = {"num": "num_different", "threshold": threshold,
                                     "remove_stopwords": str(remove_stopwords)}
                    num_different.update({k: acc["num_different"] for k, acc in col_acc if len(acc.keys()) == 4})

                    num_missing = {"num": "num_missing", "threshold": threshold,
                                   "remove_stopwords": str(remove_stopwords)}
                    num_missing.update({k: acc["num_missing"] for k, acc in col_acc if len(acc.keys()) == 4})

                    num_extra = {"num": "num_extra", "threshold": threshold, "remove_stopwords": str(remove_stopwords)}
                    num_extra.update({k: acc["num_extra"] for k, acc in col_acc if len(acc.keys()) == 4})

                    num_acc = {"num": "(same + empty) / (all except extra)", "threshold": threshold,
                               "remove_stopwords": str(remove_stopwords)}
                    num_acc.update(
                        {k: acc["num_same"] / (acc["num_same"] + acc["num_different"] + acc["num_missing"]) for k, acc
                         in
                         col_acc if len(acc.keys()) == 4})

                    training.append(num_same)
                    training.append(num_different)
                    training.append(num_missing)
                    training.append(num_extra)
                    training.append(num_acc)

                    for k, acc in column_accuracies.items():
                        if len(acc.keys()) == 4:
                            best = best_thresholds[k] if k in best_thresholds else None
                            if best and best["same"] <= acc["num_same"] and best["extra"] >= acc["num_extra"]:
                                # if the same is the same
                                if best["same"] == acc["num_same"] and best["extra"] == acc["num_extra"]:
                                    best["highest best threshold"] = threshold
                                    best["threshold"] = round(((best["highest best threshold"] + best[
                                        "lowest best threshold"]) / 2), 2)
                                    best.update({"remove_stopwords": str(remove_stopwords)})
                                # if same has increased
                                elif best["same"] < acc["num_same"] and best["extra"] > acc["num_extra"]:
                                    best["same"] = acc["num_same"]
                                    best["extra"] = acc["num_extra"]
                                    best["highest best threshold"] = threshold
                                    best["lowest best threshold"] = threshold
                                    best["threshold"] = threshold
                                    best.update({"remove_stopwords": str(remove_stopwords)})

            threshold += threshold_interval
            threshold = round(threshold, 3)

        if not os.path.exists(output_path + "training/"):
            os.makedirs(output_path + "training/")

        best_thresholds_df = pd.DataFrame(list(best_thresholds.values()))
        best_thresholds_df.to_excel(output_path + "training/best_training.xlsx")
        training_df = pd.DataFrame(training)
        training_df.to_excel(output_path + "training/all_training_{}_{}.xlsx".format(self.report_name, timestamp))
        return best_thresholds_df

    def train_pipeline_regex(self, columns: Dict[str, Column], val_on_same_line_cols_to_add: List[str],
                             val_on_next_line_cols_to_add: List[str], anchor: str,
                             cleaned_reports: List[Report], separator, max_edit_distance_missing,
                             max_edit_distance_autocorrect, substitution_cost, autocorrect_tools,
                             extraction_tools, timestamp, baseline_versions, filter_values, start_threshold,
                             encoding_tools, filter_func_args) -> pd.DataFrame:
        """
        :param columns:
        :param val_on_same_line_cols_to_add:
        :param val_on_next_line_cols_to_add:
        :param anchor:
        :param cleaned_reports:
        :param separator:
        :param max_edit_distance_missing:
        :param max_edit_distance_autocorrect:
        :param substitution_cost:
        :param autocorrect_tools:
        :param extraction_tools:
        :param timestamp:
        :param baseline_versions:
        :param filter_values:
        :param start_threshold:
        :param encoding_tools:
        :param filter_func_args:
        :return:
        """

        training_regex_rules_best_dict = {}
        for col_name, col in columns.items():
            training_regex_rules_best_dict[col_name] = {"same": float('-inf'), "missing": float('inf')}

        # test front cap
        front_cap_rules = [rule for rule in self.current_regex_rules if "val on" in rule[0:6]]
        # set adding to column
        add_to_col_rules = [rule for rule in self.current_regex_rules if "add" in rule[0:3]]
        # set end cap
        end_cap_rules = [rule for rule in self.current_regex_rules if "capture" in rule[0:8]]

        # make all possible regex rules
        training_rules = create_rules(front_cap_rules, add_to_col_rules, end_cap_rules)

        training_sets = [{} for _ in range(len(training_rules))]
        for index, training_set in enumerate(training_sets):
            for col_name, col in columns.items():
                col_copy = deepcopy(col)
                regular_pattern_rules_copy = deepcopy(training_rules[index])
                col_copy.regular_pattern_rules = regular_pattern_rules_copy
                training_set[col_name] = col_copy

        for index, training_set in enumerate(training_sets):
            print("On training set number", str(index + 1))
            cleaned_reports_copy = deepcopy(cleaned_reports)

            synoptic_regex, regex_variable_mappings = synoptic_capture_regex_(
                training_set,
                val_on_same_line_cols_to_add=val_on_same_line_cols_to_add,
                val_on_next_line_cols_to_add=val_on_next_line_cols_to_add,
                anchor=anchor)

            print(synoptic_regex)
            print(regex_variable_mappings)

            filtered_reports, autocorrect_df = process_synoptics_and_ids(
                cleaned_reports_copy,
                self.column_mappings,
                synoptic_regex,
                r"(?P<column>.*){}(?P<value>((?!.+({}|—)\?*)[\s\S])*)".format(separator, separator),
                max_edit_distance_missing=max_edit_distance_missing,
                max_edit_distance_autocorrect=max_edit_distance_autocorrect,
                substitution_cost=substitution_cost,
                autocorrect_tools=autocorrect_tools,
                regex_mappings=regex_variable_mappings,
                pickle_path=self.pickle_path,
                paths=self.paths,
                extraction_tools=extraction_tools)

            id_end = self.report_ending[0]
            for report in filtered_reports:
                old_id = report.report_id
                if id_end not in old_id:
                    new_id = old_id + id_end if old_id[-1].isnumeric() else old_id[:-1] + id_end + old_id[-1]
                    new_id = "".join(new_id.split())
                    report.report_id = new_id

            if filter_func_args:
                filtered_reports = filter_report(filtered_reports, filter_func_args[0], filter_func_args[1],
                                                 self.report_ending)

            reports_with_values = turn_reports_extractions_to_values(filtered_reports, self.column_mappings,
                                                                     list(self.acronyms))

            df_raw = save_dictionaries_into_csv_raw(reports_with_values, self.column_mappings,
                                                    csv_path=self.paths["csv path raw"])

            encoded_reports = encode_extractions(reports=reports_with_values,
                                                 code_book=self.code_book,
                                                 tools=encoding_tools,
                                                 input_threshold=start_threshold,
                                                 columns=self.column_mappings,
                                                 filter_values=filter_values,
                                                 acronyms=self.acronyms)

            dataframe_coded = reports_to_spreadsheet(reports=encoded_reports,
                                                     path_to_output=self.paths["path to output"],
                                                     type_of_report="coded",
                                                     function=add_report_id)

            dataframe_coded.to_csv(self.paths["csv path coded"], index=False)

            stats = None

            for baseline_version in baseline_versions:
                compare_file_path = "compare_{}_{}_corD{}_misD{}_subC{}.xlsx".format(baseline_version[-6:-4],
                                                                                     timestamp,
                                                                                     max_edit_distance_autocorrect,
                                                                                     max_edit_distance_missing,
                                                                                     substitution_cost)

                output_excel_path = self.paths["path to output excel"] + compare_file_path

                stats, column_accuracies = highlight_csv_differences(
                    csv_path_coded=self.paths["csv path coded"],
                    csv_path_human=self.paths["path to baselines"] + baseline_version,
                    report_type=self.report_name[0].upper() + self.report_name[1:],
                    output_excel_path=output_excel_path,
                    column_mappings=list(self.column_mappings.values()))

                for col, acc in column_accuracies.items():
                    if col in training_set.keys():
                        same = acc["num_same"] if "num_same" in acc.keys() else 0
                        missing = acc["num_missing"] if "num_missing" in acc.keys() else 0
                        training_set[col].regular_pattern_rules["same"] = same
                        training_set[col].regular_pattern_rules["missing"] = missing
                        # check if its better
                        if col in training_regex_rules_best_dict.keys():
                            og_same = training_regex_rules_best_dict[col]["same"]
                            og_missing = training_regex_rules_best_dict[col]["missing"]
                            if og_same <= same and og_missing >= missing:
                                training_regex_rules_best_dict[col] = training_set[col].regular_pattern_rules

        training_regex_rules_list = []
        for col_name, rules in training_regex_rules_best_dict.items():
            best_rules_dict = {"col": col_name}
            best_rules_dict.update(rules)
            training_regex_rules_list.append(best_rules_dict)
        training_regex_rules_df = pd.DataFrame(training_regex_rules_list)
        training_regex_rules_df.to_csv(self.paths["path to regex rules"], index=False)
        return training_regex_rules_df
