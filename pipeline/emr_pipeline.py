import os
from typing import List
from pipeline.operative_pipeline.postprocessing.compare_excel import nice_compare
from pipeline.operative_pipeline.postprocessing.to_spreadsheet import reports_to_spreadsheet, \
    raw_reports_to_spreadsheet, change_unfiltered_to_dict, add_report_id
from pipeline.operative_pipeline.preprocessing.extract_cols import extract_cols
from pipeline.operative_pipeline.preprocessing.extract_synoptic_operative import clean_up_reports
from pipeline.operative_pipeline.preprocessing.scanned_pdf_to_text import load_in_pdfs, load_in_txts
from pipeline.operative_pipeline.processing.encode_extractions import code_extractions
from pipeline.operative_pipeline.processing.extract_extractions import get_general_extractions
from pipeline.pathology_pipeline.postprocessing.highlight_differences import highlight_csv_differences
from pipeline.pathology_pipeline.postprocessing.write_excel import save_dictionaries_into_csv_raw
from pipeline.pathology_pipeline.preprocessing.isolate_sections import isolate_final_diagnosis_sections
from pipeline.pathology_pipeline.preprocessing.resolve_ocr_spaces import preprocess_resolve_ocr_spaces
from pipeline.pathology_pipeline.processing.encode_extractions import encode_extractions_to_dataframe
from pipeline.pathology_pipeline.processing.process_synoptic import process_synoptics_and_ids
from pipeline.util.import_tools import import_pdf_human_cols, import_code_book, get_input_paths
from pipeline.util.paths import export_operative_paths, export_pathology_paths
from pipeline.util.report_type import ReportType
from pipeline.util.utils import find_all_vocabulary


