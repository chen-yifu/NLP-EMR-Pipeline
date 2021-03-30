from typing import List, Dict
from pipeline.util.column import Column
from pipeline.util.report import Report
from pipeline.util.value import Value


def turn_extractions_to_values_single(extractions: Dict[str, str], column_mappings: Dict[str, Column], lat: str,
                                      report_id: str) -> Dict[str, Value]:
    value_extractions = {}
    # laterality
    for human_col_key, col in column_mappings.items():
        a_val = Value("")
        # match the primary value
        for primary_col in col.primary_report_col:
            if primary_col in extractions:
                a_val.primary_value = extractions[primary_col]
        # match the alternative value
        for alternative_col in col.alternative_report_col:
            if alternative_col in extractions:
                a_val.alternative_value.append(extractions[alternative_col])
        value_extractions[human_col_key] = a_val
    value_extractions["Laterality"] = Value(lat)
    return value_extractions


def turn_reports_extractions_to_values(reports: List[Report], column_mappings: Dict[str, Column]) -> List[Report]:
    result = []
    for report in reports:
        report.extractions = turn_extractions_to_values_single(report.extractions, column_mappings, report.laterality,
                                                               report.report_id)
        result.append(report)
    return result
