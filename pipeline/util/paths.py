from pipeline.util.utils import get_full_path, get_current_time


def get_paths(report_type: str, other_paths=None) -> dict:
    """
    Creates a set of paths to be used by the pipeline.

    :param report_type:           the report name. should be same for all reports you want to use the pipeline on
    :param other_paths:           any additional paths which are not covered by the function.
    :return:
    """
    timestamp = get_current_time()
    if other_paths is None:
        other_paths = {}
    paths = {}
    path_to_input = get_full_path("data/input/{}_reports/".format(report_type))
    path_to_code_book = get_full_path("data/utils/{}_code_book.ods".format(report_type))
    path_to_output = get_full_path("data/output/{}_results/".format(report_type))
    path_to_reports = get_full_path("data/input/{}_reports/".format(report_type))
    path_to_baselines = get_full_path("data/baselines/")
    path_to_output_csv = get_full_path("data/output/{}_results/csv_files/".format(report_type))
    csv_path_raw = path_to_output_csv + "raw_{}.csv".format(timestamp)
    csv_path_coded = path_to_output_csv + "coded_{}.csv".format(timestamp)
    path_to_output_excel = get_full_path("data/output/{}_results/excel_files/".format(report_type))
    path_to_mappings = get_full_path("data/utils/{}_column_mappings.csv".format(report_type))
    paths.update(other_paths)
    paths.update(
        {"path to output": path_to_output, "path to reports": path_to_reports, "path to baselines": path_to_baselines,
         "path to output csv": path_to_output_csv, "path to output excel": path_to_output_excel,
         "path to mappings": path_to_mappings, "csv path raw": csv_path_raw,
         "csv path coded": csv_path_coded, "path to code book": path_to_code_book, "path to input": path_to_input})
    return paths
