# electronic medical records pipeline for synoptic sections

to install dependencies, run

```
pip install -r requirements.txt
```

## To use

There are several folders that need to have certain files in them:

- in the data folder:
    - baselines: put all your human encoded baselines here (if you plan to fine tune the pipeline). Your baselines
      should be in csv format.
    - input: make a new folder named {report_type}_reports and put all your reports in the {report_type}_reports folder.
    - output: make a new folder named {report_type}_results. All of the pipeline's output such as raw extractions and
      encoded extractions will go here. The subfolders will be automatically generated in the {report_type}_results
      folder.
    - utils: you must have
        - {report_type}_code_book.ods
        - {report_type}_column_mappings.csv
        - stages.csv (optional, for pathology breast cancer reports only)
        - {report_type}_excluded_autocorrect_column_pairs.data (used mainly in gui)

## Sample usage

```python
from pipeline.emr_pipeline import EMRPipeline
from pipeline.preprocessing.resolve_ocr_spaces import find_pathologic_stage
from pipeline.processing.specific_functions import *
from pipeline.utils.report_type import ReportType

my_pipeline = EMRPipeline(
    start=101, end=150, report_name="pathology", report_ending="V.pdf", report_type=ReportType.NUMERICAL)

my_pipeline.run_pipeline(
    sep_list=["invasive carcinoma", "in situ component"],
    baseline_versions=["operative_validation.csv", "operative_validation_other.csv"],
    anchor=r"^ *-* *",
    add_anchor=True,
    multi_line_cols=["SPECIMEN", "Treatment Effect", "Margins"],
    cols_to_skip=["study #", "specimen", "treatment effect", "margins"],
    tools={"pathologic stage": find_pathologic_stage,
           "nottingham_score": nottingham_score,
           "process_mm_val": process_mm_val,
           "archtectural_patterns": archtectural_patterns},
    extraction_tools=[no_lymph_node, negative_for_dcis],
    do_training=False,
    filter_values=False)
```