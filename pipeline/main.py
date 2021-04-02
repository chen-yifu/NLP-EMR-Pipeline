"""
pipeline starts here
"""

from pipeline.emr_pipeline import run_pipeline
from pipeline.postprocessing.highlight_differences import highlight_csv_differences
from pipeline.postprocessing.report_specific_encoding import nottingham_score, process_mm_val, archtectural_patterns, \
    tumour_site, number_of_foci, do_nothing
from pipeline.preprocessing.resolve_ocr_spaces import find_pathologic_stage
from pipeline.util.report_type import ReportType
from pipeline.util.utils import get_full_path

cols_to_skip = ["study #", "specimen", "treatment effect", "margins", "pathologic stage", "comment(s)",
                "part(s) involved"]
multi_line_cols = ["SPECIMEN", "Treatment Effect", "Margins", "pathologic stage", "comment(s)",
                   "Part(s) Involved:"]

# pathology pipeline
run_pipeline(start=101, end=156,
             report_type=ReportType.NUMERICAL,
             cols_to_skip=cols_to_skip,
             multi_line_cols=multi_line_cols,
             report_name="pathology",
             is_anchor=True,
             sep_list=["invasive carcinoma"],
             report_ending="Path_Redacted.pdf",
             baseline_versions=["pathology_VZ.csv", "pathology_SY.csv"],
             anchor=r"^ *-* *",
             other_paths={"pickle path": get_full_path("data/utils/excluded_autocorrect_column_pairs.data")},
             tools={"pathologic stage": find_pathologic_stage,
                    "nottingham_score": nottingham_score,
                    "process_mm_val": process_mm_val,
                    "number_of_foci": number_of_foci,
                    "tumour_site": tumour_site,
                    "do_nothing": do_nothing,
                    "archtectural_patterns": archtectural_patterns})

# operative pipeline
run_pipeline(start=1, end=50,
             report_type=ReportType.TEXT,
             anchor=r"^\d*\.* *", is_anchor=True, use_seperator_to_capture=True,
             single_line_list=["neoadjuvant treatment", "neoadjuvant treatment?"],
             cols_to_skip=["immediate reconstruction mentioned", "laterality",
                           "reconstruction mentioned"],
             sep_list=["surgical indication", "immediate reconstruction type"],
             report_name="operative", report_ending="OR_Redacted.pdf",
             contained_capture_list=["breast incision type", "immediate reconstruction type"],
             no_anchor_list=["neoadjuvant treatment", "immediate reconstruction mentioned",
                             "localization"],
             other_paths={
                 "path to weights": get_full_path("data/utils/training_metrics/params/tuning.csv")},
             baseline_versions=["operative_VZ.csv", "operative_SY.csv"])

# difference between the two human baselines
stats_human_baselines_p = highlight_csv_differences(csv_path_coded="../data/baselines/pathology_SY.csv",
                                                    csv_path_human="../data/baselines/pathology_VZ.csv",
                                                    report_type="Human Baselines",
                                                    output_excel_path="../data/output/compare_human_baseline_pathology.xlsx")

# difference between the two human baselines
stats_human_baselines_o = highlight_csv_differences(csv_path_coded="../data/baselines/operative_SY.csv",
                                                    csv_path_human="../data/baselines/operative_VZ.csv",
                                                    report_type="Human Baselines",
                                                    output_excel_path="../data/output/compare_human_baseline_operative.xlsx")

print("Comparing human baselines for pathology:", stats_human_baselines_p)
print("Comparing human baselines for operative:", stats_human_baselines_o)
