import re
from typing import Tuple, List

import pandas as pd
from collections import defaultdict
from nltk.metrics.distance import edit_distance

from pipeline.operative_pipeline.processing.extract_extractions import get_generic_extraction_regex, \
    get_extraction_specific_regex
from pipeline.pathology_pipeline.processing.columns import load_excluded_columns_as_list
from pipeline.util.paths import export_pathology_paths
from pipeline.util.regex_tools import export_pathology_mappings_to_regex_vals
from pipeline.util.report import Report


def cleanse_column(col: str) -> str:
    """
    cleanse the column by removing "-" and ":"
    :param col:      raw column
    :return:         cleansed column
    """
    col = re.sub(r"^\s*-\s*", "", col)  # remove "-"
    col = re.sub(r":\s*$", "", col)  # remove ":"
    return col.strip().lower()


def cleanse_value(val: str, function=None) -> str:
    """
    cleanse the value by removing linebreaks
    :param val:      raw value
    :return:         cleansed value
    """
    if function is None:
        return val.replace("\n", " ").strip()
    else:
        return function(val)


def process_synoptics_and_ids(unfiltered_reports: List[Report],
                              column_mappings: List[Tuple[str, str]],
                              specific_regex: str,
                              general_regex: str,
                              tools: dict = {},
                              print_debug=True,
                              max_edit_distance_missing=5,
                              max_edit_distance_autocorrect=5,
                              substitution_cost=2) -> Tuple[List[Report], pd.DataFrame]:
    """
    process and extract data from a list of synoptic reports by using regular expression
    :param unfiltered_reports:      a list of Report;                       synoptic sections and study IDs
    :param column_mappings:         a dict                                  first str is col name from PDF, second str is col from Excel
    :param print_debug:             boolean;                                print debug statements in Terminal if True
    :param max_edit_distance:       int;                                    max allowed edit distance to find missing cells
    :return:                        a list of Report;                       extracted data of the form (col_name: value)
    :return:                        pandas DataFrame                        the auto-correct information to be shown
    """

    result = []
    if print_debug:
        s = "\nProcessing synoptic report sections..."
        print(s)

    dict_with_stats = []

    # split the synoptic report into multiple sub-sections using ALL-CAPITALIZED headings as delimiter
    for report in unfiltered_reports:
        columns_and_values = process_synoptic_section(report.text, report.report_id, column_mappings, dict_with_stats,
                                                      specific_regex, general_regex, tools,
                                                      print_debug=print_debug,
                                                      max_edit_distance_missing=max_edit_distance_missing,
                                                      max_edit_distance_autocorrect=max_edit_distance_autocorrect,
                                                      substitution_cost=substitution_cost)
        report.extractions = columns_and_values
        result.append(report)

    # sort DataFrame by study ID
    df_with_stats = pd.DataFrame(dict_with_stats)
    df_with_stats.sort_values("Study ID")

    if print_debug:
        s = "Auto-correct Information:\n" + df_with_stats.to_string()
        print(s)

    # return [report for report in result if report.extractions], df_with_stats


