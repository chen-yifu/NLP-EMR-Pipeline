from typing import List, Tuple
import string

from nltk import edit_distance

from pipeline.util import import_tools
from pipeline.util.report import Report


def code_extractions(reports: List[Report], substitution_cost: int, largest_cost: int, code_book: dict,
                     path_to_weights: str = "data/outputs/training_metrics/params/tuning.csv"):
    """
    :param code_book:
    :param path_to_weights:
    :param largest_cost:
    :param substitution_cost:
    :param reports:
    :return:
    """
    tuning_weights = import_tools.import_weights(path_to_weights=path_to_weights)

    def code_report(single_report: Report) -> dict:
        """
        :param single_report:
        :return:
        """
        extracted = single_report.extractions

        encoded_dict = {}

        for human_col, dict_vals_to_code in code_book.items():
            sub_cost = tuning_weights[human_col].sub_cost if human_col in tuning_weights else substitution_cost
            large_cost = tuning_weights[human_col].large_cost if human_col in tuning_weights else largest_cost
            table = str.maketrans(dict.fromkeys(string.punctuation))

            def try_encode(raw_str: str) -> Tuple[bool, str]:
                """
                :param raw_str:
                :return:
                """
                encode_dict = code_book[human_col]
                for val, val_code in encode_dict.items():
                    cleaned_val = str(val).lower().strip().translate(table)
                    cleaned_raw = str(raw_str).lower().strip().translate(table)
                    if edit_distance(cleaned_raw, cleaned_val, substitution_cost=sub_cost) < large_cost:
                        return True, val_code
                    elif cleaned_val == "no" or cleaned_val == "none":
                        if cleaned_val in cleaned_raw.split():
                            return True, val_code
                    elif cleaned_val in cleaned_raw:
                        return True, val_code
                return False, str(raw_str)

            def encode_incision(str_to_find: str):
                """
                :param str_to_find:
                """
                cleaned_str_to_find = str(str_to_find).lower().strip().translate(table)
                if "not applicable mastectomy done" == cleaned_str_to_find or "not applicable" == cleaned_str_to_find:
                    encoded_dict["Breast Incision Type"] = ""
                else:
                    found, code = try_encode(str_to_find)
                    encoded_dict["Breast Incision Type"] = code if found else str_to_find

            def encode_reconstruction(str_to_find: str):
                """
                :param str_to_find:
                """
                found_e, code_e = try_encode(str_to_find)
                encoded_dict["Immediate Reconstruction Mentioned"] = 1 if code_e != 0 else 0
                encoded_dict[human_col] = code_e if found_e else code_e

            def extract_from(specific_dict):
                """
                :param specific_dict:
                :return:
                """
                if human_col == "Immediate Reconstruction Type":
                    encode_reconstruction(specific_dict[human_col])
                elif human_col == "Breast Incision Type":
                    encode_incision(specific_dict[human_col])
                else:
                    raw_text = specific_dict[human_col]
                    found, code = try_encode(raw_text)
                    encoded_dict[human_col] = code if found else raw_text

            if human_col == "Laterality":
                lat = single_report.laterality
                single_report.laterality = code_book["Laterality"][lat] if lat in code_book['Laterality'] else lat
            elif human_col in extracted.keys():
                extract_from(extracted)
        return encoded_dict

    for report in reports:
        report.encoded = code_report(report)
    return reports
