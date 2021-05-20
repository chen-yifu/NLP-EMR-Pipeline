# electronic medical records pipeline for synoptic sections

to install dependencies, run

```
pip install -r requirements.txt
```

## For Windows:

*WSL2 is highly recommended. You can try out command prompt or powershell at your own risk. For development, I reccomend Pycharm Professional or VSCode, as these development environemnts allow you to set up a remote connection to WSL2.* 

- For pytesseract: https://school.geekwall.in/p/9QG6NstS/
- For Tkinter: https://www.techinfected.net/2015/09/how-to-install-and-use-tkinter-in-ubuntu-debian-linux-mint.html
- For using WSL2 as your interpreter in Pycharm Professional: https://www.jetbrains.com/help/pycharm/using-wsl-as-a-remote-interpreter.html#configure-wsl
- For using VSCode and WSL: https://code.visualstudio.com/docs/remote/wsl-tutorial

## For Linux/MacOS:

TODO

# Documentation

## Sample usage

```python
from pipeline.emr_pipeline import EMRPipeline
from pipeline.processing.autocorrect_specific_functions import *
from pipeline.processing.encoding_specific_functions import *
from pipeline.processing.extraction_specific_functions import *
from pipeline.utils.report_type import ReportType

pipeline = EMRPipeline(
    start=101, end=150, report_name="pathology", report_ending="V.pdf",
    report_type=ReportType.NUMERICAL)

pipeline.run_pipeline(
    sep_list=["invasive carcinoma"],
    anchor=r"^ *-* *",
    add_anchor=True,
    val_on_next_line_cols_to_add=["SPECIMEN", "Treatment Effect"],
    cols_to_skip=["study #", "specimen", "treatment effect", "margins"],
    encoding_tools={"nottingham_score": nottingham_score,
                    "process_mm_val": process_mm_val,
                    "number_of_foci": number_of_foci},
    autocorrect_tools={"pathologic stage": find_pathologic_stage},
    extraction_tools=[no_lymph_node, negative_for_dcis],
    baseline_versions=["baseline.csv"])
```

# Folder structure

```shell
.
├── README.md
├── data
│   ├── baselines
│   │   ├── baseline_BB.csv
│   │   └── baseline_AA.csv
│   ├── input
│   │   └── {report_type}_reports
│   │       ├── 1{report_ending}
│   │       ├── 2{report_ending}
│   │       ├── 3{report_ending}
│   │       ├── 5{report_ending}
│   │       ├── 7{report_ending}
│   │       └── 10{report_ending}
│   ├── output
│   │   └── {report_type}_results
│   │       ├── csv_files
│   │       │   ├── coded_02-05-2021~1313.csv
│   │       │   └── raw_30-04-2021~1738.csv
│   │       ├── excel_files
│   │       │   ├── compare_AA_10-05-2021~1051_corD5_misD5_subC2.xlsx
│   │       │   └── compare_BB_11-05-2021~0914_corD5_misD5_subC2.xlsx
│   │       └── training
│   │           ├── all_training_{report_type}_20-04-2021~1036.xlsx
│   │           └── best_training.xlsx
│   └── utils
│       └── {report_type}_reports
│           ├── medical_vocabulary_{report_type}
│           ├── {report_type}_code_book.ods
│           ├── {report_type}_column_mappings.csv
│           ├── {report_type}_regex_rules.csv
│           └── {report_type}_excluded_autocorrect_column_pairs.data
├── main.py
├── {report_type}_gui.py
├── pipeline
│   ├── emr_pipeline.py
│   ├── postprocessing
│   │   ├── highlight_differences.py
│   │   ├── write_csv_excel.py
│   │   └── write_excel.py
│   ├── preprocessing
│   │   ├── extract_synoptic.py
│   │   ├── resolve_ocr_spaces.py
│   │   └── scanned_pdf_to_text.py
│   ├── processing
│   │   ├── autocorrect_specific_functions.py
│   │   ├── clean_text.py
│   │   ├── columns.py
│   │   ├── encode_extractions.py
│   │   ├── encoding_specific_functions.py
│   │   ├── extraction_specific_functions.py
│   │   ├── process_synoptic_general.py
│   │   └── turn_to_values.py
│   └── utils
│       ├── column.py
│       ├── encoding.py
│       ├── import_tools.py
│       ├── paths.py
│       ├── regex_tools.py
│       ├── report.py
│       ├── report_type.py
│       ├── utils.py
│       └── value.py
└── requirements.txt
```

