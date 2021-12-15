# Automated Medical Chart Review for Breast Cancer Outcomes Research: A Novel Natural Language Processing Extraction System

To install dependencies, run
```
pip install -r requirements.txt
```


## For Windows:

*WSL2 is highly recommended. You can try out command prompt or powershell at your own risk. For development, I recommend
Pycharm Professional or VSCode, as these development environments allow you to set up a remote connection to WSL2.*

- For pytesseract: https://school.geekwall.in/p/9QG6NstS/
- For Tkinter: https://www.techinfected.net/2015/09/how-to-install-and-use-tkinter-in-ubuntu-debian-linux-mint.html
- For using WSL2 as your interpreter in Pycharm
  Professional: https://www.jetbrains.com/help/pycharm/using-wsl-as-a-remote-interpreter.html#configure-wsl
- For using VSCode and WSL: https://code.visualstudio.com/docs/remote/wsl-tutorial



# Sample usage

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
│           ├── {report_type}_thresholds.csv
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
        - {report_type}_column_mappings.csv: the features of interests and the column in the report and the column in
          which the value should be recorded
        - {report_type}_excluded_autocorrect_column_pairs.data (used mainly in gui): in the GUI you can select what
          texts should not be autocorrected,
        - {report_type}_regex_rules.csv: the rules pertaining to each feature of interest to be extracted (more on this
          in regex generation function)
        - any other types of files needed for the pipeline to run

## The code book, column mappings and excluded autocorrect column pairs:

### code book (.ods or .xlsx):

**col**|**num**|**value**
:-----:|:-----:|:-----:
Laterality|1|left
Laterality|2|right
Laterality|3|bilateral

- col: the name that you want the extracted value to be under in the excel sheet. Must match col_to_collect in column
  mappings.
- num: the integer encoding you want the value to be matched to. If you want to use a custom encoding function or just
  want the value to be returned, leave this as -1.
- value: the string value that should be encoded to 3. If num is -1, either put the function you want to use here or
  leave it blank if you just want the extracted value to be returned.

### column mappings (.csv):

