import re
from typing import List
import pdftotext
import pytesseract
from pdf2image import convert_from_path
import os
import io
from appdirs import unicode

from pipeline.util import utils
from pipeline.util.report import Report
from pipeline.util.report_type import ReportType


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


def convert_pdf_to_text(path_to_input: str, paths_to_pdfs: List[str], paths_to_texts: List[str]):
    """
     Converts pdf reports into images that is finally converted to text by optical character recognition

     :param path_to_input:        path to inputs
     :param path_to_text:          path to where the generated text of the pdf reports should be put

     """
    pdf_path_and_text_path = zip(paths_to_pdfs, paths_to_texts)
    for pdf_path, output_filename in pdf_path_and_text_path:
        if not os.path.exists(path_to_input):
            os.makedirs(path_to_input)
        pages = convert_from_path(pdf_path)
        pg_cntr = 1

        sub_dir = str(path_to_input + "images/" + pdf_path.split('/')[-1].replace('.pdf', '')[0:20] + "/")
        if not os.path.exists(sub_dir):
            os.makedirs(sub_dir)

        for page in pages:
            if pg_cntr <= 20:
                filename = "pg_" + str(pg_cntr) + '_' + pdf_path.split('/')[-1].replace('.pdf', '.jpg')
                page.save(sub_dir + filename)
                with io.open(output_filename, 'a+', encoding='utf8') as f:
                    f.write(unicode(pytesseract.image_to_string(sub_dir + filename) + "\n"))
                pg_cntr += 1


def load_in_reports(start: int, end: int, skip: List[int], paths_to_r: List[str],
                    do_preprocessing: bool = True) -> List[Report]:
    """
    The pdf reports that were converted into text files are read into the pipeline by this function

    :param do_preprocessing:
    :param paths_to_texts:   the path to where the report text files are
    :param start:            first report
    :param end:              last report
    :param skip:             reports to skip
    :return:                 returns a list of Report objects with only report and id field initialized
    """
    emr_study_id = []
    nums = [n for n in range(start, end + 1) if n not in skip]
    text_paths_and_id = zip(paths_to_r, nums)

    for text_path, num in text_paths_and_id:
        if text_path[-3:] == "txt":
            emr_file_text = open(text_path, "r")
            emr_text = emr_file_text.read()
            emr_study_id.append(Report(text=emr_text, report_id=str(num), report_type=ReportType.TEXT))
            emr_file_text.close()
        elif text_path[-3:] == "pdf":
            # extract text
            pdfFileObj = open(text_path, "rb")
            pdf_text_obj = pdftotext.PDF(pdfFileObj)
            pdf_text_str = ""
            # process each page
            for page_num in range(len(pdf_text_obj)):
                raw_text = pdf_text_obj[page_num]
                pdf_text_str += raw_text
            if do_preprocessing:
                pdf_text_str = preprocess_remove_extra_text(pdf_text_str)
            # append result for this iteration
            emr_study_id.append(Report(text=pdf_text_str, report_id=str(num), report_type=ReportType.NUMERICAL))
        else:
            print("File must be in either pdf format or text format for extraction!")
    return emr_study_id
