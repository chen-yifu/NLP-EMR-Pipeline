"""
processes report and finds column value pairs
"""
import re
import string
from collections import defaultdict
from typing import Dict, List, Tuple
from nltk import edit_distance
from nltk.corpus import stopwords
from pipeline.processing.columns import load_excluded_columns_as_list
from pipeline.processing.clean_text import cleanse_column, cleanse_value
from pipeline.utils.column import Column
from pipeline.utils.report import Report
import pandas as pd
from pipeline.utils.report_type import ReportType

table = str.maketrans(dict.fromkeys(string.punctuation))
stop_words = set(stopwords.words('english'))


def get_extraction_specific_regex(unfiltered_str: str, synoptic_report_regex: str) -> dict:
    """
    Extracts information from the report using the generated regex. Removes captures that are None or "". Does not clean the data.

    :param unfiltered_str:                 the report to be looked at
    :param synoptic_report_regex:          the regex pattern to be used
    :return:
    """
    matches = re.finditer(synoptic_report_regex, unfiltered_str, re.MULTILINE)
    pairs = [(m.groupdict()) for m in matches]
    filtered_pairs = {}
    for unfiltered_dict in pairs:
        unfiltered_dict = {k: v for k, v in unfiltered_dict.items() if v is not None}
        filtered_pairs.update(unfiltered_dict)
    return filtered_pairs


def get_generic_extraction_regex(unfiltered_str: str, regex: str, is_text: bool = False, tools: dict = {}) -> dict:
    """
    Extracts information from the generic capture regex. Cleans out values that are None or "" and performs cleaning on the column and value.

    :param tools:               dictionary of functions that certain columns may need to use
    :param is_text:             whether or not the report is ReportType.TEXT or NUMERICAL
    :param unfiltered_str:      the report that the regex is to be used on
    :param regex:               the generic regex to be used
    :return:                    dictionary of the cleaned pairs
    """
    matches = re.finditer(regex, unfiltered_str, re.MULTILINE)
    generic_pairs = {}
    for m in matches:
        cleaned_column = cleanse_column(m["column"], is_text)
        func = tools[cleaned_column] if cleaned_column in tools.keys() else None
        cleaned_value = cleanse_value(m["value"], is_text, func)
        generic_pairs[cleaned_column] = cleaned_value
    return generic_pairs


def find_nearest_alternative(original_col, possible_candidates: List[str], study_id, value,
                             list_of_dict_with_stats: List[dict], is_text: bool, pickle_path: str = None,
                             max_edit_distance=2,
                             substitution_cost=1):
    """
    find the nearest alternative by choosing the element in possible_candidates with nearest edit distance to source
    if multiple candidates have the nearest distance, return the first candidate by position

    :param is_text:
    :param pickle_path:              path to data that GUI generates if a user is able to select columns to exclude.
    :param list_of_dict_with_stats:  dict of stats of column corrections
    :param original_col:             the original source
    :param possible_candidates       possible strings that the source string could be
    :param study_id:                 study id
    :param value:                    the original value inside the cell
    :param max_edit_distance:        maximum distance allowed between source and candidate
    :param substitution_cost:        cost to substitute a character instead of inserting/removing
    :return:                         candidate that is most similar to source, None if exceeds max_edit_distance
    """
    # get a list of excluded source-target column name pairs that we saved earlier
    all_excluded_columns = load_excluded_columns_as_list(pickle_path=pickle_path) if pickle_path else []
    excluded_columns = [tupl[1] for tupl in all_excluded_columns if tupl[0] == original_col]
    possible_candidates = list(set(possible_candidates) - set(excluded_columns))
    original_col = cleanse_column(original_col, is_text)
    min_dist = float("inf")
    res = None
    for c in possible_candidates:
        clean_source = original_col.replace(" ", "")
        clean_c = c.replace(" ", "")
        dist = edit_distance(clean_source, clean_c, substitution_cost=substitution_cost)
        if dist < min_dist:
            res = c
            min_dist = dist
    if min_dist > max_edit_distance:
        return None

    # add the auto-correct information to DataFrame
    if res != original_col:
        headers = ["Study ID", "Original Column", "Corrected Column", "Edit Distance", "Extracted Data"]
        extracted_stats = [study_id, original_col, res, edit_distance(original_col, res),
                           str(value).replace("\n", " ")]
        list_of_dict_with_stats.append(dict(zip(headers, extracted_stats)))

    return res


