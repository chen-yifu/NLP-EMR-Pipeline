import pickle
import pandas as pd

from pipeline.util import utils


def get_column_mappings():
    """
    :return: a list of tuples ;     mapping of PDF to Excel
    """
    # each element in the list is a tuple of (pdf_col, excel_col)
    # pdf_col is the column name from PDF reports
    # excel_col is the column name from NLP Data Collection Excel sheet
    # this will help map the extracted data onto Excel sheet
    # FIXME this needs to be double-checked     - (Yifu, Jan 3 2021)
    column_mappings = [
        ("study_id", "Study #"),
        # BREAST LESION PATHOLOGIC DIAGNOSIS
        ("invasive carcinoma", "Invasive Carcinoma"),
        ("histologic type", "Invasive Histologic Type"),
        ("glandular (acinar) / tubular differentiation", "Glandular Differentiation"),
        ("nuclear pleomorphism", "Nuclear Pleomorphism"),
        ("mitotic rate", "Mitotic Rate"),
        ("fd histologic grade", "Histologic Grade"),
        ("overall nottingham score", "Histologic Grade"),
        # in synoptic reports, "overall nottingham score" == "histologic grade"; in final diagnosis, we calculate histologic grade manually from nottingham score
        ("tumour size", "Tumour Size (mm)"),  # "\w*(\d\d)\s*(?:mm|millimeters)\w*",
        ("tumour focality", "Tumour Focality"),
        ("number of foci", "# of Foci"),
        ("tumour site", "Tumour Site"),
        ("lymphovascular invasion", "Lymphovascular Invasion"),
        ("in situ component", "Insitu Component"),
        ("in situ component type", "Insitu Type"),
        ("nuclear grade", "Insitu Nuclear Grade"),
        ("necrosis", "Necrosis"),
        ("dcis extent", "DCIS Extent"),
        ("architectural patterns", "Archtectural Patterns"),

        # MARGINS (INVASIVE)
        ("invasive carcinoma margins", "InvasiveCarcinoma Margins"),
        ("distance from closest margin", "Distance from Closest Margin"),
        ("closest margin", "Closest Margin"),

        # MARGINS (IN SITU)
        ("dcis margins", "DCIS Margins"),
        ("distance of dcis from closest margin", "Distance of DCIS from Closest Margin (mm)"),  # TODO check this
        ("closest margin", "Closest Margin DCIS"),
        # TODO Closest Margin DCIS

        # LYMPH NODES
        # TODO missing distance from closest margin
        ("number of lymph nodes examined (sentinel and nonsentinel)", "Total LN Examined"),
        ("number of sentinel nodes examined", "# Sentinel LN Examined"),
        ("micro / macro metastasis", "Micro/macro metastasis"),
        ("number of lymph nodes with micrometastases", "# LN w/ Micrometastasis"),  # TODO exclude from distance
        ("number of lymph nodes with macrometastases", "# LN w/ Macrometastasis"),  # TODO exclude from distance
        ("size of largest metastatic deposit", "Size of Largest Macrometastasis Deposit"),
        ("extranodal extension", "Extranodal Extension"),
        ("extent", "Extent (mm)"),  # Lymph node extent # TODO find word flag

        # PATHOLOGIC STAGING
        ("tumour size", "InvasiveTumourSize (mm)"),
        ("number of sentinel nodes examined", "# Sentinel Nodes Examined"),
        ("number of lymph nodes with micrometastases", "# Micrometastatic Nodes"),  # TODO exclude from distance
        ("number of lymph nodes with macrometastases", "# Macrometastatic Nodes"),  # TODO exclude from distance
        ("pathologic stage", "Pathologic Stage")
    ]
    return column_mappings


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


def load_excluded_columns_as_df(path="pathology_pipeline/processing/excluded_autocorrect_column_pairs.data"):
    """
    Load a list of excluded columns from pickle file
    :return:        pandas DataFrame;            columns to be excluded
    """
    path = utils.get_full_path(path)
    try:
        with open(path, 'rb') as filehandle:
            # read the data as binary data stream
            excl_list = pickle.load(filehandle)
            data = {"Original": [tupl[0] for tupl in excl_list], "Corrected": [tupl[1] for tupl in excl_list]}
            df = pd.DataFrame(data, columns=['Original', 'Corrected'])
            return df
    except:
        s = "Loading excluded column pairs as dataframe" \
            "\nDid not find a list of excluded column pairs, please ensure it is a Pickle file at {}".format(path)
        excl_df = pd.DataFrame()
        return excl_df


def load_excluded_columns_as_list(path="pathology_pipeline/processing/excluded_autocorrect_column_pairs.data"):
    """
    Load a list of excluded columns from pickle file
    :return:        list of str;            columns to be excluded
    """
    path = utils.get_full_path(path)
    try:
        with open(path, 'rb') as filehandle:
            # read the data as binary data stream
            excl_list = pickle.load(filehandle)
    except:
        s = "Loading excluded column pairs as list" \
            "\nDid not find a list of excluded column pairs, please ensure it is a Pickle file at {}".format(path)
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
