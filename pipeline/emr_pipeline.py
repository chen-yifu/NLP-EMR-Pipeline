import time
from pipeline.operative_pipeline.operative_pipeline import run_operative_pipeline
from pipeline.pathology_pipeline.pathology_pipeline import run_pathology_pipeline


def run_pipeline():
    """
    start: int, end: int, skip: List[int]

    :param start:
    :param end:
    :param skip:
    """
    start = time.time()
    run_operative_pipeline(start=1, end=48, skip=[22, 43])
    end = time.time()
    op = end - start
    start = time.time()
    run_pathology_pipeline(101, 156, skip=[140])
    end = time.time()
    pathology = end - start

    print("Pathology Time: {}".format(pathology))
    print("Operative Time: {}".format(op))
