import re
from typing import Dict, List


def duplicate_lymph_nodes(report: str, result: dict, generic_pairs: dict):
    if (result["number of lymph nodes examined"] != ""):
        result["number of lymph nodes examined (sentinel and nonsentinel)"] = result["number of lymph nodes examined"]
        del result["number of lymph nodes examined"]


def find_num_foci(report: str, result: dict, generic_pairs: dict):
    if result["number of foci"] == "":
        result["number of foci"] = result["tumour focality"]


def in_situ(report: str, result: dict, generic_pairs: dict):
    if result["histologic type"].lower() == "ductal carcinoma in situ":
        # if in situ type is not found, use histologic type
        if result["in situ component type"] == "":
            result["in situ component type"] = result["histologic type"]
        # if in situ component is not found, use histologic type
        if result["in situ component"] == "":
            result["in situ component"] = result["histologic type"]


def no_lymph_node(report: str, result: dict, generic_pairs: dict):
    spaceless_synoptic_report = report.replace(" ", "")
    if "Nolymphnodespresent" in spaceless_synoptic_report:
        result["number of lymph nodes examined (sentinel and nonsentinel)"] = "0"
        result["number of sentinel nodes examined"] = "0"
        result["micro / macro metastasis"] = None
        result["number of lymph nodes with micrometastases"] = None
        result["number of lymph nodes with macrometastases"] = None
        result["size of largest metastatic deposit"] = None


def no_dcis_extent(report: str, result: dict, generic_pairs: dict):
    if "dcis extent" not in result.keys() and "dcis extent" not in generic_pairs.keys():
        try:
            result["dcis extent"] = generic_pairs["dcis estimated size"]
        except:
            pass


def negative_for_dcis(report: str, result: dict, generic_pairs: dict):
    cleaned_report = report.lower().strip()
    match1 = re.search(r"(?i)- *N *e *g *a *t *i *v *e  *f *o *r  *D *C *I *S", cleaned_report)

    if match1:
        result["distance from closest margin"] = None
        result["closest margin"] = None
        try:
            result["distance of dcis from closest margin"] = generic_pairs["distance from closest margin"]
        except KeyError:
            pass
        try:
            result["closest margin1"] = generic_pairs["closest margin"]
        except KeyError:
            pass