def process_synoptic_section(synoptic_report_str: str,
                             study_id,
                             column_mappings: List[Tuple[str, str]],
                             dict_with_stats: dict,
                             specific_regex: str, general_regex: str,
                             tools: dict,
                             print_debug=True,
                             max_edit_distance_missing=5,
                             max_edit_distance_autocorrect=5,
                             substitution_cost=2,
                             skip_threshold=0.95) -> dict:
    """
    process and extract specific data from a synoptic report.

    :param synoptic_report_str:         str;                    synoptic report section
    :param study_id:                str;                    the study id of this report
    :param column_mappings:         a list of (str, str);   first str is col name from PDF, second str is col from Excel
    :param dict_with_stats:                      pandas DataFrame;       save the auto-corrected columns into this DataFrame
    :param print_debug:             boolean;                print debug statements in Terminal if true
    :param max_edit_distance_missing:int;                   maximum edit distance allowed when finding missing columns
    :param max_edit_distance_autocorrect: int               maximum edit distance allowed when auto-correcting columns
    :param skip_threshold:          int;                    between 0 and 1, specifies the percentage of max missing columns
    :return:                        dict;                   extracted data, represented by dictionary {column: value}
    """

    # generic regex that captures all column values
    generic_pairs = get_generic_extraction_regex(synoptic_report_str, general_regex)

    synoptic_report_regex = r"(Part\(s\) Involved:\s*(?P<parts_involved>((?!Synoptic Report)[\s\S])*)|SPECIMEN\s*-(?P<specimen>.+)|LYMPH ((?!Extent)[\s\S])*Extent:(?P<lymph_node_extent>.*)|TREATMENT EFFECT\s*-(?P<treatment_effect>.+)|MARGINS *\n *-(?P<margins>.*)|P *A *T *H *O *L *O *G *I *C *S *T *A *G *E *\s*-(?P<pathologic_stage>.*)|COMMENT\(S\)\s*-(?P<comments>((?!-|\nBased on AJCC)[\s\S])*))|(?P<column>[^-:]*(?=:)):(?P<value>(?:(?!-|Part\(s\) Involved|SPECIMEN|MARGINS|TREATMENT EFFECT|LYMPH NODES|DCIS Estimated|P *A *T *H *|.* prepared by PLEXIA .*)[\s\S])*)"

    # autogenerated regex based on columns
    # specific_pairs = get_extraction_specific_regex(synoptic_report_str, export_pathology_mappings_to_regex_vals,
    #                                                re.compile(synoptic_report_regex))

    synoptic_report_regex = r"(Part\(s\) Involved:\s*(?P<parts_involved>((?!Synoptic Report)[\s\S])*)|SPECIMEN\s*-(?P<specimen>.+)|LYMPH ((?!Extent)[\s\S])*Extent:(?P<lymph_node_extent>.*)|TREATMENT EFFECT\s*-(?P<treatment_effect>.+)|MARGINS *\n *-(?P<margins>.*)|P *A *T *H *O *L *O *G *I *C *S *T *A *G *E *\s*-(?P<pathologic_stage>.*)|COMMENT\(S\)\s*-(?P<comments>((?!-|\nBased on AJCC)[\s\S])*))|(?P<column>[^-:]*(?=:)):(?P<value>(?:(?!-|Part\(s\) Involved|SPECIMEN|MARGINS|TREATMENT EFFECT|LYMPH NODES|DCIS Estimated|P *A *T *H *|.* prepared by PLEXIA .*)[\s\S])*)"
    synoptic_report_regex = re.compile(synoptic_report_regex)
    pairs = [(m.groupdict()) for m in synoptic_report_regex.finditer(synoptic_report_str)]
    print(pairs)
    # output placeholder
    result = defaultdict(str)
    # result.update(specific_pairs)

    # save study_id
    result["study_id"] = study_id

    # iterate through generic pairs
    # for pair in generic_pairs:
    #     if pair["column"] and len(pair["value"].strip()) > 0:
    #         clean_column = cleanse_column(pair["column"])
    #         clean_value = cleanse_value(pair["value"])
    #         keys = list(result.keys())
    #         if clean_column in keys:  # check for duplicated column name
    #             result[utils.get_next_col_name(clean_column, keys)] = clean_value
    #         else:
    #             result[clean_column] = clean_value

