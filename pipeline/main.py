from typing import List

from pipeline.check_report import *
from pipeline.operative_pipeline.operative_pipeline import run_operative_pipeline
from pipeline.pathology_pipeline.pathology_pipeline import run_pathology_pipeline


def run_pipeline(start: int, end: int, skip: List[int]):
    """
    :param start:
    :param end:
    :param skip:
    """
    if is_pathologic():
        run_pathology_pipeline(start=start, end=end, skip=skip)
    elif is_operative():
        run_operative_pipeline(start=start, end=end, skip=skip)
    else:
        print("The report is not pathologic or operative.")


# run below for operative pipeline
run_pipeline(start=1, end=48, skip=[22, 43])

# run below for pathology pipeline
# run_pipeline(101, 156, skip=[])
