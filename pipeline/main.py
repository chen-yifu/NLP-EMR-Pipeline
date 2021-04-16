"""
main file to invoke methods
"""
from pipeline.emr_pipeline import EMRPipeline
from pipeline.processing.report_specific_encoding import nottingham_score, process_mm_val, archtectural_patterns, \
    tumour_site, number_of_foci, do_nothing, immediate_reconstruction_mentioned
from pipeline.preprocessing.resolve_ocr_spaces import find_pathologic_stage
from pipeline.utils.report_type import ReportType
from pipeline.utils.utils import get_full_path


def main():
    """ Main method to run the pipeline"""

    # pathology pipeline
    pathology_pipeline = EMRPipeline(
        start=101, end=156, report_name="pathology", report_ending="Path_Redacted.pdf",
        report_type=ReportType.NUMERICAL,
        other_paths={"pickle path": get_full_path("data/utils/excluded_autocorrect_column_pairs.data")})

    pathology_pipeline.run_pipeline(sep_list=["invasive carcinoma"],
                                    baseline_versions=["pathology_VZ.csv"],
                                    anchor=r"^ *-* *",
                                    add_anchor=True,
                                    multi_line_cols=["SPECIMEN", "Treatment Effect", "Margins", "pathologic stage",
                                                     "comment(s)",
                                                     "Part(s) Involved:"],
                                    cols_to_skip=["study #", "specimen", "treatment effect", "margins",
                                                  "pathologic stage", "comment(s)",
                                                  "part(s) involved", "nottingham score"],
                                    tools={"pathologic stage": find_pathologic_stage,
                                           "nottingham_score": nottingham_score,
                                           "process_mm_val": process_mm_val,
                                           "number_of_foci": number_of_foci,
                                           "tumour_site": tumour_site,
                                           "do_nothing": do_nothing,
                                           "archtectural_patterns": archtectural_patterns},
                                    do_training=False)

    # operative pipeline
    operative_pipeline = EMRPipeline(start=1, end=50, report_name="operative", report_ending="OR_Redacted.pdf",
                                     report_type=ReportType.ALPHA)

    operative_pipeline.run_pipeline(baseline_versions=["operative_VZ.csv"], anchor=r"^\d*\.* *",
                                    single_line_list=["neoadjuvant treatment", "neoadjuvant treatment?"],
                                    use_separator_to_capture=True,
                                    add_anchor=True,
                                    cols_to_skip=["immediate reconstruction mentioned", "laterality",
                                                  "reconstruction mentioned"],
                                    contained_capture_list=["breast incision type", "immediate reconstruction type"],
                                    no_anchor_list=["neoadjuvant treatment", "immediate reconstruction mentioned",
                                                    "localization"],
                                    tools={"immediate_reconstruction_mentioned": immediate_reconstruction_mentioned},
                                    sep_list=["surgical indication", "immediate reconstruction type"],
                                    perform_autocorrect=True,
                                    do_training=False)


main()
