from typing import Dict, List

import pandas as pd

from pipeline.utils.column import Column
from pipeline.utils.report import Report


def save_dictionaries_into_csv_raw(reports: List[Report], column_mapping: Dict[str, Column], csv_path: str,
                                   print_debug=True) -> pd.DataFrame:
    """
    given a list of reports, keeping only the targeted columns in column_mapping, save them to a csv file
    i.e., even if we extracted other columns, if it's not a target column, we don't keep it
    :param reports:
    :param column_mapping:
    :param csv_path:                                     path to output csv
    :param print_debug:                                  print debug statements and resulting dataframe if True
    """

    report_cols = []
    human_cols = []
    for human_col, report_col in column_mapping.items():
        human_cols.append(human_col)
        report_cols += report_col.primary_report_col
        report_cols += report_col.alternative_report_col

    pd.options.mode.chained_assignment = None  # default="warn"
    pd.options.display.width = 0

    to_encode = []
    for report in reports:
        to_encode_dict = {}
        for col, extract in report.extractions.items():
            to_encode_dict[col] = extract.primary_value + str(
                extract.alternative_value) if extract.alternative_value != [] else extract.primary_value
        to_encode_dict.update({"Study #": report.report_id})
        to_encode.append(to_encode_dict)

    unique_cols = []
    [unique_cols.append(col) for col in human_cols if col not in unique_cols]
    df = pd.DataFrame(to_encode, columns=unique_cols)

    df.to_csv(csv_path, index=False)

    if print_debug:
        s = df.loc[:].to_string()
        print(s)
        s = "\nDone saving the results to {}\n".format(csv_path)

    return df