def run_pipeline(start: int, end: int, skip: List[int], report_type: ReportType,
                 print_debug: bool = True,
                 max_edit_distance_missing: int = 5,
                 max_edit_distance_autocorrect_path: int = 5,
                 substitution_cost_oper: int = 1,
                 max_edit_distance_autocorrect_oper: int = 4,
                 substitution_cost_path: int = 2,
                 resolve_ocr=True):
    """
    :param start:                                   the first report id
    :param end:                                     the last report id
    :param skip:                                    reports to skip based on id
    :param report_type:                             the type of report being analyzed, is an Enum
    :param print_debug:                             print debug statements in Terminal if True
    :param max_edit_distance_missing:               the maximum edit distance for searching for missing cell values
    :param max_edit_distance_autocorrect_path:      the maximum edit distance for autocorrecting extracted pairs for pathology
    :param substitution_cost_oper:                  the substitution cost for edit distance for operative
    :param max_edit_distance_autocorrect_oper:      the maximum edit distance for autocorrecting extracted pairs for operative
    :param substitution_cost_path:                  the substitution cost for edit distance for pathology
    :param resolve_ocr:                             resolve ocr white space if true
    :return:
    """
    # import paths for operative report
    operative_paths = export_operative_paths
    code_book = import_code_book(operative_paths["path_to_code_book"])
    paths_to_pdfs = get_input_paths(start, end, skip, operative_paths["path_to_op_reports"], "{} OR_Redacted.pdf")
    operative_text_paths = get_input_paths(start, end, skip, operative_paths["path_to_text"],
                                           "{} OR_Redacted.txt")

    # important paths for pathology report
    pathology_paths = export_pathology_paths
    pathology_pdf_paths = get_input_paths(start, end, skip=skip,
                                          path_to_reports=pathology_paths["path_to_path_reports"],
                                          report_str="{} Path_Redacted.pdf")
    excel_path_highlight_differences = pathology_paths["path_to_output_excel"] + \
                                       "compare_{}_corD{}_misD{}_subC{}_STAT.xlsx".format(pathology_paths["timestamp"],
                                                                                          max_edit_distance_autocorrect_path,
                                                                                          max_edit_distance_missing,
                                                                                          substitution_cost_path)

    # this is only needed to run once. converts pdfs to images that can be changed to text with ocr. all the images and
    # text are saved in path_to_ocr
    if not os.path.exists(operative_paths["path_to_text"]):
        load_in_pdfs(path_to_text=operative_paths["path_to_text"], path_to_input=operative_paths["path_to_input"],
                     paths_to_pdfs=paths_to_pdfs,
                     paths_to_texts=operative_text_paths)

    # the pdfs are converted into text files which is read into the pipeline with this function.
    # returns list[Report] with only report and id and report type
    correct_paths_to_reports = operative_text_paths if report_type is ReportType.OPERATIVE else pathology_pdf_paths
    reports_string_form = load_in_txts(start=start, end=end, skip=skip, paths_to_texts=correct_paths_to_reports)

    medical_vocabulary = find_all_vocabulary([report.text for report in reports_string_form],
                                             print_debug=print_debug,
                                             min_freq=40)

    if resolve_ocr:
        reports_string_form = preprocess_resolve_ocr_spaces(reports_string_form, print_debug=print_debug,
                                                            medical_vocabulary=medical_vocabulary)

    # returns list[Report] with everything BUT encoded and not_found initialized
    cleaned_emr, ids_without_synoptic = clean_up_reports(emr_text=reports_string_form)

    # split starts here
    if report_type is ReportType.PATHOLOGY:
        column_mappings = import_pdf_human_cols(pathology_paths["path_to_path_mappings"])

        # this is the str of PDFs that do not contain any Synoptic Report section
        without_synoptics_strs_and_ids = [report for report in reports_string_form if
                                          report.report_id in ids_without_synoptic]

        # If the PDF doesn't contain a synoptic section, use the Final Diagnosis section instead
        final_diagnosis_reports, ids_without_final_diagnosis = isolate_final_diagnosis_sections(
            without_synoptics_strs_and_ids,
            print_debug=print_debug)

        if print_debug:
            if len(ids_without_final_diagnosis) > 0:
                s = "Study IDs with neither Synoptic Report nor Final Diagnosis: {}".format(ids_without_final_diagnosis)
                print(s)

        filtered_reports, autocorrect_df = process_synoptics_and_ids(cleaned_emr,
                                                                     column_mappings,
                                                                     path_to_stages=pathology_paths["path_to_stages"],
                                                                     print_debug=print_debug,
                                                                     max_edit_distance_missing=max_edit_distance_missing,
                                                                     max_edit_distance_autocorrect=max_edit_distance_autocorrect_path,
                                                                     substitution_cost=substitution_cost_path,
                                                                     pickle_path=pathology_paths["pickle_path"])

        filtered_reports = [report for report in filtered_reports if report.extractions]  # remove None from list

        final_diagnosis_reports = []

        all_reports = filtered_reports + final_diagnosis_reports
        df_raw = save_dictionaries_into_csv_raw(all_reports,
                                                column_mappings,
                                                csv_path=pathology_paths["csv_path_raw"],
                                                print_debug=print_debug)

        df_coded = encode_extractions_to_dataframe(df_raw, print_debug=print_debug)

        df_coded.to_csv(pathology_paths["csv_path_coded"], index=False)

        stats = highlight_csv_differences(pathology_paths["csv_path_coded"],
                                          pathology_paths["csv_path_baseline_SY"],
                                          excel_path_highlight_differences,
                                          print_debug=print_debug)

        if print_debug:
            print("\nPipeline process finished.\nStats:{}".format(stats))

        return stats, autocorrect_df

    elif report_type is ReportType.OPERATIVE:
        op_mappings = import_pdf_human_cols(operative_paths["path_op_mappings"])
        # and all the subsections are lists
        studies_with_general_extractions = get_general_extractions(list_reports=cleaned_emr)

        # raw to spreadsheet, no altering has been done
        reports_to_spreadsheet(studies_with_general_extractions, type_of_report="unfiltered_reports",
                               path_to_output=operative_paths["path_to_output"],
                               function=change_unfiltered_to_dict)

        for report in studies_with_general_extractions:
            print(report.report_id)
            print(report.extractions)

        studies_with_cleaned_extractions = extract_cols(reports=studies_with_general_extractions,
                                                        pdf_human_cols=op_mappings)
        # turning raw text values into spreadsheet
        raw_reports_to_spreadsheet(reports=studies_with_cleaned_extractions, pdf_human_cols=op_mappings,
                                   path_to_output=operative_paths["path_to_output"])

        # changing the raw text into codes
        encoded_reports = code_extractions(reports=studies_with_cleaned_extractions,
                                           substitution_cost=substitution_cost_oper,
                                           largest_cost=max_edit_distance_autocorrect_oper, code_book=code_book,
                                           path_to_weights=operative_paths["path_to_weights"])

        # turning coded to spreadsheets
        dataframe_coded = reports_to_spreadsheet(reports=encoded_reports,
                                                 path_to_output=operative_paths["path_to_output"],
                                                 type_of_report="coded", function=add_report_id)

        # doing nice comparison
        training_dict = nice_compare(baseline_version=operative_paths["baseline_version"],
                                     pipeline_dataframe=dataframe_coded,
                                     baseline_path=operative_paths["baseline_path"],
                                     path_to_outputs=operative_paths["path_to_output"])

        return training_dict
