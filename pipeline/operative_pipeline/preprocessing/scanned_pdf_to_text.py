from typing import List

import pytesseract
from pdf2image import convert_from_path
import os
import io
from appdirs import unicode

from pipeline.operative_pipeline.util.report import Report


def load_in_pdfs(start: int, end: int, skip: List[int], path_to_reports: str, path_to_ocr: str):
    """
     :param skip:
     :param path_to_outputs:
     :param path_to_reports:
     :param start:                       first OR
     :param end:                         last OR
     """
    for index in range(start, end + 1):
        if index in skip:
            continue
        else:
            pdf_path = path_to_reports + str(index) + ' OR_Redacted.pdf'
            if not os.path.exists(path_to_ocr):
                os.makedirs(path_to_ocr)
            output_filename = path_to_ocr + str(index) + " OR_Redacted.txt"
            pages = convert_from_path(pdf_path)
            pg_cntr = 1

            sub_dir = str("data/outputs/" + "images/" + pdf_path.split('/')[-1].replace('.pdf', '')[0:20] + "/")
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
    :param path_to_txt:
    :param start:
    :param end:
    :param skip:
    :return:
    """
    emr_study_id = []
    for index in range(start, end + 1):
        if index in skip:
            continue
        else:
            file_name = path_to_txt + str(index) + " OR_Redacted.txt"
            emr_file_text = open(file_name, "r")
            emr_text = emr_file_text.read()
            emr_study_id.append(Report(report=emr_text, report_id=str(index)))
            emr_file_text.close()
    return emr_study_id