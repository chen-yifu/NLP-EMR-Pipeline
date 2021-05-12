from typing import List, Dict
from pipeline.utils.column import Column, table
from pipeline.utils.report import Report
from pipeline.utils.value import Value


def turn_extractions_to_values_single(extractions: Dict[str, str], column_mappings: Dict[str, Column],
                                      acronyms: List[str]) -> Dict[str, Value]:
    """
    Turns string extractions into Value objects for a single report.

    :param extractions:     the extracted values and their respective columns
    :param column_mappings: human columns and their respective report columns
    :return:                single report with Value objects in extractions
    """
    acronyms_lowercased = [a.lower() for a in acronyms]

    def find_replace_acronyms(val: str):
        """
        :param val:
        :return:
        """
        if not val:
            val = ""
        val_to_return = []
        for word in val.split():
            found = False
            for index, acyn in enumerate(acronyms_lowercased):
                if word.lower() == acyn.lower():
                    val_to_return.append(acronyms[index])
                    found = True
                    break
            if not found:
                val_to_return.append(word)
        return " ".join(val_to_return)

    value_extractions = {}
    for human_col_key, col in column_mappings.items():
        a_val = Value("")
        # match the primary value
        for primary_col in col.cleaned_primary_report_col:
            if primary_col in extractions:
                extracted = extractions[primary_col]
                if extracted != "":
                    a_val.primary_value = find_replace_acronyms(extracted)
        # match the alternative value
        for alternative_col in col.cleaned_alternative_report_col:
            if alternative_col in extractions:
                extracted = extractions[alternative_col]
                if extracted != "":
                    a_val.alternative_value.append(find_replace_acronyms(extracted))
        value_extractions[human_col_key] = a_val
    return value_extractions


def turn_reports_extractions_to_values(reports: List[Report], column_mappings: Dict[str, Column],
                                       acronyms: List[str]) -> List[Report]:
    """
    Outer function that takes all reports and turns their string extractions into Value objects
    :param reports:          all the reports with extractions
    :param column_mappings:  human columns and their respective report columns
    :return:                 reports with Values objects
    """
    result = []
    for report in reports:
        report.extractions = turn_extractions_to_values_single(report.extractions, column_mappings, acronyms)
        result.append(report)
    return result