def autocorrect_columns(correct_col_names, extractions_so_far, study_id, list_of_dict_with_stats, pickle_path, is_text,
                        tools: dict, max_edit_distance=5, substitution_cost=2):
    """
    using a list of correct column names, autocorrect potential typos (that resulted from OCR) in column names

    :param tools:                        functions that some columns may use for cleaning
    :param pickle_path:                  path to pickled data from GUI
    :param correct_col_names:            a list of correct column names
    :param extractions_so_far:           extracted generic key-value pairs from synoptic reports
    :param study_id:                     the study id of the dictionary
    :param list_of_dict_with_stats:      save the auto-correct activities to be shown on GUI
    :param max_edit_distance:            maximum distance allowed between source and candidate
    :param substitution_cost:            cost to substitute a character instead of inserting/removing
    :return:                             dict with auto-corrected column names
    """
    columns = list(extractions_so_far.keys())
    for col in columns:
        if col in correct_col_names:  # do nothing if key is correct
            continue
        else:
            nearest_column = find_nearest_alternative(col, correct_col_names, study_id, extractions_so_far[col],
                                                      list_of_dict_with_stats, is_text=is_text,
                                                      max_edit_distance=max_edit_distance,
                                                      substitution_cost=substitution_cost, pickle_path=pickle_path)
            # if the nearest column is already extracted, find the next alternative
            while nearest_column is not None and nearest_column in extractions_so_far.keys():
                correct_col_names.remove(nearest_column)
                nearest_column = find_nearest_alternative(col, correct_col_names, study_id, extractions_so_far[col],
                                                          list_of_dict_with_stats, is_text=is_text,
                                                          max_edit_distance=max_edit_distance,
                                                          substitution_cost=substitution_cost,
                                                          pickle_path=pickle_path)
            # copy the value from incorrect column name to correct column name
            if nearest_column:
                in_tools = nearest_column.lower() in tools.keys()
                cleansed_val = cleanse_value(extractions_so_far[col], is_text,
                                             tools[nearest_column]) if in_tools else cleanse_value(
                    extractions_so_far[col], is_text)
                extractions_so_far[nearest_column] = cleansed_val

    try:
        # resolve column that have multiple aliases
        # the column "Total LN Examined" could be either, but keep only one
        if (extractions_so_far["number of lymph nodes examined"] != ""):
            extractions_so_far["number of lymph nodes examined (sentinel and nonsentinel)"] = extractions_so_far[
                "number of lymph nodes examined"]
            del extractions_so_far["number of lymph nodes examined"]
        # if number of foci isn't found, use tumour focality
        if extractions_so_far["number of foci"] == "":
            extractions_so_far["number of foci"] = extractions_so_far["tumour focality"]
        # if in situ type is not found, use histologic type
        if extractions_so_far["in situ component type"] == "":
            extractions_so_far["in situ component type"] = extractions_so_far["histologic type"]
        # if in situ component is not found, use histologic type
        if extractions_so_far["in situ component"] == "":
            extractions_so_far["in situ component"] = extractions_so_far["histologic type"]
    except KeyError or Exception:
        pass
    return extractions_so_far


