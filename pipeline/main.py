"""
pipeline starts here
"""
from pipeline.emr_pipeline import run_pipeline
from pipeline.pathology_pipeline.preprocessing.resolve_ocr_spaces import find_pathologic_stage
from pipeline.util.report_type import ReportType
from pipeline.util.utils import get_full_path

cols_to_skip = ["study #", "specimen", "treatment effect", "margins", "pathologic stage", "comment(s)",
                "part(s) Involved"]
multi_line_cols = ["SPECIMEN", "Treatment Effect", "Margins", "pathologic stage", "comment(s)",
                   "Part(s) Involved:"]

run_pipeline(start=101, end=156, skip=[140], report_type=ReportType.NUMERICAL, cols_to_skip=cols_to_skip,
             multi_line_cols=multi_line_cols, report_name="pathology", report_ending="Path_Redacted.pdf",
             baseline_version="data_collection_baseline_VZ.csv",
             other_paths={"pickle path": get_full_path("data/utils/excluded_autocorrect_column_pairs.data")},
             tools={"pathologic stage": find_pathologic_stage})

run_pipeline(start=1, end=48, skip=[22, 43], report_type=ReportType.TEXT,
             cols_to_skip=[["Immediate Reconstruction Mentioned", "Laterality"]], report_name="operative",
             report_ending="OR_Redacted.pdf", other_paths={
        "path to weights": get_full_path("data/utils/training_metrics/params/tuning.csv"),
        "path to code book": get_full_path("data/utils/operative_code_book.ods")},
             baseline_version="data_collection_baseline_VZ_48.csv")
