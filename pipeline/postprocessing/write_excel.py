from collections import defaultdict

import pandas as pd


def save_dictionaries_into_csv_raw(dictionaries, column_mapping, csv_path, print_debug=True):
    """
    given a list of dictionaries, keeping only the targeted columns in column_mapping, save them to a csv file
    i.e., even if we extracted other columns, if it's not a target column, we don't keep it
    :param dictionaries:                a list of dict;             each element is a dictionary that is a row in dataframe
    :param column_mapping:      a list of (str, str);   first str is col name from PDF, second str is col from Excel
    :param csv_path:            str;                        path to output csv
    :param print_debug:         boolean;                    print debug statements and resulting dataframe if True
    :return:                    dataframe;                  resulting dataframe that has been saved
    """
    pdf_columns = [col_pdf for col_pdf, col_csv in column_mapping]
    csv_columns = [col_csv for col_pdf, col_csv in column_mapping]
    pd.options.mode.chained_assignment = None  # default="warn"
    pd.options.display.width = 0

    # remove unneeded column-value pairs
    for dictionary in dictionaries:
        keys = list(dictionary.keys())
        for k in keys:
            if k not in pdf_columns:       # if a col-val pair in dictionary is not useful
                del dictionary[k]          # don't include it in final csv

    # rename the column names
    renamed_dictionaries = []
    for dictionary in dictionaries:
        renamed_dictionary = defaultdict(str)
        for index, col in enumerate(pdf_columns):
            if renamed_dictionary[col] == "":
                val = dictionary[col]
                renamed_dictionary[csv_columns[index]] = val
        renamed_dictionaries.append(renamed_dictionary)

    # keep only unique csv column names (e.g. we have a duplicate "Histologic Grade", if keep both, will cause "ValueError: cannot reindex from a duplicate axis")
    unique_cols = []
    [unique_cols.append(col) for col in csv_columns if col not in unique_cols]
    print([(d["Study #"], d["Histologic Grade"]) for d in renamed_dictionaries])
    df = pd.DataFrame(renamed_dictionaries, columns=unique_cols)

    df.to_csv(csv_path, index=False)

    if print_debug:
        s = df.loc[:].to_string()
        print(s)
        s = "\nDone saving the results to {}\n".format(csv_path)

    return df
