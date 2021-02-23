import pickle
import pandas as pd

from pipeline.util import utils


def get_zero_empty_columns():
    # for these columns, "0" and "None" mean the same thing
    zero_empty_columns = ['Tumour Size (mm)',
                          'Closest Margin',
                          'Distance of DCIS from Closest Margin (mm)',
                          'Closest Margin DCIS',
                          'Total LN Examined',
                          '# Sentinel LN Examined',
                          '# LN w/ Micrometastasis',
                          '# LN w/ Macrometastasis',
                          'Size of Largest Macrometastasis Deposit',
                          'Extent (mm)',
                          'InvasiveTumourSize (mm)',
                          '# Sentinel Nodes Examined',
                          '# Micrometastatic Nodes',
                          '# Macrometastatic Nodes',
                          "Tumour Site"]
    return zero_empty_columns


def load_excluded_columns_as_df(pickle_path):
    """
    Load a list of excluded columns from pickle file
    :return:        pandas DataFrame;            columns to be excluded
    """
    try:
        with open(pickle_path, 'rb') as filehandle:
            # read the data as binary data stream
            excl_list = pickle.load(filehandle)
            data = {"Original": [tupl[0] for tupl in excl_list], "Corrected": [tupl[1] for tupl in excl_list]}
            df = pd.DataFrame(data, columns=['Original', 'Corrected'])
            return df
    except:
        s = "Loading excluded column pairs as dataframe" \
            "\nDid not find a list of excluded column pairs, please ensure it is a Pickle file at {}".format(
            pickle_path)
        excl_df = pd.DataFrame()
        return excl_df


def load_excluded_columns_as_list(pickle_path):
    """
    Load a list of excluded columns from pickle file
    :return:        list of str;            columns to be excluded
    """
    try:
        with open(pickle_path, 'rb') as filehandle:
            # read the data as binary data stream
            excl_list = pickle.load(filehandle)
    except:
        s = "Loading excluded column pairs as list" \
            "\nDid not find a list of excluded column pairs, please ensure it is a Pickle file at {}".format(
            pickle_path)
        print(s)
        excl_list = []
    return excl_list


def save_excluded_columns(list_of_cols,
                          path="pathology_pipeline/processing/excluded_autocorrect_column_pairs.data"):
    """
    Given a list of columns, save the excluded columns to a pickle file locally
    :param list_of_cols:        list of str;        list of columns to be excluded
    :return:                    str;                path to the file
    """
    path = utils.get_full_path(path)
    with open(path, 'wb') as f:
        pickle.dump(list_of_cols, f)
