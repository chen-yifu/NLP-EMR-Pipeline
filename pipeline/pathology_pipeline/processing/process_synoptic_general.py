import re
import string
from collections import defaultdict
from typing import Dict, List, Pattern, Tuple
from nltk import edit_distance
from nltk.corpus import stopwords

from pipeline.util.report import Report
import pandas as pd

from pipeline.util.report_type import ReportType

table = str.maketrans(dict.fromkeys(string.punctuation))
stop_words = set(stopwords.words('english'))


def get_extraction_specific_regex(unfiltered_str: str, synoptic_report_regex: Pattern[str]) -> dict:
    """
    :param unfiltered_str:
    :param mappings:
    :param synoptic_report_regex:
    :return:
    """
    pairs = [(m.groupdict()) for m in synoptic_report_regex.finditer(unfiltered_str)]
    filtered_pairs = {}
    for unfiltered_dict in pairs:
        unfiltered_dict = {k: v for k, v in unfiltered_dict.items() if v is not None}
        filtered_pairs.update(unfiltered_dict)
    return filtered_pairs


def get_generic_extraction_regex(unfiltered_str: str, regex: str) -> dict:
    """
    :param unfiltered_str:
    :param regex:
    :return:
    """
    matches = re.finditer(regex, unfiltered_str, re.MULTILINE)
    generic_pairs = {}
    for m in matches:
        cleaned_column = cleanse_value(m["column"])
        cleaned_value = cleanse_value(m["value"])
        generic_pairs[cleaned_column] = cleaned_value
    return generic_pairs


def cleanse_column(col: str, remove_num: bool = False) -> str:
    """
    cleanse the column by removing "-" and ":"
    :param col:      raw column
    :return:         cleansed column
    """
    col = re.sub(r"^\s*-\s*", "", col)  # remove "-"
    col = re.sub(r":\s*$", "", col)  # remove ":"
    if remove_num:
        return " ".join([w for w in col.split() if w.isalpha()]).lower().strip().translate(table)
    return col.strip().lower().translate(table)


def cleanse_value(val: str, remove_nums: bool = False, function=None) -> str:
    """
    cleanse the value by removing linebreaks
    :param remove_nums:
    :param function:
    :param val:      raw value
    :return:         cleansed value
    """
    if remove_nums:
        return " ".join([w for w in val.split() if w.isalpha()]).replace("\n", " ").strip().lower().translate(table)
    return function(val) if function else val.replace("\n", " ").strip().lower().translate(table)