def process_synoptic_section(synoptic_report_str: str, report_id: str, report_type: ReportType, pickle_path: str,
                             column_mappings: Dict[str, Column], list_of_dict_with_stats: List[dict],
                             regex_mappings: Dict[str, List[str]], specific_regex: str, general_regex: str,
                             tools: dict = {}, print_debug: bool = True, max_edit_distance_missing=5,
                             max_edit_distance_autocorrect=5, substitution_cost=2, skip_threshold=0.95) -> dict:
    """
    :param pickle_path:                        path to pickled data via GUI
    :param column_mappings:                    human columns and report columns where that inforamtion can be found
    :param report_type:                        enum of either TEXT or NUMERICAL
    :param substitution_cost:                  cost for a letter substitution
    :param specific_regex:                     regular pattern that was generated earlier by synoptic_capture_regex
    :param general_regex:                      general regular pattern based on the separator
    :param regex_mappings:                     the variables that were made earlier for regular pattern mapped to their columns
    :param tools:                              functions that columns may need to use for cleaning
    :param synoptic_report_str:                synoptic report section
    :param report_id:                          the study id of this report
    :param column_mappings:                    first str is col name from PDF, second str is col from Excel
    :param list_of_dict_with_stats:            save the auto-corrected columns into this DataFrame
    :param print_debug:                        print debug statements in Terminal if true
    :param max_edit_distance_missing:          maximum edit distance allowed when finding missing columns
    :param max_edit_distance_autocorrect:      maximum edit distance allowed when auto-correcting columns
    :param skip_threshold:                     between 0 and 1, specifies the percentage of max missing columns
    :return:                                   extracted data, represented by dictionary {column: value}
    """
    # checking if is text or numerical
    is_text = True if report_type is ReportType.ALPHA else False

    # todo
    def missing_columns(correct_cols: List[str], cols_so_far: List[str]):
        """
        :param correct_cols:
        :param cols_so_far:
        :return:
        """
        missing = list(set(correct_cols) - set(cols_so_far))
        for pdf_col in column_mappings.values():
            for csf in cols_so_far:
                primary_cols = pdf_col.cleaned_primary_report_col
                if csf in primary_cols:
                    for pcol in primary_cols:
                        try:
                            missing.remove(pcol)
                        except ValueError:
                            pass
        return missing

    # adding a "-" to match header
    synoptic_report_str = "- " + synoptic_report_str

    # autogenerated regex based on columns
    specific_pairs = get_extraction_specific_regex(synoptic_report_str, specific_regex)

    result = defaultdict(str)

    for key, val in specific_pairs.items():
        pdf_key = regex_mappings[key][-1].lower()
        in_tools = pdf_key in tools.keys()
        val = cleanse_value(val, is_text, function=tools[pdf_key]) if in_tools else cleanse_value(val, is_text)
        result[regex_mappings[key][-1]] = val

    # save study_id
    result["study"] = report_id

    # calculate the proportion of missing columns, if it's above skip_threshold, then return None immediately
    correct_col_names = []
    for pdf_cols in column_mappings.values():
        correct_col_names += pdf_cols.cleaned_primary_report_col

    # if too many columns are missing, we probably isolated a section with unexpected template,
    # so return nothing and exclude from result
    columns_found = [k.lower().translate(table) for k in result.keys() if k and result[k] != ""]
    columns_missing = missing_columns(correct_col_names, columns_found)

    try:
        percentage_missing = len(columns_missing) / len(correct_col_names)
        if percentage_missing > skip_threshold:
            if print_debug:
                print("Ignored study id {} because too many columns are missing."
                      " (does not have a synoptic report or its synoptic report isn't normal)".format(report_id))
    except ZeroDivisionError or Exception:
        pass

    # auto-correct the matches by using a predefined list of correct column names in "column_mappings"
    result = autocorrect_columns(correct_col_names, result, report_id, list_of_dict_with_stats, is_text=is_text,
                                 max_edit_distance=max_edit_distance_autocorrect,
                                 substitution_cost=substitution_cost, pickle_path=pickle_path, tools=tools)

    generic_pairs = get_generic_extraction_regex(synoptic_report_str, general_regex, is_text)

    # resolve redundant spaces caused by OCR
    for col, val in generic_pairs.items():
        col = re.sub(" *-? +", " ", col).strip().lower()
        val = re.sub(" +", " ", val).strip()
        nearest_column = find_nearest_alternative(col, columns_missing, report_id, val, list_of_dict_with_stats,
                                                  max_edit_distance=max_edit_distance_missing, is_text=is_text,
                                                  substitution_cost=substitution_cost,
                                                  pickle_path=pickle_path)
        if nearest_column in columns_missing:
            in_tools = nearest_column in tools
            cleansed_val = cleanse_value(val, is_text, tools[nearest_column]) if in_tools else cleanse_value(val,
                                                                                                             is_text)
            result[nearest_column] = cleansed_val
        elif nearest_column:
            raise ValueError("Should never reached this branch. Nearest column is among possible candidates")

    spaceless_synoptic_report = synoptic_report_str.replace(" ", "")
    if "Nolymphnodespresent" in spaceless_synoptic_report:
        result["number of lymph nodes examined (sentinel and nonsentinel)"] = "0"
        result["number of sentinel nodes examined"] = "0"
        result["micro / macro metastasis"] = None
        result["number of lymph nodes with micrometastases"] = None
        result["number of lymph nodes with macrometastases"] = None
        result["size of largest metastatic deposit"] = None

    return result


