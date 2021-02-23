from typing import List
import pytesseract
from pdf2image import convert_from_path
import os
import io
from appdirs import unicode
from pipeline.util.report import Report
from pipeline.util.report_type import ReportType


def load_in_pdfs(start: int, end: int, skip: List[int], path_to_reports: str, path_to_text: str, path_to_input: str):
    """
     Converts pdf reports into images that is finally converted to text by optical character recognition

     :param path_to_input:        path to inputs
     :param path_to_text:          path to where the generated text of the pdf reports should be put
     :param skip:                 reports to skip
     :param path_to_reports:      path to pdf reports
     :param start:                first report
     :param end:                  last report
     """
    for index in range(start, end + 1):
        if index in skip:
            continue
        else:
            pdf_path = path_to_reports + str(index) + ' OR_Redacted.pdf'
            if not os.path.exists(path_to_text):
                os.makedirs(path_to_text)
            output_filename = path_to_text + str(index) + " OR_Redacted.txt"
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


def load_in_txts(start: int, end: int, skip: List[int], path_to_txt: str) -> List[Report]:
    """
    The pdf reports that were converted into text files are read into the pipeline by this function

    :param path_to_txt:      the path to where the report text files are
    :param start:            first report
    :param end:              last report
    :param skip:             reports to skip
    :return:                 returns a list of Report objects with only report and id field initialized
    """
    emr_study_id = []
    for index in range(start, end + 1):
        if index in skip:
            continue
        else:
            file_name = path_to_txt + str(index) + " OR_Redacted.txt"
            emr_file_text = open(file_name, "r")
            emr_text = emr_file_text.read()
            emr_study_id.append(Report(text=emr_text, report_id=str(index), report_type=ReportType.OPERATIVE))
            emr_file_text.close()
    return emr_study_id
