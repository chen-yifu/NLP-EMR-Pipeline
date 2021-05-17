"""
main file to invoke methods
"""
from typing import Tuple, Any
from pipeline.emr_pipeline import EMRPipeline
from pipeline.processing.specific_functions import *
from pipeline.utils.report_type import ReportType
from pipeline.utils.utils import get_full_path

validation_p = ["pathology_validation_D.csv", "pathology_validation_VZ.csv"]
training_p = ["pathology_VZ.csv"]
validation_o = ["operative_validation_D.csv", "operative_validation_VZ.csv"]
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
        sep_list=["invasive carcinoma", "in situ component", "in situ component type", "insitu component",
                  "insitu type"],
        baseline_versions=validation_p,
        anchor=r"^ *-* *",
        add_anchor=True,
        multi_line_cols=["SPECIMEN", "Treatment Effect", "Margins", "pathologic stage", "comment(s)",
                         "Part(s) Involved:"],
        cols_to_skip=["study #", "specimen", "treatment effect", "margins", "pathologic stage", "comment(s)",
                      "part(s) involved", "nottingham score", "closest margin", "closest margin1"],
        encoding_tools={"nottingham_score": nottingham_score,
                        "process_mm_val": process_mm_val,
                        "number_of_foci": number_of_foci,
                        "tumour_site": tumour_site,
                        "do_nothing": do_nothing,
                        "archtectural_patterns": archtectural_patterns},
        autocorrect_tools={"pathologic stage": find_pathologic_stage},
        extraction_tools=[no_lymph_node, negative_for_dcis, no_dcis_extent, in_situ, duplicate_lymph_nodes,
                          find_num_foci],
        do_training_all=False,
        filter_values=False)

    # pathology_pipeline.run_pipeline(
    #     baseline_versions=validation_p,
    #     anchor=r"^ *-* *",
    #     cols_to_skip=["study #", "specimen", "treatment effect", "margins", "pathologic stage", "comment(s)",
    #                   "part(s) involved", "nottingham score", "closest margin", "closest margin1"],
    #     cols_to_add=["SPECIMEN", "Treatment Effect", "Margins", "pathologic stage", "comment(s)",
    #                  "Part(s) Involved:"],
    #     tools={"pathologic stage": find_pathologic_stage,
    #            "nottingham_score": nottingham_score,
    #            "process_mm_val": process_mm_val,
    #            "number_of_foci": number_of_foci,
    #            "tumour_site": tumour_site,
    #            "do_nothing": do_nothing,
    #            "archtectural_patterns": archtectural_patterns},
    #     extraction_tools=[no_lymph_node, negative_for_dcis, no_dcis_extent, in_situ, duplicate_lymph_nodes,
    #                       find_num_foci])


def operative_pipeline_main() -> Tuple[Any, pd.DataFrame]:
    """ Main method to run the operative pipeline"""

    return operative_pipeline.run_pipeline(
        baseline_versions=validation_o,
        anchor=r"^\d*\.* *",
        single_line_list=["neoadjuvant treatment", "neoadjuvant treatment?"],
        use_separator_to_capture=True,
        add_anchor=True,
        cols_to_skip=["immediate reconstruction mentioned", "laterality",
                      "reconstruction mentioned"],
        contained_capture_list=["breast incision type", "immediate reconstruction type"],
        no_anchor_list=["neoadjuvant treatment", "immediate reconstruction mentioned",
                        "localization"],
        encoding_tools={"immediate_reconstruction_mentioned": immediate_reconstruction_mentioned},
        sep_list=["surgical indication", "immediate reconstruction type"],
        perform_autocorrect=True,
        do_training_all=False,
        filter_values=True,
        filter_func=filter_report,
        filter_func_args=("indication", ["prophylaxis", "prophylactic"]),
        resolve_ocr=False)

    # operative_pipeline.run_pipeline(
    #     baseline_versions=validation_o,
    #     anchor=r"^\d*\.* *",
    #     cols_to_skip=["immediate reconstruction mentioned", "laterality",
    #                   "reconstruction mentioned"],
    #     tools={"immediate_reconstruction_mentioned": immediate_reconstruction_mentioned},
    #     perform_autocorrect=True,
    #     filter_values=True,
    #     filter_func=filter_report,
    #     filter_func_args=("indication", ["prophylaxis", "prophylactic"]))


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

operative_pipeline_main()
pathology_pipeline_main()
