import time

from pipeline.emr_pipeline import run_pipeline
from pipeline.util.report_type import ReportType

# run_pipeline(start=101, end=156, skip=[140], report_type=ReportType.NUMERICAL)

run_pipeline(start=1, end=48, skip=[22, 43], report_type=ReportType.TEXT)