#     # calculate the proportion of missing columns, if it's above skip_threshold, then return None immediately
#     correct_col_names = [pdf_col for (pdf_col, excel_col) in column_mappings]
#     # if too many columns are missing, we probably isolated a section with unexpected template, so return nothing and exclude from result
#     columns_found = [k.lower() for k in result.keys() if k and result[k] != ""]
#     columns_missing = list(set(correct_col_names) - set(columns_found))
#     try:
#         percentage_missing = len(columns_missing) / len(list(set(correct_col_names)))
#         if percentage_missing > skip_threshold:
#             if print_debug:
#                 s = "Ignored study id {} because too many columns are missing. (does not have a synoptic report or its synoptic report isn't normal)".format(
#                     study_id)
#                 print(s)
#             return None
#     except ZeroDivisionError or Exception:
#         None
#
#     # auto-correct the matches by using a predefined list of correct column names in "column_mappings"
#     result = autocorrect_columns(correct_col_names, result, study_id, dict_with_stats,
#                                  max_edit_distance=max_edit_distance_autocorrect,
#                                  substitution_cost=substitution_cost,
#                                  pickle_path=export_pathology_paths["pickle_path"])
#
#     find_missing_regex = re.compile(r"(?P<column>.*):(?P<value>.*)")
#     specific_pairs = [(m.groupdict()) for m in find_missing_regex.finditer(synoptic_report_str)]
#     # resolve redundant spaces caused by OCR
#     for pair in specific_pairs:
#         pair["column"] = re.sub(" *-? +", " ", pair["column"]).strip().lower()
#         pair["value"] = re.sub(" +", " ", pair["value"]).strip()
#     for pair in specific_pairs:
#         nearest_column = find_nearest_alternative(pair["column"],
#                                                   columns_missing,
#                                                   study_id,
#                                                   pair["value"],
#                                                   dict_with_stats,
#                                                   max_edit_distance=max_edit_distance_missing,
#                                                   substitution_cost=substitution_cost,
#                                                   pickle_path=export_pathology_paths["pickle_path"])
#         if nearest_column in columns_missing:
#             result[nearest_column] = pair["value"]
#         elif nearest_column:
#             raise ValueError("Should never reached this branch. Nearest column is among possible candidates")
#
#     spaceless_synoptic_report = synoptic_report_str.replace(" ", "")
#     if "Nolymphnodespresent" in spaceless_synoptic_report:
#         result["number of lymph nodes examined (sentinel and nonsentinel)"] = "0"
#         result["number of sentinel nodes examined"] = "0"
#         result["micro / macro metastasis"] = None
#         result["number of lymph nodes with micrometastases"] = None
#         result["number of lymph nodes with macrometastases"] = None
#         result["size of largest metastatic deposit"] = None
#
#     return result
#
#
# def autocorrect_columns(correct_col_names, dictionary, study_id, df, pickle_path, max_edit_distance=5,
#                         substitution_cost=2,
#                         print_debug=True):
#     """
#     using a list of correct column names, autocorrect potential typos (that resulted from OCR) in column names
#     :param correct_col_names:       list of str;            a list of correct column names
#     :param dictionary:              dict;                   extracted generic key-value pairs from synoptic reports
#     :param study_id:                str;                    the study id of the dictionary
#     :param df:                      pandas DataFrame;       save the auto-correct activities to be shown on GUI
#     :param max_edit_distance:       int;                    maximum distance allowed between source and candidate
#     :param substitution_cost:       int;                    cost to substitute a character instead of inserting/removing
#     :return:                        dict;                   dict with auto-corrected column names
#     """
#
#     columns = list(dictionary.keys())
#     for col in columns:
#         if col in correct_col_names:  # do nothing if key is correct
#             continue
#         else:
#             nearest_column = find_nearest_alternative(col,
#                                                       correct_col_names,
#                                                       study_id,
#                                                       dictionary[col],
#                                                       df,
#                                                       max_edit_distance=max_edit_distance,
#                                                       substitution_cost=substitution_cost,
#                                                       pickle_path=pickle_path)
#             # if the nearest column is already extracted, find the next alternative
#             while nearest_column is not None and nearest_column in dictionary.keys():
#                 correct_col_names.remove(nearest_column)
#                 nearest_column = find_nearest_alternative(col,
#                                                           correct_col_names,
#                                                           study_id,
#                                                           dictionary[col],
#                                                           df,
#                                                           max_edit_distance=max_edit_distance,
#                                                           substitution_cost=substitution_cost,
#                                                           pickle_path=pickle_path)
#             # copy the value from incorrect column name to correct column name
#             if nearest_column:
#                 dictionary[nearest_column] = dictionary[col]
#
#     # resolve column that have multiple aliases
#     # the column "Total LN Examined" could be either, but keep only one
#     if (dictionary["number of lymph nodes examined"] != ""):
#         dictionary["number of lymph nodes examined (sentinel and nonsentinel)"] = dictionary[
#             "number of lymph nodes examined"]
#         del dictionary["number of lymph nodes examined"]
#     # if number of foci isn't found, use tumour focality
#     if dictionary["number of foci"] == "":
#         dictionary["number of foci"] = dictionary["tumour focality"]
#     # if in situ type is not found, use histologic type
#     if dictionary["in situ component type"] == "":
#         dictionary["in situ component type"] = dictionary["histologic type"]
#     # if in situ component is not found, use histologic type
#     if dictionary["in situ component"] == "":
#         dictionary["in situ component"] = dictionary["histologic type"]
#     return dictionary
#
#
# def find_nearest_alternative(source, possible_candidates, study_id, value, df, pickle_path, max_edit_distance=2,
#                              substitution_cost=1):
#     """
#     find the nearest alternative by choosing the element in possible_candidates with nearest edit distance to source
#     if multiple candidates have the nearest distance, return the first candidate by position
#     :param source:                  str;                the original source
#     :param possible_candidates:     list of str;        possible strings that the source string could be
#     :param study_id:                str;                study id
#     :param value:                   str;                the original value inside the cell
#     :param max_edit_distance:       int;                maximum distance allowed between source and candidate
#     :param substitution_cost:       int;                cost to substitute a character instead of inserting/removing
#     :return:                        str;    candidate that is most similar to source, None if exceeds max_edit_distance
#     """
#
#     # get a list of excluded source-target column name pairs that we saved earlier
#     all_excluded_columns = load_excluded_columns_as_list(pickle_path=pickle_path)
#     excluded_columns = [tupl[1] for tupl in all_excluded_columns if tupl[0] == source]
#     possible_candidates = list(set(possible_candidates) - set(excluded_columns))
#
#     min_dist = float("inf")
#     res = None
#     for c in possible_candidates:
#         clean_source = source.replace(" ", "")
#         clean_c = c.replace(" ", "")
#         dist = edit_distance(clean_source, clean_c, substitution_cost=substitution_cost)
#         # dist = edit_distance(source, c, substitution_cost=substitution_cost)
#         if dist < min_dist:
#             res = c
#             min_dist = dist
#     if min_dist > max_edit_distance:
#         return None
#
#     # add the auto-correct information to DataFrame
#     if res != source:
#         df.loc[-1] = [study_id, source, res, edit_distance(source, res), str(value).replace("\n", " ")]  # adding a row
#         df.index = df.index + 1  # shifting index
#
#     return res
