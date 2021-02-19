import re
import pdftotext
from pipeline.pathology_pipeline.pathology_pipeline import utils


def get_input_paths(pdf_id_beginning, pdf_id_end):
    """
    Given the starting and ending pdf ids, return the full path of all documents
    REQUIRES the pdfs to be located in "../data/input" folder
    e.g. 101 Path_Redacted.pdf /Users/yifu/PycharmProjects/pathology_pipeline/data/input/101 Path_Redacted.pdf data/input/101 Path_Redacted.pdf
    :param pdf_id_beginning: int;   first pdf
    :param pdf_id_end:       int;   last pdf
    :return:        list of str;    the list of paths for each pdf
    """
    root = utils.get_project_root()
    input_pdf_paths = []
    for i in range(pdf_id_beginning, pdf_id_end + 1):
        if i == 140:
            continue  # note: PDF for id 140 is missing
        temp_path = "../data/input/{} Path_Redacted.pdf".format(i)
        input_pdf_paths.append(temp_path)

    return input_pdf_paths


def pdfs_to_strings(pdf_paths, do_preprocessing=True, print_debug=False):
    """
    takes in a list of pdf paths and extract the textual content into a list of (str, str) tuples
    :param pdf_paths:           a list of string;               paths to input pdfs
    :param do_preprocessing:    boolean;                        apply preprocessing to each pdf's string if True
    :param print_debug:         boolean;                        print debugging statements if True
    :return:                    a list of tuples (str, str);    str is extracted text, str is the study ID of pdf
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
        result_texts.append((pdf_text_str, study_id))

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
