from pipeline.operative_pipeline.postprocessing.compare_excel import nice_compare
from pipeline.operative_pipeline.postprocessing.to_spreadsheet import *
from pipeline.operative_pipeline.preprocessing.extract_cols import extract_cols
from pipeline.operative_pipeline.preprocessing.extract_synoptic_operative import clean_up_reports
from pipeline.operative_pipeline.preprocessing.scanned_pdf_to_text import convert_pdf_to_text, load_in_reports
from pipeline.operative_pipeline.processing.encode_extractions import code_extractions
from pipeline.operative_pipeline.processing.extract_extractions import get_general_extractions
from pipeline.util.import_tools import import_pdf_human_cols, import_code_book, get_input_paths
from pipeline.util.regex_tools import preoperative_rational_regex, operative_axilla_regex, operative_breast_regex
from pipeline.util.utils import get_full_path


def run_operative_pipeline(start: int, end: int, skip: List[int],
                           path_to_output: str = get_full_path("data/output/operative_results/"),
                           path_to_input: str = get_full_path("data/input/operative_reports/"),
                           path_to_text: str = get_full_path("data/input/operative_reports/operative_reports_text/"),
                           path_to_reports: str = get_full_path("data/input/operative_reports/"),
                           path_to_code_book: str = get_full_path("data/utils/operative_code_book.ods"),
                           path_to_pdf_human_cols: str = get_full_path("data/utils/operative_column_mappings.csv"),
                           baseline_version: str = "data_collection_baseline_VZ_48.csv",
                           baseline_path: str = get_full_path("data/baselines/"),
                           path_to_weights: str = get_full_path("data/utils/training_metrics/params/tuning.csv"),
                           substitution_cost: int = 1,
                           largest_cost: int = 4) -> dict:
    """
    REQUIRES: Operative reports do not need to be converted by Adobe OCR, instead we use Pytesseract: https://pypi.org/project/pytesseract/
    Pytesseract works very well with text data, but very badly with numerical data, especially zeros

    :param path_to_input:               the path to the inputs
    :param path_to_text:                the path to the image and text files that Pytesseract generates
    :param path_to_weights:             the path to the weights for each column that is used in edit distance
    :param substitution_cost:           a default substitution cost for edit distance if none is provided
    :param largest_cost:                a default overall cost for edit distance if none is provided
    :param skip:                        any reports to skip
    :param baseline_path:               the path to the directory where he golden standard is
    :param baseline_version:            which version of the golden standard to use
    :param path_to_code_book:           path to the encodings
    :param path_to_pdf_human_cols:      path to the column mappings
    :param path_to_output:              path to all the outputted information
    :param start:                       the first report
    :param end:                         the last report
    :param path_to_reports:             path to where the pdf reports are held
    """
    pdf_col_human_col = import_pdf_human_cols(path_to_pdf_human_cols)
    code_book = import_code_book(path_to_code_book)
    paths_to_pdfs = get_input_paths(start=start, end=end, skip=skip, path_to_reports=path_to_reports,
                                    report_str="{} OR_Redacted.pdf")
    paths_to_texts = get_input_paths(start=start, end=end, skip=skip, path_to_reports=path_to_text,
                                     report_str="{} OR_Redacted.txt")

    # this is only needed to run once. converts pdfs to images that can be changed to text with ocr. all the images and
    # text are saved in path_to_ocr
    if not os.path.exists(path_to_text):
        convert_pdf_to_text(path_to_text=path_to_text, path_to_input=path_to_input, paths_to_pdfs=paths_to_pdfs,
                            paths_to_texts=paths_to_texts)

    # the pdfs are converted into text files which is read into the pipeline with this function.
    # returns list[Report] with only report and id and report type
    uncleaned_text = load_in_reports(start=start, end=end, skip=skip, paths_to_texts=paths_to_texts)

    # returns list[Report] with everything BUT encoded and not_found initialized
    cleaned_emr, ids_without_synoptic = clean_up_reports(emr_text=uncleaned_text)

    # and all the subsections are lists
    studies_with_general_extractions = get_general_extractions(list_reports=cleaned_emr)

    # raw to spreadsheet, no altering has been done
    reports_to_spreadsheet(studies_with_general_extractions, type_of_report="unfiltered_reports",
                           path_to_output=path_to_output,
                           function=change_unfiltered_to_dict)

    for report in studies_with_general_extractions:
        print(report.report_id)
        print(report.extractions)

    studies_with_cleaned_extractions = extract_cols(reports=studies_with_general_extractions,
                                                    pdf_human_cols=pdf_col_human_col)
    # turning raw text values into spreadsheet
    raw_reports_to_spreadsheet(reports=studies_with_cleaned_extractions, pdf_human_cols=pdf_col_human_col,
                               path_to_output=path_to_output)

    # changing the raw text into codes
    encoded_reports = code_extractions(reports=studies_with_cleaned_extractions, substitution_cost=substitution_cost,
                                       largest_cost=largest_cost, code_book_path=path_to_code_book,
                                       path_to_weights=path_to_weights)

    # turning coded to spreadsheets
    dataframe_coded = reports_to_spreadsheet(reports=encoded_reports, path_to_output=path_to_output,
                                             type_of_report="coded", function=add_report_id)

    # doing nice comparison
    training_dict = nice_compare(baseline_version=baseline_version, pipeline_dataframe=dataframe_coded,
                                 baseline_path=baseline_path,
                                 path_to_outputs=path_to_output)

    return training_dict
