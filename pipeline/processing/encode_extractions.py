"""
Encodes the extractions to numbers in code book.
"""

from typing import Dict, List, Union, Tuple
import pandas as pd
import spacy
from spacy.tokens import Span
from pipeline.processing.report_specific_encoding import do_nothing
from pipeline.utils.encoding import Encoding
from pipeline.utils.report import Report
from pipeline.utils.value import Value

nlp = spacy.load("en_core_sci_lg")


def remove_stop_words(val: str) -> str:
    if pd.isna(val):
        val = ""
    doc = nlp(val)
    clean_token = []
    for token in doc:
        if not token.is_stop:
            clean_token.append(token.text)
    return " ".join(clean_token)


def get_entities(val: str) -> List[Union[Span, str]]:
    """
    :param val:
    :return:
    """
    if val is None or pd.isna(val):
        return [""]
    if type(val) is float or pd.isna(val):
        val = ""
    doc = nlp(val)
    clean_token = []
    for token in doc:
        if not token.is_stop:
            clean_token.append(token.text)
    entities = list(nlp(val).ents) if len(val.split()) > 5 else [val]
    return entities if len(entities) > 0 else [val]


def encode_extractions(reports: List[Report], code_book: Dict[str, List[Encoding]], threshold: float, tools: dict = {},
                       model: str = "en_core_sci_lg") -> List[Report]:
    """
    :param reports:
    :param code_book:
    :param tools:
    :param model:
    :return:
    """
    print("Beginning to encode the extractions using {}".format(model))

    def encode_extraction_for_single_report(extractions: Dict[str, Value]) -> Dict[str, str]:
        """
        :param extractions:
        :return:
        """
        encoded_extractions_dict = {}
        for human_col, encodings in code_book.items():
            done_encoding = False

            def try_encoding_scispacy(val_to_encode: List[Span], print_debug: bool = False) -> Tuple[bool, str, int]:
                """
                :param print_debug:
                :param val_to_encode:
                :return:
                """
                num = ""
                found = False
                pipeline_val_str_to_return = ""
                # init this to very low number
                alpha = float("-inf")
                for encoding in encodings:
                    for encoding_val in encoding.val:
                        code_book_doc = nlp(encoding_val)
                        for pipeline_val in val_to_encode:
                            pipeline_val_str = pipeline_val.text if isinstance(pipeline_val, Span) else pipeline_val
                            pipeline_doc = nlp(pipeline_val_str.lower())
                            sim = pipeline_doc.similarity(code_book_doc)
                            if sim > alpha and sim > threshold:
                                alpha = sim
                                num = str(encoding.num)
                                found = True
                                pipeline_val_str_to_return = pipeline_val_str
                            if alpha == 1 or encoding_val.lower() in pipeline_val_str:
                                return True, str(encoding.num), 1
                if found:
                    return found, num, alpha
                else:
                    return found, pipeline_val_str_to_return, alpha

            for encoding in encodings:
                # is the encoding is -1 it means it either depends on another column or uses a special function to be
                # encoded
                if encoding.num == -1:
                    possible_function_name = encoding.val[0].strip().lower()
                    human_column_name = human_col.lower().strip()
                    possible_functions = [f.lower().strip() for f in tools.keys()]
                    if human_column_name in possible_functions:
                        func_in_tools = tools[human_column_name]
                    elif possible_function_name in possible_functions:
                        func_in_tools = tools[possible_function_name]
                    else:
                        print("Function for {} not found, will use default function".format(
                            human_column_name + " | " + possible_function_name))
                        func_in_tools = do_nothing
                    try:
                        val = extractions[human_col].primary_value
                        encoded_extractions_dict[human_col] = func_in_tools(val, encoded_extractions_dict)
                    except Exception as e:
                        try:
                            encoded_extractions_dict[human_col] = func_in_tools(encoded_extractions_dict)
                        except Exception as e:
                            print(e)
                            encoded_extractions_dict[human_col] = "pipeline malfunction"
                    done_encoding = True

            # try to find the highest number, if its one then we return that num
            if not done_encoding:
                try:
                    primary_val = extractions[human_col].primary_value
                    alternative_val = extractions[human_col].alternative_value[0] if extractions[
                                                                                         human_col].alternative_value != [] else ""
                    cleaned_primary_val = get_entities(primary_val)
                    cleaned_alternative_val = get_entities(alternative_val)
                    found_primary, primary_encoded_value, primary_alpha = try_encoding_scispacy(cleaned_primary_val,
                                                                                                encodings)
                    found_alternative, alternative_encoded_value, alternative_alpha = try_encoding_scispacy(
                        cleaned_alternative_val, encodings)
                    if primary_alpha == 1 and found_primary:
                        encoded_extractions_dict[human_col] = primary_encoded_value
                    elif alternative_alpha == 1 and found_alternative:
                        encoded_extractions_dict[human_col] = alternative_encoded_value
                    elif primary_alpha > alternative_alpha and found_primary:
                        encoded_extractions_dict[human_col] = primary_encoded_value
                    elif alternative_alpha > primary_alpha and found_alternative:
                        encoded_extractions_dict[human_col] = alternative_encoded_value
                    else:
                        encoded_extractions_dict[human_col] = ""
                except KeyError:
                    print("This should of not occurred.")

        return encoded_extractions_dict

    for report in reports:
        report.encoded = encode_extraction_for_single_report(report.extractions)
    return reports
