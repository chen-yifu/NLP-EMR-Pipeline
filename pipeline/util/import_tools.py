import pandas as pd
from typing import Dict, List, Tuple

from pipeline.util.tuning import Tuning


def import_weights(path_to_weights: str) -> Dict[str, Tuning]:
    """
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


def import_pdf_human_cols(pdf_human_csv: str) -> List[Tuple[str, str]]:
    """
    :type pdf_human_csv: str
    :return List[Tuple[str, Any]]
    """
    pdf_cols_human_cols_list = []
    pdf_cols_human_cols = pd.read_csv(pdf_human_csv)
    for index, row in pdf_cols_human_cols.iterrows():
        pdf_col = row[0]
        human_col = row[1]
        pdf_cols_human_cols_list.append((pdf_col, human_col))
    return pdf_cols_human_cols_list


def import_code_book(code_book_path: str):
    """
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
