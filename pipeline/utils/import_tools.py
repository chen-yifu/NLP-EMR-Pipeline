"""
This file contains methods that import tools needed to run the pipeline
"""
import string
from typing import Dict, List, Tuple, Set

import os
import pandas as pd
from pipeline.utils.column import Column
from pipeline.utils.encoding import Encoding

table = str.maketrans(dict.fromkeys(string.punctuation))


def extract_cols(row):
    try:
        return row.split(",")
    except AttributeError:
        return []


def import_code_book(code_book_path: str, column_id: int = 0, encoding_id: int = 1,
                     value_id: int = 2) -> Dict[str, List[Encoding]]:
    """
    Imports a code book in excel sheet format that is used for encoding extractions.

    :param value_id:             the index in the excel file of the column that contains the values that correspond to encodings
    :param column_id:            the index in the excel file of the column that corresponds to the report column
    :param encoding_id:          the index in the excel file of the column that contains the encodings
    :param code_book_path:       the path to the coded book
    :return code_book
    """
    code_book = {}
    code_book_path_cols = pd.read_excel(code_book_path)
    for index, row in code_book_path_cols.iterrows():
        col_name = row[column_id]
        num = row[encoding_id]
        val = row[value_id]
        val_list = str(val).split(",") if not pd.isna(val) else []
        cleaned_val_list = [e.strip() for e in val_list]
        if col_name not in code_book:
            code_book[col_name] = []
        encoding_list = code_book[col_name]
        encoding_list.append(Encoding(cleaned_val_list, num))
    return code_book


def get_input_paths(start: int, end: int, path_to_reports: str, report_str: str) -> List[str]:
    """
    Given the starting and ending pdf ids, return the full path of all documents
    REQUIRES the pdfs to be located in "../data/input" folder
    e.g. 101 Path_Redacted.pdf /Users/yifu/PycharmProjects/pathology_pipeline/data/input/101 Path_Redacted.pdf data/input/101 Path_Redacted.pdf

    :param report_str:            the report str for example {} OR_Redacted.text or {} Path_Redacted.pdf
    :param path_to_reports:       general path to all the reports
    :param start:                 the first pdf id
    :param end:                   the last pdf id
    :return:                      list of paths
    """
    # make general list of paths
    nums_list = [n for n in range(start, end + 1)]
    return [path_to_reports + report_str.format(i) for i in nums_list]


def import_pdf_human_cols_tuples(pdf_human_csv: str, keep_punc: bool = False) -> List[Tuple[str, str]]:
    """
    DEPRECATED: only used in the old pathology pipeline
    Imports the columns you want to find from a csv file as a list of tuples.
    [(pdf_col, human_annotated_col),(pdf_col, human_annotated_col),(pdf_col, human_annotated_col), ...]

    :param pdf_human_csv:
    :param keep_punc:
    :return:
    """
    pdf_cols_human_cols_list = []
    pdf_cols_human_cols = pd.read_csv(pdf_human_csv)
    for index, row in pdf_cols_human_cols.iterrows():
        pdf_cols = str(row[0])
        human_col = row[1]
        if keep_punc:
            cleaned_pdf_col_list = pdf_cols.strip()
        else:
            cleaned_pdf_col_list = pdf_cols.translate(table).strip()
        for pdf_col in cleaned_pdf_col_list:
            pdf_cols_human_cols_list.append((pdf_col, human_col))
    return pdf_cols_human_cols_list


def create_regex_rules_csv(regex_rules_path: str, pdf_cols_human_cols_dict_w_column: Dict[str, Column]):
    """
    :param regex_rules_path:
    :param pdf_cols_human_cols_dict_w_column:
    """
    regex_rules_list = []
    for col_name, col_obj in pdf_cols_human_cols_dict_w_column.items():
        regex_col_dict = {"col": col_name}
        regex_col_dict.update(col_obj.regular_pattern_rules)
        regex_rules_list.append(regex_col_dict)
    regex_rules_df = pd.DataFrame(regex_rules_list)
    regex_rules_df.to_csv(regex_rules_path, index=False)
    print(regex_rules_df)


def find_regex_rules(regex_rules: List[dict], human_col: str):
    """
    :param regex_rules:
    :param human_col:
    :return:
    """
    for cols_dict in regex_rules:
        if cols_dict["col"] == human_col:
            cols_dict.pop("col")
            return cols_dict
    return {}


def import_columns(pdf_human_excel_sheet: str, threshold_path: str, regex_rules_path: str, skip=None,
                   primary_row_index: int = 0, alternative_row_index: int = 1, human_col_index: int = 2,
                   zero_empty_index: int = 3) -> Dict[str, Column]:
    """
    Imports the columns you want to find from a csv file as a dict of type Column.

    :param regex_rules_path:
    :param zero_empty_index:
    :param threshold_path:
    :param alternative_row_index:       the index that corresponds to column that contains alternative columns
    :param primary_row_index:           the index that corresponds to column that contains primary columns
    :param human_col_index:             the index that corresponds to column that contains the human excel columns
    :param pdf_human_excel_sheet:       path to the columns, must be a csv
    :param skip:                        columns to skip
    :return: pdf_cols_human_cols_dict_w_column
    """
    if skip is None:
        skip = []
    pdf_cols_human_cols_dict_w_column = {}
    pdf_cols_human_cols = pd.read_csv(pdf_human_excel_sheet)
    thresholds_exist = os.path.exists(threshold_path)
    regex_rules_exist = os.path.exists(regex_rules_path)
    if not thresholds_exist:
        print("No specialized thresholds exist, will use defaults of 0.75.")
    column_thresholds = pd.read_excel(threshold_path) if thresholds_exist else None
    regex_rules = pd.read_csv(regex_rules_path).to_dict('record') if regex_rules_exist else None
    list_of_cols = list(column_thresholds["column"]) if thresholds_exist else []
    for index, row in pdf_cols_human_cols.iterrows():
        human_col = row[human_col_index]
        index_t = list_of_cols.index(human_col) if human_col in list_of_cols else -1
        col_regex_rules = find_regex_rules(regex_rules, human_col)
        if human_col.lower() in skip:
            continue
        else:
            primary_pdf_cols_list = extract_cols(row[primary_row_index])
            alternative_pdf_col_list = extract_cols(row[alternative_row_index])
            pdf_cols_human_cols_dict_w_column[human_col] = Column(human_col=human_col,
                                                                  primary_report_col=primary_pdf_cols_list,
                                                                  alternative_report_col=alternative_pdf_col_list,
                                                                  threshold=
                                                                  column_thresholds.iloc[[index_t]]["threshold"][
                                                                      index_t] if index_t != -1 else .75,
                                                                  zero_empty=row[zero_empty_index],
                                                                  regular_pattern_rules=col_regex_rules)
    if not regex_rules_exist:
        print("No regex rules exist, will make default regex rules csv.")
        create_regex_rules_csv(regex_rules_path, pdf_cols_human_cols_dict_w_column)

    return pdf_cols_human_cols_dict_w_column


def get_acronyms(encodings: List[str]) -> Set[str]:
    """
    :param encodings:
    :return:
    """
    acronyms = set()
    for encoding in encodings:
        all_upper = len([l for l in encoding if l.isupper()]) >= len(encoding) - 1 and len(encoding) > 2
        if all_upper:
            acronyms.add(encoding)
    return acronyms