![image](https://user-images.githubusercontent.com/55033656/119017166-f34af000-b957-11eb-87de-2a1011affc20.png)
![image](https://user-images.githubusercontent.com/55033656/119017270-11b0eb80-b958-11eb-8677-a03e6ef3c1de.png)

**pdf_col**|**alternative**|**col_to_collect**|**zero_empty**
:-----:|:-----:|:-----:|:-----:
study #| |Study #|false
laterality| |Laterality|false
"indication for surgury,indication"| |Surgical Indication|false
preoperative biopsy| |Pre-Operative Biopsy|false
"preoperative diagnosis (pathology),preoperative diagnosis"| |Pre-Operative Diagnosis|false
neoadjuvant treatment?| |Neoadjuvant Treatment|false
"incision and its relation to tumour,incision in relation to tumor"|"Additional notes on breast procedure (narrative),Additional notes on breast procedure"|Breast Incision Type|false

- pdf_col: the name of the feature of interest in the report
- alternative: if the feature of interest could be found in another column in the report, put it here
- col_to_collect: the name in which the extracted value should be put under (seen in the excel sheet)
- zero_empty: if None and 0 mean the same thing

### excluded autocorrect column pairs (.data):

In the GUI, you are able to select which autocorrections to exclude or add.

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
    report_type=ReportType.NUMERICAL,
    other_paths=["another_path.csv"])
```

# Running the pipeline

## Using new regular pattern rules

```python
# using the pipeline object created earlier
pipeline.run_pipeline(
    baseline_versions=["baseline.csv"],
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
```

## Using old regular pattern rules

```python
# using the pipeline object created earlier
pipeline.run_pipeline(
    sep_list=["invasive carcinoma", "in situ component", "in situ component type", "insitu component",
              "insitu type"],
    baseline_versions=["baseline.csv"],
    anchor=r"^ *-* *",
    add_anchor=True,
    val_on_next_line_cols_to_add=["SPECIMEN", "Treatment Effect", "Margins", "pathologic stage", "comment(s)",
                                  "Part(s) Involved:"],
    cols_to_skip=["study #", "specimen", "treatment effect", "margins", "pathologic stage", "comment(s)",
                  "part(s) involved", "nottingham score", "closest margin", "closest margin1"],
    encoding_tools={"nottingham_score": nottingham_score,
                    "process_mm_val": process_mm_val,
                    "number_of_foci": number_of_foci,
                    "tumour_site": tumour_site,
                    "archtectural_patterns": archtectural_patterns},
    autocorrect_tools={"pathologic stage": find_pathologic_stage},
    extraction_tools=[no_lymph_node, negative_for_dcis, no_dcis_extent, in_situ, duplicate_lymph_nodes,
                      find_num_foci])
```

# Customization

This pipeline can be fully customized through the use of functions. There are three types of functions you can make.

## extraction_tools

These functions deal with how the pipeline should extract FoI, either based on other parts of the report of other FoI.
Every function must follow this format:

```python
def extraction_function(report: str, result: dict, generic_pairs: dict):
    if "key" in generic_pairs.keys():
        result["another_key"] = generic_pairs["key"]

```

You don't have to use all three arguments, but they must all be present in the function.

## autocorrect_tools

After a value has been extracted, you might want to clean it a special type of way. Every function must follow this
format:

```python
def autocorrect_function(val: str, paths: Dict[str, str]) -> str:
    return clean_val(val)
```

## encoding_tools

Sometimes you may want a value to be encoded a certain way. This can include using regex to clean a value or some kind
of different encoding method. Every function must have this format:

```python
def encoding_function(value: str = "", encodings_so_far: Dict[str, str] = {}):
    if "col" in encodings_so_far.keys():
        return value + encodings_so_far["col"]
```

# Regex Generation Function

This pipeline's coolest and probably most confusing feature is the regular pattern (regex) generation algorithm. Since
the synoptic section is highly structured, we decided to use regular patterns to extract information. However, since
each report has different columns, a unique regular pattern would need to be used for each type of report. Thus, we have
a regex generation algorithm.

The algorithm utilizes a template:

```bash
{front_cap}(?P<var>{end_cap}
```

- front_cap: specifies rules for column you want to extract
- end_cap: specifies rules for the value you want to extract

## The regex rules (NEW)

There will be a csv that looks like this:
**col**|**val on same line**|**val on next line**|**add anchor**|**add separator to col name**|**capture to end of val**
|**capture up to line with separator**|**capture up to keyword**
:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:
Study #|TRUE|FALSE|TRUE|FALSE|FALSE|TRUE|FALSE Laterality|TRUE|FALSE|TRUE|FALSE|FALSE|TRUE|FALSE Surgical
Indication|TRUE|FALSE|TRUE|TRUE|FALSE|TRUE|FALSE Pre-Operative Biopsy|TRUE|FALSE|TRUE|FALSE|FALSE|TRUE|FALSE
Pre-Operative Diagnosis|TRUE|FALSE|TRUE|FALSE|FALSE|TRUE|FALSE Neoadjuvant
Treatment|TRUE|FALSE|FALSE|FALSE|TRUE|FALSE|FALSE

### capture {}

When you want to stop capturing the value. These regular patterns would be in the end cap. For instance:
```{front_cap}(?P<var>{end_cap}```

- up to but not including the line with a separator: ```{front_cap}(?P<var>((?!.+{sep}\?*)[\s\S])*)```
- up to a keyword: ```{front_cap}(?P<var>((?!{next_col})[\s\S])*)```
- up to the end of the same line as the column: ```{front_cap}(?P<var>.+)```

### add {}

If you want to add something the report column. These regular patterns would be in the front cap. For instance:
```{front_cap}(?P<var>{end_cap}```

- separator (https://regex101.com/r/OJxapt/1): ```col1:(?P<var>{end_cap}```
- anchor (https://regex101.com/r/IDwCHq/1): ```^\d*\.* *col1(?P<var>{end_cap}```

### val on {}

Whether the value is on the same line as the column or the next line. These regular patterns would be in the front
cap.For instance:
```{front_cap}(?P<var>{end_cap}```

- same line (https://regex101.com/r/BxtXNo/1): ```col3(?P<var>{end_cap}```
- next line (https://regex101.com/r/LZkuW9/1): ```col1\s*-*(?P<var>{end_cap}```

#### Example:

A regular pattern for a column named "Indication" that uses a separator, anchor, captures up to but not including the
line with a separator and is on the same line:
```^\d*\.* *Indication:(?P<var>((?!.+:\?*)[\s\S])*)``` -> see it in action here: https://regex101.com/r/mZw1ov/1

The mentioned rules above are the current ones in place. If you want to add more rules please feel free to!

# Training the pipeline

You can train parts of the pipeline; the encoding portion, and the extraction portion.

## Training the encoding

```python
# using the pipeline object created earlier
pipeline.run_pipeline(
    baseline_versions=["baseline.csv"],
    anchor=r"^ *-* *",
    cols_to_skip=["study #", "nottingham score", "closest margin", "closest margin1"],
    val_on_next_line_cols_to_add=["SPECIMEN", "Treatment Effect", "Margins", "comment(s)", "Part(s) Involved:"],
    encoding_tools={"nottingham_score": nottingham_score,
                    "process_mm_val": process_mm_val,
                    "number_of_foci": number_of_foci,
                    "tumour_site": tumour_site,
                    "archtectural_patterns": archtectural_patterns},
    autocorrect_tools={"pathologic stage": find_pathologic_stage},
    extraction_tools=[no_lymph_node, negative_for_dcis, no_dcis_extent, in_situ, duplicate_lymph_nodes, find_num_foci],
    train_thresholds=True,
    # add these three new arguments to train the encoding
    start_threshold=0.5,
    end_threshold=1,
    threshold_interval=.05)
```

## Training the extraction (NEW)

```python
# using the pipeline object created earlier
pipeline.run_pipeline(
    baseline_versions=["baseline.csv"],
    anchor=r"^ *-* *",
    cols_to_skip=["study #", "nottingham score", "closest margin", "closest margin1"],
    val_on_next_line_cols_to_add=["SPECIMEN", "Treatment Effect", "Margins", "comment(s)", "Part(s) Involved:"],
    encoding_tools={"nottingham_score": nottingham_score,
                    "process_mm_val": process_mm_val,
                    "number_of_foci": number_of_foci,
                    "tumour_site": tumour_site,
                    "archtectural_patterns": archtectural_patterns},
    autocorrect_tools={"pathologic stage": find_pathologic_stage},
    extraction_tools=[no_lymph_node, negative_for_dcis, no_dcis_extent, in_situ, duplicate_lymph_nodes, find_num_foci],
    # add this argument to train the regex
    train_regex=True)
```

## Additional Resources

The interactive notebook for visualizing the Biomedical Word Embeddings is available on Google Colab [here](https://colab.research.google.com/drive/1ciw-GdCKHgJ6PjXjkxAF65plH2CjYL5I?usp=sharing). From there, you may compare the quality of embeddings produced by SciSpacy and PubMed BERT

### Word embeddings produced by SciSpacy's en_core_sci_lg model

#### 3D PCA Plot
![SciSpacy word embeddings visualized](https://github.com/chen-yifu/EMR_pipeline/blob/f3048c75b99e35f3d5e8c770b3c817b8db665869/figures/Embeddings%20SciSpacy.gif)

#### 2D PCA Plot
![SciSpacy word embeddings visualized (2D)](https://github.com/chen-yifu/EMR_pipeline/blob/30bc738da656323d1ccdb565121be45112bef0e7/figures/Embeddings%20SciSpacy%202D.png)

### Word embeddings prouced by PubMedBERT

#### 3D PCA Plot
![PubMedBERT word embeddings visualized](https://github.com/chen-yifu/EMR_pipeline/blob/f3048c75b99e35f3d5e8c770b3c817b8db665869/figures/Embeddings%20PubMedBERT.gif)

#### 2D PCA Plot
![PubMedBERT word embeddings visualized (2D)](https://github.com/chen-yifu/EMR_pipeline/blob/30bc738da656323d1ccdb565121be45112bef0e7/figures/Embeddings%20PubMed%20BERT%202D.png)

### PCA Heatmap
The following heatmap shows the cosine similarity between the first word's (mastectomy) embedding with the other words' (codebook candidates) embeddings.
![Word embeddings visualized (heatmap)](https://github.com/chen-yifu/EMR_pipeline/blob/8ecec7524b79ba75c6d0272d4eb0c5929cf55529/figures/Embeddings%20Heatmap.png)

In our NLP pipeline implementation, we chose SciSpacy's word embedding model over PubMedBERT, because the former seems to perform better at embedding single tokens. Theoretically, the inferior performance of the latter can be explained by the lack of sentence-level contexts that BERT usually sees during pre-training.

# Contact:

Lucy: lhao03[at]student.ubc.ca
Yifu: yifuch01[at]student.ubc.ca

# Reference:

Preprint: https://www.medrxiv.org/content/10.1101/2021.05.04.21256134v1
