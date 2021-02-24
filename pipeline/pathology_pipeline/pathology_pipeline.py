from pipeline.pathology_pipeline.postprocessing.highlight_differences import highlight_csv_differences
from pipeline.pathology_pipeline.postprocessing.write_excel import save_dictionaries_into_csv_raw
from pipeline.pathology_pipeline.preprocessing import read_pdf
from pipeline.pathology_pipeline.preprocessing.isolate_sections import isolate_synoptic_sections, \
    isolate_final_diagnosis_sections
from pipeline.pathology_pipeline.preprocessing.resolve_ocr_spaces import preprocess_resolve_ocr_spaces
from pipeline.pathology_pipeline.processing.columns import get_column_mappings
from pipeline.pathology_pipeline.processing.encode_extractions import encode_extractions_to_dataframe
from pipeline.pathology_pipeline.processing.process_synoptic import process_synoptics_and_ids
from pipeline.util.utils import get_full_path, get_current_time, find_all_vocabulary


def run_pathology_pipeline(start,
                           end,
                           skip,
                           print_debug=True,
                           max_edit_distance_missing=5,
                           max_edit_distance_autocorrect=5,
                           substitution_cost=2,
                           resolve_ocr=True,
                           path_to_output_csv=get_full_path("data/output/pathology_results/csv_files/"),
                           path_to_output_excel=get_full_path("data/output/pathology_results/excel_files/"),
                           path_to_baselines=get_full_path("data/baselines/"),
                           path_to_mappings=get_full_path("data/utils/pathology_column_mappings.xlsx"),
                           path_to_reports=get_full_path("data/input/pathology_reports/"),
                           path_to_stages=get_full_path("data/utils/stages.csv"),
                           pickle_path=get_full_path("data/utils/excluded_autocorrect_column_pairs.data")):
    """
    REQUIRES: the pdf document must be converted to searchable format by Adobe OCR in advance

    :param path_to_output_excel:
    :param path_to_output_csv:
    :param pickle_path:
    :param path_to_stages:
    :param path_to_reports:
    :param path_to_mappings:
    :param path_to_baselines:
    :param path_to_output:                str;              path to output
    :param start:
    :param end:
    :param skip:
    :param print_debug:                   boolean;          print debug statements in Terminal if True
    :param max_edit_distance_autocorrect: int;              the maximum edit distance for autocorrecting extracted pairs
    :param max_edit_distance_missing:     int;              the maximum edit distance for searching for missing cell values
    :param substitution_cost:             int;              the substitution cost for edit distance
    :param resolve_ocr:                   boolean;          resolve ocr white space if true
    :return:                              a list of tuples; e.g. (5,6,1 (1600,20,30,100,70)) means missing dist. = 5, auto dist. = 6, sub_cost=1, same=1600, diff=20,missing=30, extra=100, zero=70.
    :return:                              pandas DataFrame; information about auto-correct
    """

    # input pdf paths
    input_pdf_paths = read_pdf.get_input_paths(start, end, skip=skip, path_to_reports=path_to_reports)

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

    column_mappings = get_column_mappings(path_to_mappings)

    # convert pdf reports to a list of (pdf_string, study_id) tuples
    strings_and_ids = read_pdf.pdfs_to_strings(input_pdf_paths, do_preprocessing=True, print_debug=print_debug)
    print(strings_and_ids[1][0])

    medical_vocabulary = find_all_vocabulary([string for (string, study_id) in strings_and_ids],
                                             print_debug=print_debug,
                                             min_freq=40)
    if resolve_ocr:
        strings_and_ids = preprocess_resolve_ocr_spaces(strings_and_ids,
                                                        print_debug=print_debug,
                                                        medical_vocabulary=medical_vocabulary)

    # isolate and extract the synoptic reports from all data
    synoptics_and_ids, ids_without_synoptics = isolate_synoptic_sections(strings_and_ids,
                                                                         print_debug=print_debug)

    # this is the str of PDFs that do not contain any Synoptic Report section
    without_synoptics_strs_and_ids = [(string, study_id) for string, study_id in strings_and_ids if
                                      study_id in ids_without_synoptics]

    # If the PDF doesn't contain a synoptic section, use the Final Diagnosis section instead
    final_diagnosis_and_ids, ids_without_final_diagnosis = isolate_final_diagnosis_sections(
        without_synoptics_strs_and_ids,
        print_debug=print_debug)

    if print_debug:
        if len(ids_without_final_diagnosis) > 0:
            s = "Study IDs with neither Synoptic Report nor Final Diagnosis: {}".format(ids_without_final_diagnosis)
            print(s)

    synoptic_dictionaries, autocorrect_df = process_synoptics_and_ids(synoptics_and_ids, column_mappings,
                                                                      path_to_stages=path_to_stages,
                                                                      print_debug=print_debug,
                                                                      max_edit_distance_missing=max_edit_distance_missing,
                                                                      max_edit_distance_autocorrect=max_edit_distance_autocorrect,
                                                                      substitution_cost=substitution_cost,
                                                                      pickle_path=pickle_path)

    synoptic_dictionaries = [d for d in synoptic_dictionaries if d]  # remove None from list

    final_diagnosis_dictionaries = []

    all_dictionaries = synoptic_dictionaries + final_diagnosis_dictionaries
    df_raw = save_dictionaries_into_csv_raw(all_dictionaries,
                                            column_mappings,
                                            csv_path=csv_path_raw,
                                            print_debug=print_debug)

    df_coded = encode_extractions_to_dataframe(df_raw, print_debug=print_debug)

    df_coded.to_csv(csv_path_coded, index=False)

    stats = highlight_csv_differences(csv_path_coded,
                                      csv_path_baseline_SY,  # this is comparing to SY's baseline
                                      excel_path_highlight_differences,
                                      print_debug=print_debug)

    if print_debug:
        s = "\nPipeline process finished.\nStats:{}".format(stats)
        print(s)

    return stats, autocorrect_df
