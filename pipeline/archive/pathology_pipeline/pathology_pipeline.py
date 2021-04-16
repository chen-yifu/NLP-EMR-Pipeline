from pipeline.preprocessing.extract_synoptic import clean_up_reports
from pipeline.preprocessing.scanned_pdf_to_text import load_in_reports
from pipeline.postprocessing.highlight_differences import highlight_csv_differences
from pipeline.postprocessing.write_excel import save_dictionaries_into_csv_raw
from pipeline.archive.pathology_pipeline.preprocessing.isolate_sections import isolate_final_diagnosis_sections
from pipeline.preprocessing.resolve_ocr_spaces import preprocess_resolve_ocr_spaces
from pipeline.archive.pathology_pipeline.processing.encode_extractions import encode_extractions_to_dataframe
from pipeline.archive.pathology_pipeline.processing.process_synoptic import process_synoptics_and_ids
from pipeline.processing.turn_to_values import turn_reports_extractions_to_values
from pipeline.utils.import_tools import get_input_paths, import_columns, import_pdf_human_cols_tuples
from pipeline.utils.utils import get_full_path, get_current_time, find_all_vocabulary


def run_pathology_pipeline(start,
                           end,
                           print_debug=True,
                           max_edit_distance_missing=5,
                           max_edit_distance_autocorrect=5,
                           substitution_cost=2,
                           resolve_ocr=True,
                           path_to_output_csv=get_full_path("../../data/output/pathology_results/csv_files/"),
                           path_to_output_excel=get_full_path("../../data/output/pathology_results/excel_files/"),
                           path_to_baselines=get_full_path("../../data/baselines/"),
                           path_to_mappings=get_full_path("../../data/utils/pathology_column_mappings.csv"),
                           path_to_reports=get_full_path("../../data/input/pathology_reports/"),
                           path_to_stages=get_full_path("../../data/utils/stages.csv"),
                           pickle_path=get_full_path("../../data/utils/excluded_autocorrect_column_pairs.data")):
    """
    REQUIRES: the pdf document must be converted to searchable format by Adobe OCR in advance

    :param path_to_output_excel:
    :param path_to_output_csv:
    :param pickle_path:
    :param path_to_stages:
    :param path_to_reports:
    :param path_to_mappings:
    :param path_to_baselines:
    :param start:
    :param end:
    :param print_debug:                   boolean;          print debug statements in Terminal if True
    :param max_edit_distance_autocorrect: int;              the maximum edit distance for autocorrecting extracted pairs
    :param max_edit_distance_missing:     int;              the maximum edit distance for searching for missing cell values
    :param substitution_cost:             int;              the substitution cost for edit distance
    :param resolve_ocr:                   boolean;          resolve ocr white space if true
    :return:                              a list of tuples; e.g. (5,6,1 (1600,20,30,100,70)) means missing dist. = 5, auto dist. = 6, sub_cost=1, same=1600, diff=20,missing=30, extra=100, zero=70.
    :return:                              pandas DataFrame; information about auto-correct
    """

    # input pdf paths
    input_pdf_paths = get_input_paths(start, end, path_to_reports=path_to_reports, report_str="{} Path_Redacted.pdf")

    # the path to save raw data
    timestamp = get_current_time()
    csv_path_raw = path_to_output_csv + "raw_{}.csv".format(timestamp)

    # the path to save raw & coded data
    csv_path_coded = path_to_output_csv + "coded_{}.csv".format(timestamp)

    # the path to save excel sheet that highlights the errors/differences
    excel_path_highlight_differences = path_to_output_excel + "compare_{}_corD{}_misD{}_subC{}_STAT.xlsx".format(
        timestamp, max_edit_distance_autocorrect, max_edit_distance_missing, substitution_cost)

    # the path to the csv sheet for the human-annotated baseline csv file
    # Vito's extracted encodings
    csv_path_baseline_VZ = path_to_baselines + "data_collection_baseline_VZ.csv"
    # Sean's extracted encodings
    csv_path_baseline_SY = path_to_baselines + "data_collection_baseline_SY.csv"

    column_mappings = import_columns(path_to_mappings, "")

    # convert pdf reports to a list of reports with report.text and report.report_id
    reports_string_form = load_in_reports(start=start, end=end, paths_to_r=input_pdf_paths)

    medical_vocabulary = find_all_vocabulary([report.text for report in reports_string_form],
                                             print_debug=print_debug,
                                             min_freq=40)
    if resolve_ocr:
        reports_string_form = preprocess_resolve_ocr_spaces(reports_string_form, print_debug=print_debug,
                                                            medical_vocabulary=medical_vocabulary)

    # isolate and extract the synoptic reports from all data
    synoptic_reports, ids_without_synoptic = clean_up_reports(reports_string_form)

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

    filtered_reports, autocorrect_df = process_synoptics_and_ids(synoptic_reports,
                                                                 import_pdf_human_cols_tuples(path_to_mappings,
                                                                                              keep_punc=True),
                                                                 path_to_stages=path_to_stages,
                                                                 print_debug=print_debug,
                                                                 max_edit_distance_missing=max_edit_distance_missing,
                                                                 max_edit_distance_autocorrect=max_edit_distance_autocorrect,
                                                                 substitution_cost=substitution_cost,
                                                                 pickle_path=pickle_path)

    filtered_reports = [report for report in filtered_reports if report.extractions]  # remove None from list

    final_diagnosis_reports = []

    all_reports = filtered_reports + final_diagnosis_reports

    reports_with_values = turn_reports_extractions_to_values(all_reports, column_mappings)

    df_raw = save_dictionaries_into_csv_raw(reports_with_values,
                                            column_mappings,
                                            csv_path=csv_path_raw,
                                            print_debug=print_debug)

    df_coded = encode_extractions_to_dataframe(df_raw, print_debug=print_debug)

    df_coded.to_csv(csv_path_coded, index=False)

    stats = highlight_csv_differences(csv_path_coded,
                                      csv_path_baseline_SY,  # this is comparing to SY's baseline
                                      excel_path_highlight_differences,
                                      print_debug=print_debug,
                                      report_type="pathology")

    if print_debug:
        s = "\nPipeline process finished.\nStats:{}".format(stats)
        print(s)

    return stats, autocorrect_df

# run_pathology_pipeline(start=101, end=156)
