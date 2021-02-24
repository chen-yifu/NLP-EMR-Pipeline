import re
import pdftotext

from pipeline.util import utils
from pipeline.util.report import Report
from pipeline.util.report_type import ReportType


def pdfs_to_strings(pdf_paths, do_preprocessing=True, print_debug=False):
    """
    takes in a list of pdf paths and extract the textual content into a list of (str, str) tuples

    :param pdf_paths:           a list of string;               paths to input pdfs
    :param do_preprocessing:    boolean;                        apply preprocessing to each pdf's string if True
    :param print_debug:         boolean;                        print debugging statements if True
    :return:                    a list of reports               the report will have the fields text,id and type initialized
    """

    result_texts = []

    for index, path in enumerate(pdf_paths):
        # extract study ID from file path
        # regex demo: https://regex101.com/r/FX8VfI/2
        regex = re.compile(r"\D*(?P<id>\d+) Path_Redacted")
        match = re.match(regex, path)
        try:
            study_id = match.group("id")
        except AttributeError:
            raise NameError("The path doesn't contain study ID. "
                            "It should be, for example: 'data/input/101 Path_Redacted.pdf' ")

        # extract text
        pdfFileObj = open(path, "rb")
        pdf_text_obj = pdftotext.PDF(pdfFileObj)
        pdf_text_str = ""
        # process each page
        for page_num in range(len(pdf_text_obj)):
            raw_text = pdf_text_obj[page_num]
            pdf_text_str += raw_text
        if do_preprocessing:
            pdf_text_str = preprocess_remove_extra_text(pdf_text_str)
        # append result for this iteration
        result_texts.append(Report(text=pdf_text_str, report_id=study_id, report_type=ReportType.PATHOLOGY))

    return result_texts


def preprocess_remove_extra_text(input_report):
    """
    helper function to preprocess reports
    :param input_report:        string;         the raw extracted text from pdf
    :return:                    string;         preprocessed string
    """

    regex = r".*(?:Resuts For|Based on.*AJCC|Prepared.*PLEXIA.*|FINAL RESULTS|Based on.*AJCC|.*Page\s*\d\s*of\s*\d.*|https.*|For VCH|For VPP|For PHC).*"
    utils.util_resolve_ocr_spaces(regex)
    res = re.sub(regex, "", input_report)  # remove footer, separator, and distracting texts
    res = re.sub(r"\n{1,}", "\n", res)  # remove redundant linebreak
    return res
