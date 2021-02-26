# import paths for operative report
from pipeline.util.utils import get_full_path, get_current_time

path_to_output = get_full_path("data/output/operative_results/")
path_to_input = get_full_path("data/input/operative_reports/")
path_to_text = get_full_path("data/input/operative_reports/operative_reports_text/")
path_to_op_reports = get_full_path("data/input/operative_reports/")
path_to_code_book = get_full_path("data/utils/operative_code_book.ods")
path_op_mappings = get_full_path("data/utils/operative_column_mappings.csv")
baseline_version = "data_collection_baseline_VZ_48.csv"
baseline_path = get_full_path("data/baselines/")
path_to_weights = get_full_path("data/utils/training_metrics/params/tuning.csv")

# important paths for pathology report
timestamp = get_current_time()
path_to_output_csv = get_full_path("data/output/pathology_results/csv_files/")
path_to_output_excel = get_full_path("data/output/pathology_results/excel_files/")
path_to_baselines = get_full_path("data/baselines/")
path_to_path_mappings = get_full_path("data/utils/pathology_column_mappings.csv")
path_to_path_reports = get_full_path("data/input/pathology_reports/")
path_to_stages = get_full_path("data/utils/stages.csv")
pickle_path = get_full_path("data/utils/excluded_autocorrect_column_pairs.data")
csv_path_raw = path_to_output_csv + "raw_{}.csv".format(timestamp)
csv_path_coded = path_to_output_csv + "coded_{}.csv".format(timestamp)
csv_path_baseline_VZ = get_full_path("data/baselines/data_collection_baseline_VZ.csv")
csv_path_baseline_SY = get_full_path("data/baselines/data_collection_baseline_SY.csv")

export_operative_paths = {"path_to_output": path_to_output, "path_to_input": path_to_input,
                          "path_to_text": path_to_text, "path_to_op_reports": path_to_op_reports,
                          "path_to_code_book": path_to_code_book, "path_op_mappings": path_op_mappings,
                          "baseline_version": baseline_version, "baseline_path": baseline_path,
                          "path_to_weights": path_to_weights}

export_pathology_paths = {"timestamp": timestamp, "path_to_output_csv": path_to_output_csv,
                          "path_to_output_excel": path_to_output_excel,
                          "path_to_baselines": path_to_baselines, "path_to_path_mappings": path_to_path_mappings,
                          "path_to_path_reports": path_to_path_reports, "path_to_stages": path_to_stages,
                          "pickle_path": pickle_path, "csv_path_raw": csv_path_raw, "csv_path_coded": csv_path_coded,
                          "csv_path_baseline_VZ": csv_path_baseline_VZ, "csv_path_baseline_SY": csv_path_baseline_SY}
