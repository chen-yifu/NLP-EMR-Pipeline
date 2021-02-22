from typing import List
import nltk
from pipeline.util import import_tools
from pipeline.util.report import Report


def extract_cols(reports: List[Report], pdf_human_cols_path="../data/inputs/operative_column_mappings.ods",
                 other_cols_path="../data/inputs/other_cols.xlsx") -> List[Report]:
    """
    :param other_cols_path:
    :param pdf_human_cols_path: str
    :param reports: List[Report]
    :return studies: List[Report]
    """
    cols_to_find = import_tools.import_pdf_human_cols(pdf_human_cols_path)  # this is a dict
    already_found = set()

    def extract_operative_cols_single(single_report: Report):
        """
        :param single_report:
        """
        copy_cols_to_find = list(cols_to_find.keys())

        def find_match(subsection: dict) -> dict:
            """
            :param subsection:
            :return:
            """

            extracted_pdf = {}
            for extracted_col, extracted_val in subsection.items():
                for pdf_col in copy_cols_to_find:

                    if pdf_col.lower() == "reconstruction mentioned":
                        continue
                    else:
                        if nltk.edit_distance(pdf_col.lower(), extracted_col.lower()) < 3:
                            if pdf_col.lower() == "reconstruction":
                                extracted_pdf.update({"Immediate Reconstruction Mentioned": 1})
                            extracted_pdf[cols_to_find[pdf_col]] = extracted_val
                            already_found.add(pdf_col)
            return extracted_pdf

        preoperative = single_report.preoperative_breast
        operative_breast = single_report.operative_breast
        operative_axilla = single_report.operative_axilla

        single_report.preoperative_breast = find_match(preoperative)
        single_report.operative_axilla = find_match(operative_axilla)
        single_report.operative_breast = find_match(operative_breast)
        single_report.not_found = [x for x in copy_cols_to_find if x not in already_found]

    for study in reports:
        extract_operative_cols_single(study)
    return reports
