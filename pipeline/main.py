import time

from pipeline.emr_pipeline import run_pipeline
from pipeline.util.report_type import ReportType
from pipeline.operative_pipeline.operative_pipeline import run_operative_pipeline
from pipeline.pathology_pipeline.pathology_pipeline import run_pathology_pipeline

# def run_working_pipeline():
#     start = time.time()
#     run_operative_pipeline(start=1, end=48, skip=[22, 43])
#     end = time.time()
#     op = end - start
#     start = time.time()
#     run_pathology_pipeline(101, 156, skip=[140])
#     end = time.time()
#     pathology = end - start
#
#     print("Pathology Time: {}".format(pathology))
#     print("Operative Time: {}".format(op))
#
#
# run_working_pipeline()


run_pipeline(start=1, end=48, skip=[22, 43], report_type=ReportType.OPERATIVE)

run_pipeline(start=101, end=156, skip=[140], report_type=ReportType.PATHOLOGY)
