import string
from typing import Dict, List, Tuple
import pandas as pd

from pipeline.util.column import Column
from pipeline.util.tuning import Tuning

table = str.maketrans(dict.fromkeys(string.punctuation))


def extract_cols(row):
    try:
        return row.split(",")
    except AttributeError:
        return []


def import_weights(path_to_weights: str) -> Dict[str, Tuning]:
    """
    Imports the tuning weights for the operative reports pipeline found in data/utils/training_metrics/params

    :param path_to_weights:
    """
    tuning_dict = {}
    tuning_weights = pd.read_csv(path_to_weights)
    for row in tuning_weights.iterrows():
        col_name = row[1][0]
        sub_cost = row[1][1]
        large_cost = row[1][2]
        tuning_dict[col_name] = Tuning(col_name=col_name, sub_cost=sub_cost, large_cost=large_cost)
    return tuning_dict


def import_code_book(code_book_path: str) -> dict:
    """
    Imports a code book in excel sheet used for encoding extractions format into a dictionary.

    :param code_book_path: str
    :return code_book: Dict of Dict
    """
    code_book = {}
    code_book_path_cols = pd.read_excel(code_book_path)
    for index, row in code_book_path_cols.iterrows():
        col_name = row[0]
        encoded_val = row[1]
        val = row[2]
        val_list = val.split(",")
        cleaned_val_list = [e.strip() for e in val_list]
        if col_name not in code_book:
            code_book[col_name] = {}
        val_dict = code_book[col_name]
        for cleaned_val in cleaned_val_list:
            val_dict[cleaned_val] = encoded_val
    return code_book


def get_input_paths(start: int, end: int, skip: List[int], path_to_reports: str,
                    report_str: str) -> List[str]:
    """
    Given the starting and ending pdf ids, return the full path of all documents
    REQUIRES the pdfs to be located in "../data/input" folder
    e.g. 101 Path_Redacted.pdf /Users/yifu/PycharmProjects/pathology_pipeline/data/input/101 Path_Redacted.pdf data/input/101 Path_Redacted.pdf

    :param report_str:            the report str for example {} OR_Redacted.text or {} Path_Redacted.pdf
    :param path_to_reports:       general path to all the reports
    :param skip:                  ids to skip
    :param start:                 the first pdf id
    :param end:                   the last pdf id
    :return:                      list of paths
    """
    # make general list of paths
    nums_list = [n for n in range(start, end + 1) if n not in skip]
    return [path_to_reports + report_str.format(i) for i in nums_list]


def import_pdf_human_cols_as_dict(pdf_human_excel_sheet: str, skip=None, primary_row_index: int = 0,
                                  alternative_row_index: int = 1, human_col_index: int = 2) -> Dict[str, List[str]]:
    """
    Imports the columns you want to find from a csv file as a dictionary.
    {human_annotated_col:[pdf_col, pdf_col, ...],human_annotated_col:[pdf_col, pdf_col, ...],... }

    :param primary_row_index:
    :param human_col:
    :param pdf_human_excel_sheet:
    :param skip:
    :return:
    """
    if skip is None:
        skip = []
    pdf_cols_human_cols_dict = {}
    pdf_cols_human_cols = pd.read_csv(pdf_human_excel_sheet)
    for index, row in pdf_cols_human_cols.iterrows():
        human_col = row[human_col_index]
        if human_col.lower() in skip:
            continue
        else:
            pdf_cols = row[primary_row_index]
            pdf_cols_list = pdf_cols.split(",")
            cleaned_pdf_col_list = [p.strip() for p in pdf_cols_list]
            pdf_cols_human_cols_dict[human_col] = cleaned_pdf_col_list
    return pdf_cols_human_cols_dict


def import_pdf_human_cols_tuples(pdf_human_csv: str, keep_punc: bool = False, primary_row_index: int = 0,
                                 alternative_row_index: int = 1, human_col_index: int = 2) -> List[Tuple[str, str]]:
    """
    Imports the columns you want to find from a csv file as a list of tuples.
    [(pdf_col, human_annotated_col),(pdf_col, human_annotated_col),(pdf_col, human_annotated_col), ...]

    :param pdf_human_csv:
    :param keep_punc:
    :return:
    """
    pdf_cols_human_cols_list = []
    pdf_cols_human_cols = pd.read_csv(pdf_human_csv)
    for index, row in pdf_cols_human_cols.iterrows():
        pdf_cols = row[primary_row_index]
        human_col = row[human_col_index]
        pdf_cols_list = pdf_cols.split(",")
        if keep_punc:
            cleaned_pdf_col_list = [p.strip() for p in pdf_cols_list]
        else:
            cleaned_pdf_col_list = [p.translate(table).strip() for p in pdf_cols_list]
        for pdf_col in cleaned_pdf_col_list:
            pdf_cols_human_cols_list.append((pdf_col, human_col))
    return pdf_cols_human_cols_list


def import_columns(pdf_human_excel_sheet: str, skip=None, primary_row_index: int = 0,
                   alternative_row_index: int = 1, human_col_index: int = 2) -> Dict[str, Column]:
    """
    Imports the columns you want to find from a csv file as a dict of type Column.

    :param pdf_human_excel_sheet:
    :param skip:
    :return:
    """
    if skip is None:
        skip = []
    pdf_cols_human_cols_dict_w_column = {}
    pdf_cols_human_cols = pd.read_csv(pdf_human_excel_sheet)
    for index, row in pdf_cols_human_cols.iterrows():
        human_col = row[human_col_index]
        if human_col.lower() in skip:
            continue
        else:
            primary_pdf_cols_list = extract_cols(row[primary_row_index])
            alternative_pdf_col_list = extract_cols(row[alternative_row_index])
            pdf_cols_human_cols_dict_w_column[human_col] = Column(human_col=human_col,
                                                                  primary_report_col=primary_pdf_cols_list,
                                                                  alternative_report_col=alternative_pdf_col_list)
    return pdf_cols_human_cols_dict_w_column