## data folder

The data folder contains all the files the pipeline needs to run and is where the pipeline will output files. The data
folder contains 4 sub folders. In order to facilitate the processing of different types of reports, there will be
another sub folder for each report type named {report_type}_reports. In {report_type}_reports folder, there is a set of
folders that are the same for each report type:

- **baselines**:
    - {report_type}_reports:
        - put all your human encoded baselines here (if you plan to train the pipeline). Your baselines must be in csv
          format.
- **input**:
    - {report_type}_reports:
        - put all your reports in the {report_type}_reports folder. All your reports must be numbered from an integer to
          another integer.
        - You should try your best to make sure the numbering of the reports are close to being consecutive.
        - It is okay to have gaps in the numbers (as shown in the folder structure above). Each report must have the
          same file ending.
        - Your reports must be in pdf format.
- **output**:
    - {report_type}_reports:
        - All the pipeline's output such as raw extractions and encoded extractions will go here. The sub folders will
          be automatically generated in the {report_type}_results folder.
- **utils**:
    - {report_type}_reports:
        - {report_type}_code_book.ods: values and their encodings
        - {report_type}_column_mappings.csv: the features of interests and the column in the report and the column in which the value should be recorded 
        - {report_type}_excluded_autocorrect_column_pairs.data (used mainly in gui): in the GUI you can select what texts should not be autocorrected,
        - {report_type}_regex_rules.csv: the rules pertaining to each feature of interest to be extracted (more on this in regex generation function)
        - any other types of files needed for the pipeline to run

## The code book, column mappings and excluded autocorrect column pairs:

### code book:
**col**|**num**|**value**
:-----:|:-----:|:-----:
Laterality|1|left
Laterality|2|right
Laterality|3|bilateral

### column mappings:
**pdf_col**|**alternative**|**col_to_collect**|**zero_empty**
:-----:|:-----:|:-----:|:-----:
study #| |Study #|false
laterality| |Laterality|false
"indication for surgury,indication"| |Surgical Indication|false
preoperative biopsy| |Pre-Operative Biopsy|false
"preoperative diagnosis (pathology),preoperative diagnosis"| |Pre-Operative Diagnosis|false
neoadjuvant treatment?| |Neoadjuvant Treatment|false
"incision and its relation to tumour,incision in relation to tumor"|"Additional notes on breast procedure (narrative),Additional notes on breast procedure"|Breast Incision Type|false



### excluded autocorrect column pairs:

# Instantiating the pipeline

You must create an EMRPipeline object first.

```python
from pipeline.utils.report_type import ReportType
from pipeline.emr_pipeline import EMRPipeline

pipeline = EMRPipeline(
    start=1,
    end=10,
    report_name="name",
    report_ending="report.pdf",
    report_type=ReportType.NUMERICAL)
```

# Running the pipeline

This pipeline can be fully customized through the use of functions. There are three types of functions you can make.

## extraction_tools

These functions deal with how the pipeline should extract FoI, either based on other parts of the report of other FoI.

```python

```

## autocorrect_tools

After a value has been extracted, you might want to clean it a special type of way.

```python

```

## encoding_tools

Sometimes you may want a value to be encoded a certain way. This can include using regex to clean a value or some kind
of different encoding method.

```python

```

# regex generation function

This pipeline's coolest and probably most confusing feature is the regular pattern (regex) generation algorithm. Since
the synoptic section is highly structured, we decided to use regular patterns to extract information. However, since
each report has different columns, a unique regular pattern would need to be used for each type of report. Thus, we have
a regex generation algorithm.

## The regex rules (NEW)
There will be a csv that looks like this:


### add {}

### capture up to {}

### val on {}

# Training the pipeline

You can train parts of the pipeline. The encoding portion and the extraction portion.

## Training the encoding

## Training the extraction (NEW)


