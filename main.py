"""
2021 Yifu (https://github.com/chen-yifu) and Lucy (https://github.com/lhao03)
Main file to run from.
"""
from typing import Tuple, Any
from pipeline.emr_pipeline import EMRPipeline
from pipeline.processing.autocorrect_specific_functions import *
from pipeline.processing.encoding_specific_functions import *
from pipeline.processing.extraction_specific_functions import *
from pipeline.utils.report_type import ReportType
from pipeline.utils.utils import get_full_path

validation_p = ["pathology_validation_D.csv", "pathology_validation_VZ.csv"]
training_p = ["pathology_VZ.csv"]
validation_o = [
    # "operative_validation_D.csv",
    "operative_validation_VZ.csv"]
training_o = ["operative_VZ.csv"]

# operative pipeline
operative_pipeline = EMRPipeline(start=1, end=50, report_name="operative", report_ending="V.pdf",
                                 report_type=ReportType.ALPHA)

# pathology pipeline
pathology_pipeline = EMRPipeline(
    start=101, end=150, report_name="pathology", report_ending="V.pdf",
    report_type=ReportType.NUMERICAL,
    other_paths={"stages": get_full_path("data/utils/pathology_reports/stages.csv")})


def pathology_pipeline_main() -> Tuple[Any, pd.DataFrame]:
    """ Main method to run the pathology pipeline"""

    return pathology_pipeline.run_pipeline(
        baseline_versions=validation_p,
        anchor=r"^ *-* *",
        cols_to_skip=["study #", "nottingham score", "closest margin", "closest margin1"],
        val_on_next_line_cols_to_add=["SPECIMEN", "Treatment Effect", "Margins", "comment(s)", "Part(s) Involved:"],
        encoding_tools={"nottingham_score": nottingham_score,
                        "process_mm_val": process_mm_val,
                        "number_of_foci": number_of_foci,
                        "tumour_site": tumour_site,
                        "archtectural_patterns": archtectural_patterns},
        autocorrect_tools={"pathologic stage": find_pathologic_stage},
        extraction_tools=[no_lymph_node, negative_for_dcis, no_dcis_extent, in_situ, duplicate_lymph_nodes,
                          find_num_foci])


def operative_pipeline_main() -> Tuple[Any, pd.DataFrame]:
    """ Main method to run the operative pipeline"""

    return operative_pipeline.run_pipeline(
        baseline_versions=validation_o,
        anchor=r"^\d*\.* *",
        cols_to_skip=["study #", "immediate reconstruction mentioned", "laterality",
                      "reconstruction mentioned"],
        encoding_tools={"immediate_reconstruction_mentioned": immediate_reconstruction_mentioned},
        filter_values=True,
        filter_func_args=("indication", ["prophylaxis", "prophylactic"]),
        resolve_ocr=False)


# def operative_gui():
#     operative_app = OperativeEMRApp()
#     operative_app.geometry("1280x740")
#     operative_app.mainloop()

# def pathology_gui():
#     pathology_app = PathologyEMRApp()
#     pathology_app.geometry("1280x740")
#     pathology_app.mainloop()

# pathology_gui()
# operative_gui()
pathology_pipeline_main()
operative_pipeline_main()
