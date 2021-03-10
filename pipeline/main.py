import time

from pipeline.emr_pipeline import run_pipeline
from pipeline.operative_pipeline.processing.extract_extractions import clean_up_str
from pipeline.util.regex_tools import export_pathology_synoptic_regex
from pipeline.util.report_type import ReportType
from pipeline.operative_pipeline.operative_pipeline import run_operative_pipeline
from pipeline.pathology_pipeline.pathology_pipeline import run_pathology_pipeline

run_pipeline(start=101, end=156, skip=[140], report_type=ReportType.NUMERICAL)

# run_pipeline(start=1, end=48, skip=[22, 43], report_type=ReportType.TEXT)
