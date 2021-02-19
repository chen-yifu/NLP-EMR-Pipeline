import re

from nltk import edit_distance


def encode_extractions_to_dataframe(df, print_debug=True):
    """
    given a dataframe, convert the values according to the code book
    :param df:           pandas dataframe;               data for all pdf reports, extracted column-value pairs
    :param print_debug:         boolean;                        print debug statements in Terminal if True
    :return:                    pandas dataframe;               data for all pdf reports, coded according to code book
    """

    # TODO return 0
    # TODO implement number of foci
    # TODO implement tumour site?
    # TODO infer in situ type from histologic type?
    # TODO distance_dcis_closest_margin check for Final diagnosis (e.g. ID 105)

    def invasive_carcinoma(value):
        """
        0=Absent 1=Present
        :param value:           str;            unprocessed data
        :return:                str;            codified data
        """
        value = str(value).lower().replace(" ", "")
        if value == None or value == "":
            return ""
        if "present" in value:
            return "1"
        else:
            return "0"

    def invasive_histologic_type(invasive_carcinoma_value, invasive_hist_tpe):
        """
        0=N/A 1=Lobular 2=Ductal 3=Mucinous 4=Tubular 5=Micro-invasive carcinoma 6=Other
        :return:                str;            codified data
        """
        if invasive_carcinoma_value == ("0" or "" or None or "nan"):
            return ""

        value = str(invasive_hist_tpe).lower().replace(" ", "")
        if "lobular" in value:
            return "1"
        elif "ductal" in value:
            return "2"
        elif "mucinous" in value:
            return "3"
        elif "tubular" in value:
            return "4"
        elif "micro" in value:
            return "5"
        elif "other" in value:
            return "6"

    def glandular_nuclear_mitotic(value):
        """
        0=N/A 1=1 2=2 3=3
        :param value:           str;            unprocessed data
        :return:                str;            codified data
        """
        value = str(value).lower().replace(" ", "")
        if "1" in value:
            return 1
        elif "2" in value:
            return 2
        elif "3" in value:
            return 3
        else:
            return None

    def histologic_grade(value):
        """
        0=N/A 1=I 2=II 3=III
        - If Nottingham Score is 3-5 --> Histologic grade 1
        - If Nottingham Score is 6-7 --> Histologic grade 2
        - If Nottingham Score is 8-9 --> Histologic grade 3
        :param value:           str;            unprocessed data
        :return:                str;            codified data
        """
        value = str(value).lower().replace(" ", "")
        if "1" in value:
            return "1"
        elif "2" in value:
            return "2"
        elif "3" in value:
            return "3"
        # if this pdf doesn't have synoptic report, we use the final diagnosis' nottingham score, which is range 3-9, to convert to this
        elif value in ["3", "4", "5"]:
            return "1"
        elif value in ["6", "7"]:
            return "2"
        elif value in ["8", "9"]:
            return "3"

    def tumour_size(value):
        """
        mm
        :param value:           str;            unprocessed data
        :return:                str;            codified data
        """
        value = str(value).lower().replace(" ", "")
        # regex demo: https://regex101.com/r/FkMTtr/1
        regex = re.compile(r"([\<\>]? ?\d+\.?\d*)")
        matches = re.findall(regex, value)
        if matches:
            return matches[0]

    def tumour_focality(value):
        """
        0=N/A 1=Single 2=Multifocal
        :param value:           str;            unprocessed data
        :return:                str;            codified data
        """
        value = str(value).lower().replace(" ", "")
        if "single" in value:
            return "1"
        elif "multi" in value:
            return "2"

    def number_of_foci(focality, num_foci):
        """
        0=not specified #=#
        :param focality:        str;            tumour focality
        :param num_foci:        str;            # of foci
        :return:                str;            codified data
        """
        if focality == "1":
            return "1"
        raw = str(num_foci)
        value = str(num_foci).lower().replace(" ", "")
        regex = re.compile(r"(\d+)")
        matches = re.findall(regex, value)
        if "single" in value:
            return "1"
        elif matches:
            return matches[0]
        elif "cannotbedetermined" in value:
            return "cannot be determined"



    def tumour_site(value):
        """
        clock orientation
        :param value:           str;            unprocessed data
        :return:                str;            codified data
        """
        value_copy = str(value)
        value = str(value).lower().replace(" ", "")
        # if "mm" is in value, the correct column is tumour size, not tumour site
        if "mm" in value:
            return ""
        regex_full = re.compile(r"(\d+:\d+)")  # 12:00
        regex_part = re.compile(r"(\d+)")      # 12 o' clock
        matches_full = re.findall(regex_full, value)
        matches_part = re.findall(regex_part, value)
        if matches_full:
            if len(matches_full[0]) == 4:
                value = "0" + matches_full[0]
            else:
                value = matches_full[0]
        elif matches_part:
            if len(matches_part[0]) == 1:
                value = "0" + str(matches_part[0]) + ":00"
            elif len(matches_part[0]) >= 2:
                value = str(matches_part[0]) + ":00"
                if int(matches_part[0]) > 12:
                    value = ""
        else:
            value = value_copy

        return value

    def lymphovascular_invasion(value):
        """
        0=Absent 1=Present 2=Cannot be determined
        :param value:           str;            unprocessed data
        :return:                str;            codified data
        """
        value = str(value).lower().replace(" ", "")
        if "present" in value:
            return "1"
        elif edit_distance(value, "notidentified") <= 1:
            return ""
        else:
            return ""

    def insitu_component(value):
        """
        0=Absent 1=Present
        :param value:           str;            unprocessed data
        :return:                str;            codified data
        """
        value = str(value).lower().replace(" ", "")
        substring_list = ["present", "lobul", "duct", "dcis", "lcis", "ocis", "invasive"]
        if any(substring in value for substring in substring_list):
            return "1"
        elif "none" in value:
            return ""
        elif edit_distance(value, "notidentified") <= 1:
            return "0"
        else:
            return ""

    def insitu_type(value):
        """
        0=N/A 1=Lobular 2=Ductal 3=Lobular and ductal 4=Other (Specify)
        :param value:           str;            unprocessed data
        :return:                str;            codified data
        """
        raw_value = value
        value = str(value).lower().replace(" ", "")
        if ("lobular" in value and "ductal" in value) or ("lcis" in value and "dcis" in value):
            return "3"
        elif "lcis" in value or "lobul" in value:
            return "1"
        elif "dcis" in value or "duct" in value:
            return "2"
        elif len(value) > 3:
            return str(raw_value)
        else:
            return "0"

    def insitu_nuclear_grade(value):
        """
        0=N/A 1=I 2=II 3=III
        :param value:           str;            unprocessed data
        :return:                str;            codified data
        """
        value = str(value).lower().replace(" ", "")
        if "low" in value:
            return "1"
        elif "inter" in value:
            return "2"
        elif "high" in value:
            return "3"

    def archtectural_patterns(value):
        """
        :param value:           str;            unprocessed data
        :return:                str;            codified data
        """
        value = str(value)
        regex = re.compile(r" {2,}")
        value = re.sub(regex, " ", value)
        if value != "nan":
            return value
        else:
            return ""

    def invasive_carcinoma_margins(value):
        """
        0=negative 1=positive 2=Can't be assessed
        :param value:           str;            unprocessed data
        :return:                str;            codified data
        """
        value = str(value).lower().replace(" ", "")
        if "negative" in value:
            return "0"
        elif "positive" in value:
            return "1"
        elif value == "notfoundfromfinaldiagnosis":
            return ""
        else:
            return "2"

    def distance_from_closest_margin(value):
        """
        mm
        :param value:           str;            unprocessed data
        :return:                str;            codified data
        """
        value = str(value).lower().replace(" ", "")
        # regex demo: https://regex101.com/r/FkMTtr/1
        regex = re.compile(r"([\<\>]? ?\d+\.?\d*)")
        matches = re.findall(regex, value)
        if matches:
            return matches[0]


    def closest_margin(value):
        """
        0=N/A 1=Posterior 2=Anterior 3=Lateral 4=Medial 5=Anterior and posterior 6=Inferior 7=Superior 8=Other (Specify)
        :param value_:           str;            unprocessed data
        :return:                str;            codified data
        """
        value_ = str(value).lower().replace(" ", "")
        if "anterior" in value_ and "posterior" in value_:
            return "5"
        elif "posterior" in value_:
            return "1"
        elif "anterior" in value_:
            return "2"
        elif "lateral" in value_:
            return "3"
        elif "medial" in value_:
            return "4"
        elif "inferior" in value_:
            return "6"
        elif "superior" in value_:
            return "7"
        elif len(value_) > 3:
            return str(value)

    def dcis_margins(value):
        """
        0=negative 1=positive
        :param value:           str;            unprocessed data
        :return:                str;            codified data
        """
        value = str(value).lower().replace(" ", "")
        if "invasivecarcinoma" in value:
            return ""   # the DCIS Margin data is missing and we wrongly extracted Invasive Carcinoma Margins instead
        if "negative" in value:
            return "0"
        elif "positive" in value:
            return "1"

    def distance_dcis_closest_margin(value):

        """
        mm
        :param value:           str;            unprocessed data
        :return:                str;            codified data
        """
        space_regex = re.compile(" +")
        value = re.sub(space_regex, " ", str(value)).strip()
        # value = str(value).lower().replace(" ", "")
        # regex demo: https://regex101.com/r/FkMTtr/2
        regex = re.compile(r"([\<\>]? ?\d+\.?\d*)")
        matches = re.findall(regex, value)
        if matches:
            return matches[0]
        else:
            return value

    def closest_margin_dcis(value):
        """
        0=N/A 1=Posterior 2=Anterior 3=Lateral 4=Medial 5=Anterior and posterior 6=Inferior 7=Superior 8=Other (Specify)
        :param value_:           str;            unprocessed data
        :return:                str;            codified data
        """
        value_ = str(value).lower().replace(" ", "")
        if "anterior" in value_ and "posterior" in value_:
            return "5"
        elif "posterior" in value_:
            return "1"
        elif "anterior" in value_:
            return "2"
        elif "lateral" in value_:
            return "3"
        elif "medial" in value_:
            return "4"
        elif "inferior" in value_:
            return "6"
        elif "superior" in value_:
            return "7"
        elif len(value_) > 3:
            return str(value)

    def size_largest_macrometastasis_deposit(value):
        """
        mm
        :param value:           str;            unprocessed data
        :return:                str;            codified data
        """
        if value == None:
            return ""
        value = str(value).lower().replace(" ", "")
        # regex demo: https://regex101.com/r/FkMTtr/1
        regex = re.compile(r"([\<\>]? ?\d+\.?\d*)")
        matches = re.findall(regex, value)
        if matches:
            return matches[0]
        else:
            return ""

    def lymph_metasatsis(value):
        """
        # LN with micro/macro metastasis
        :param value:           str;            unprocessed data
        :return:                str;            codified data
        """
        value = str(value).lower().replace(" ", "")
        # regex demo: https://regex101.com/r/FkMTtr/1
        regex = re.compile(r"([\<\>]? ?\d+\.?\d*)")
        matches = re.findall(regex, value)
        if matches:
            return matches[0]
        else:
            return "0"

    def micro_macro_metastasis(value):
        """
        0=Absent 1=Present
        :param value:           str;            unprocessed data
        :return:                str;            codified data
        """
        value = str(value).lower().replace(" ", "")
        if "present" in value:
            return "1"
        elif edit_distance(value, "notidentified") <= 1:
            return "0"
        else:
            return ""

    def extranodal_extension(value):
        """
        0=Absent 1=Present
        :param value:           str;            unprocessed data
        :return:                str;            codified data
        """
        value = str(value).lower().replace(" ", "")
        if "present" in value:
            return "1"
        elif "notidentified" in value:
            return "0"
        else:
            return ""

    def extent(value):
        """
        mm
        :param value:           str;            unprocessed data
        :return:                str;            codified data
        """
        value = str(value).lower().replace(" ", "")
        # regex demo: https://regex101.com/r/FkMTtr/1
        regex = re.compile(r"([\<\>]? ?\d+\.?\d*)")
        matches = re.findall(regex, value)
        if matches:
            return matches[0]

    def invasive_tumour_size(value):
        """
        mm
        :param value:           str;            unprocessed data
        :return:                str;            codified data
        """
        value = str(value).lower().replace(" ", "")
        # regex demo: https://regex101.com/r/FkMTtr/1
        regex = re.compile(r"([\<\>]? ?\d+\.?\d*)")
        matches = re.findall(regex, value)
        if matches:
            return matches[0]
        elif "cannotbedetermined" in value:
            return "Cannot be determined"

    def micro_nodes(value):
        """
        # LN with micrometastasis
        :param value:           str;            unprocessed data
        :return:                str;            codified data
        """
        if value == None:
            return ""
        value = str(value).lower().replace(" ", "")
        # regex demo:
        regex = re.compile(r"([\<\>]? ?\d+\d*)")
        matches = re.findall(regex, value)
        if matches:
            return matches[0]
        else:
            return ""

    def macro_nodes(value):
        """
        # LN with macrometastasis
        :param value:           str;            unprocessed data
        :return:                str;            codified data
        """
        if value == None:
            return ""
        value = str(value).lower().replace(" ", "")
        # regex demo: https://regex101.com/r/FkMTtr/1
        regex = re.compile(r"([\<\>]? ?\d+\d*)")
        matches = re.findall(regex, value)
        if matches:
            return matches[0]
        else:
            return ""

    def resolve_cannot_be_determined(value):
        """
        if the cell contains word such as "cannot be determined", truncate the result to this
        :param value:
        :return:
        """
        value = str(value).lower().replace(" ", "")
        if "cannotbedetermined" in value:
            return "cannnot be determined"
        elif "cannotbeassessed" in value:
            return "cannnot be assessed"

    # make a copy of dataframe to save results
    result_df = df.copy()
    result_df["Invasive Carcinoma"] = df["Invasive Carcinoma"].apply(invasive_carcinoma)
    result_df["Invasive Histologic Type"] = result_df.apply(lambda x: invasive_histologic_type(x["Invasive Carcinoma"], x["Invasive Histologic Type"]), axis=1)
    result_df["Glandular Differentiation"] = df["Glandular Differentiation"].apply(glandular_nuclear_mitotic)
    result_df["Nuclear Pleomorphism"] = df["Nuclear Pleomorphism"].apply(glandular_nuclear_mitotic)
    result_df["Mitotic Rate"] = df["Mitotic Rate"].apply(glandular_nuclear_mitotic)
    # calculate "Nottingham Score" as the aggregation of "Glandular Diff.", "Nuclear Pleomorphism", and "Mitotic Rate"
    result_df.insert(result_df.columns.get_loc(
        "Glandular Differentiation"),
        "Nottingham Score",
        result_df["Glandular Differentiation"] + result_df["Nuclear Pleomorphism"] + result_df["Mitotic Rate"]
    )
    result_df["Histologic Grade"] = df["Histologic Grade"].apply(histologic_grade)
    result_df["Tumour Size (mm)"] = df["Tumour Size (mm)"].apply(tumour_size)
    result_df["Tumour Focality"] = df["Tumour Focality"].apply(tumour_focality)
    result_df["# of Foci"] = result_df.apply(lambda x: number_of_foci(x["Tumour Focality"], x["# of Foci"]), axis=1)
    result_df["Tumour Site"] = df["Tumour Site"].apply(tumour_site)
    result_df["Lymphovascular Invasion"] = df["Lymphovascular Invasion"].apply(lymphovascular_invasion)
    result_df["Insitu Component"] = df["Insitu Component"].apply(insitu_component)
    result_df["Insitu Type"] = df["Insitu Type"].apply(insitu_type)
    result_df["Insitu Nuclear Grade"] = df["Insitu Nuclear Grade"].apply(insitu_nuclear_grade)
    result_df["Archtectural Patterns"] = df["Archtectural Patterns"].apply(archtectural_patterns)
    result_df["InvasiveCarcinoma Margins"] = df["InvasiveCarcinoma Margins"].apply(invasive_carcinoma_margins)
    result_df["Distance from Closest Margin"] = df["Distance from Closest Margin"].apply(distance_from_closest_margin)
    result_df["Closest Margin"] = df["Closest Margin"].apply(closest_margin)
    result_df["DCIS Margins"] = df["DCIS Margins"].apply(dcis_margins)
    result_df["Distance of DCIS from Closest Margin (mm)"] = df["Distance of DCIS from Closest Margin (mm)"].apply(distance_dcis_closest_margin)
    result_df["Closest Margin DCIS"] = df["Closest Margin DCIS"].apply(closest_margin_dcis)
    result_df["# LN w/ Micrometastasis"] = df["# LN w/ Micrometastasis"].apply(micro_nodes)
    result_df["# LN w/ Macrometastasis"] = df["# LN w/ Macrometastasis"].apply(macro_nodes)
    result_df["Micro/macro metastasis"] = df["Micro/macro metastasis"].apply(micro_macro_metastasis)
    result_df["Size of Largest Macrometastasis Deposit"] = df["Size of Largest Macrometastasis Deposit"].apply(size_largest_macrometastasis_deposit)
    result_df["Extranodal Extension"] = df["Extranodal Extension"].apply(extranodal_extension)
    result_df["Extent (mm)"] = df["Extent (mm)"].apply(extent)
    result_df["InvasiveTumourSize (mm)"] = df["InvasiveTumourSize (mm)"].apply(invasive_tumour_size)
    result_df["# Micrometastatic Nodes"] = df["# Micrometastatic Nodes"].apply(micro_nodes)
    result_df["# Macrometastatic Nodes"] = df["# Macrometastatic Nodes"].apply(macro_nodes)
    # result_df.applymap(resolve_cannot_be_determined)

    if print_debug:
        print(result_df)

    return result_df