def process_synoptics_and_ids(unfiltered_reports: List[Report], column_mappings: List[Tuple[str, str]],
                              specific_regex: str, general_regex: str, regex_mappings: Dict[str, List[str]],
                              tools: dict = {}, print_debug=True, max_edit_distance_missing=5,
                              max_edit_distance_autocorrect=5,
                              substitution_cost=2) -> Tuple[List[Report], pd.DataFrame]:
    """
    process and extract data from a list of synoptic reports by using regular expression

    :param max_edit_distance_autocorrect:
    :param substitution_cost:
    :param max_edit_distance_missing:      max allowed edit distance to find missing cells
    :param regex_mappings:
    :param general_regex:
    :param tools:
    :param specific_regex:
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

    # split the synoptic report into multiple sub-sections using ALL-CAPITALIZED headings as delimiter
    for report in unfiltered_reports:
        report.extractions = process_synoptic_section(report.text, report.report_id, report.report_type,
                                                      column_mappings, list_of_dict_with_stats, regex_mappings,
                                                      specific_regex, general_regex, tools,
                                                      max_edit_distance_missing=max_edit_distance_missing,
                                                      max_edit_distance_autocorrect=max_edit_distance_autocorrect,
                                                      substitution_cost=substitution_cost)
        result.append(report)

    # sort DataFrame by study ID
    df_with_stats = pd.DataFrame(list_of_dict_with_stats)
    df_with_stats.sort_values("Study ID")

    if print_debug:
        s = "Auto-correct Information:\n" + df_with_stats.to_string()
        print(s)

    return [report for report in result if report.extractions], df_with_stats


def process_synoptic_section(synoptic_report_str: str, study_id: str, report_type: ReportType,
                             column_mappings: List[Tuple[str, str]], list_of_dict_with_stats: List[dict],
                             regex_mappings: Dict[str, List[str]], specific_regex: str, general_regex: str,
                             tools: dict = {}, print_debug: bool = True, max_edit_distance_missing=5,
                             max_edit_distance_autocorrect=5, substitution_cost=2, skip_threshold=0.95) -> dict:
    """
    :param report_type:
    :param substitution_cost:
    :param specific_regex:
    :param general_regex:
    :param regex_mappings:
    :param tools:
    :param synoptic_report_str:                synoptic report section
    :param study_id:                           the study id of this report
    :param column_mappings:                    first str is col name from PDF, second str is col from Excel
    :param list_of_dict_with_stats:            save the auto-corrected columns into this DataFrame
    :param print_debug:                        print debug statements in Terminal if true
    :param max_edit_distance_missing:          maximum edit distance allowed when finding missing columns
    :param max_edit_distance_autocorrect:      maximum edit distance allowed when auto-correcting columns
    :param skip_threshold:                     between 0 and 1, specifies the percentage of max missing columns
    :return:                                   extracted data, represented by dictionary {column: value}
    """

    # autogenerated regex based on columns
    specific_pairs = get_extraction_specific_regex(synoptic_report_str, re.compile(specific_regex))

    changed_keys_pairs = {}

    for key, val in specific_pairs.items():
        val = cleanse_value(val, function=tools[key]) if key in tools else cleanse_value(val)
        changed_keys_pairs[regex_mappings[key][-1].translate(table)] = val

    # output placeholder
    result = defaultdict(str)
    result.update(changed_keys_pairs)

    # save study_id
    result["study_id"] = study_id

    # calculate the proportion of missing columns, if it's above skip_threshold, then return None immediately
    correct_col_names = [pdf_col for (pdf_col, excel_col) in column_mappings]

    # if too many columns are missing, we probably isolated a section with unexpected template,
    # so return nothing and exclude from result
    columns_found = [k.lower() for k in result.keys() if k and result[k] != ""]
    columns_missing = list(set(correct_col_names) - set(columns_found))
    try:
        percentage_missing = len(columns_missing) / len(list(set(correct_col_names)))
        if percentage_missing > skip_threshold:
            if print_debug:
                print("Ignored study id {} because too many columns are missing."
                      " (does not have a synoptic report or its synoptic report isn't normal)".format(study_id))
    except ZeroDivisionError or Exception:
        pass

    # auto-correct the matches by using a predefined list of correct column names in "column_mappings"
    result = autocorrect_columns(correct_col_names, result, study_id, list_of_dict_with_stats,
                                 max_edit_distance=max_edit_distance_autocorrect,
                                 substitution_cost=substitution_cost)

    generic_pairs = get_generic_extraction_regex(synoptic_report_str, general_regex)

    # resolve redundant spaces caused by OCR
    for col, val in generic_pairs.items():
        nearest_column = find_nearest_alternative(col,
                                                  columns_missing,
                                                  study_id,
                                                  val,
                                                  list_of_dict_with_stats,
                                                  max_edit_distance=max_edit_distance_missing,
                                                  substitution_cost=substitution_cost)
        if nearest_column in columns_missing:
            result[nearest_column] = val
        elif nearest_column:
            raise ValueError("Should never reached this branch. Nearest column is among possible candidates")

    return result


def autocorrect_columns(correct_col_names, extractions_so_far, study_id,
                        list_of_dict_with_stats,
                        max_edit_distance=5,
                        substitution_cost=2):
    """
    using a list of correct column names, autocorrect potential typos (that resulted from OCR) in column names

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
            nearest_column = find_nearest_alternative(col,
                                                      correct_col_names,
                                                      study_id,
                                                      extractions_so_far[col],
                                                      list_of_dict_with_stats,
                                                      max_edit_distance=max_edit_distance,
                                                      substitution_cost=substitution_cost)
            # if the nearest column is already extracted, find the next alternative
            while nearest_column is not None and nearest_column in extractions_so_far.keys():
                correct_col_names.remove(nearest_column)
                nearest_column = find_nearest_alternative(col,
                                                          correct_col_names,
                                                          study_id,
                                                          extractions_so_far[col],
                                                          list_of_dict_with_stats,
                                                          max_edit_distance=max_edit_distance,
                                                          substitution_cost=substitution_cost)
            # copy the value from incorrect column name to correct column name
            if nearest_column:
                extractions_so_far[nearest_column] = extractions_so_far[col]
    return extractions_so_far


def find_nearest_alternative(original_col, possible_candidates: List[str], study_id, value,
                             list_of_dict_with_stats: List[dict],
                             excluded_columns: list = [], max_edit_distance=2,
                             substitution_cost=1):
    """
    find the nearest alternative by choosing the element in possible_candidates with nearest edit distance to source
    if multiple candidates have the nearest distance, return the first candidate by position

    :param list_of_dict_with_stats:
    :param excluded_columns:
    :param original_col:            str;                the original source
    :param possible_candidates:     list of str;        possible strings that the source string could be
    :param study_id:                str;                study id
    :param value:                   str;                the original value inside the cell
    :param max_edit_distance:       int;                maximum distance allowed between source and candidate
    :param substitution_cost:       int;                cost to substitute a character instead of inserting/removing
    :return:                        str;    candidate that is most similar to source, None if exceeds max_edit_distance
    """
    # get a list of excluded source-target column name pairs that we saved earlier
    possible_candidates = list(set(possible_candidates) - set(excluded_columns))
    original_col = cleanse_column(original_col, remove_num=True)
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
        extracted_stats = [study_id, original_col, res, edit_distance(original_col, res), str(value).replace("\n", " ")]
        list_of_dict_with_stats.append(dict(zip(headers, extracted_stats)))

    return res
