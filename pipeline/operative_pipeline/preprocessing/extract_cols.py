from typing import List, Tuple
import nltk
from pipeline.util import import_tools
from pipeline.util.report import Report


def extract_cols(reports: List[Report], pdf_human_cols: List[Tuple[str, str]]) -> List[Report]:
    """
    Extracts the columns that someone wants. This function will filter the columns.

    :param pdf_human_cols:
    :param reports: List[Report]     list of reports
    :return reports_cleaned:         list of filtered reports
    """
    human_cols = [human_col for pdf_col, human_col in pdf_human_cols]  # this is a list of tuple
    already_found = set()

    def extract_operative_cols_single(single_report: Report):
        """
        :param single_report:
        """
        pdf_cols = [pdf_col for pdf_col, human_col in pdf_human_cols]

        def find_match(subsection: dict) -> dict:
            """
            :param subsection:
            :return:
            """

            extracted_pdf = {}
            for extracted_col, extracted_val in subsection.items():
                for index, pdf_col in enumerate(pdf_cols):
                    if pdf_col.lower() == "reconstruction mentioned":
                        continue
                    else:
                        if nltk.edit_distance(pdf_col.lower(), extracted_col.lower()) < 3:
                            if pdf_col.lower() == "reconstruction":
                                extracted_pdf.update({"Immediate Reconstruction Mentioned": 1})
                            extracted_pdf[human_cols[index]] = extracted_val
                            already_found.add(pdf_col)
            return extracted_pdf

        uncleaned_extractions = single_report.extractions
        single_report.extractions = find_match(uncleaned_extractions)
        single_report.not_found = [x for x in pdf_cols if x not in already_found]

    for study in reports:
        extract_operative_cols_single(study)
    return reports