def process_synoptics_and_ids(unfiltered_reports: List[Report], column_mappings: Dict[str, Column], specific_regex: str,
                              general_regex: str, regex_mappings: Dict[str, List[str]], pickle_path, tools: dict = {},
                              print_debug=True, max_edit_distance_missing: int = 5,
                              max_edit_distance_autocorrect: int = 5,
                              substitution_cost: int = 2) -> Tuple[List[Report], pd.DataFrame]:
    """
    process and extract data from a list of synoptic reports by using regular expression

    :param pickle_path:                    path to columns you want to exclude from autocorrect if applicable
    :param column_mappings:                dict of human col name mapped to Column object
    :param max_edit_distance_autocorrect:  the maximum edit distance for autocorrecting extracted pairs
    :param substitution_cost:              the substitution cost for edit distance
    :param max_edit_distance_missing:      max allowed edit distance to find missing cells
    :param regex_mappings:                 the mappings of columns to their regex variables
    :param general_regex:                  a regular pattern that extracts column and values
    :param tools:                          a dictionary of column names mapped to functions to act on any values of that column
    :param specific_regex:                 the regex pattern generated earlier in the pipeline based on the user input columns
    :param unfiltered_reports:             synoptic sections and study IDs
    :param column_mappings:                first str is col name from PDF, second str is col from Excel
    :param print_debug:                    print debug statements in Terminal if True
    :return:                               extracted data of the form (col_name: value)
    :return:                               the auto-correct information to be shown
    """

    result = []
    if print_debug:
        s = "\nProcessing synoptic report sections..."
        print(s)

    list_of_dict_with_stats = []

    for report in unfiltered_reports:
        cleaned_text = report.text.strip().replace(" is ", ":")
        report.extractions = process_synoptic_section(cleaned_text, report.report_id, report.report_type, pickle_path,
                                                      column_mappings, list_of_dict_with_stats,
                                                      regex_mappings, specific_regex, general_regex, tools,
                                                      max_edit_distance_missing=max_edit_distance_missing,
                                                      max_edit_distance_autocorrect=max_edit_distance_autocorrect,
                                                      substitution_cost=substitution_cost)

        report.extractions.update({"laterality": report.laterality})
        report.extractions = {" ".join(k.translate(table).lower().strip().split()): v for k, v in
                              report.extractions.items()}
        result.append(report)
        print(report.report_id)
        print(report.extractions)

    # sort DataFrame by study ID
    df_with_stats = pd.DataFrame(list_of_dict_with_stats)
    df_with_stats.sort_values("Study ID")

    if print_debug:
        s = "Auto-correct Information:\n" + df_with_stats.to_string()
        print(s)

    return [report for report in result if report.extractions], df_with_stats
