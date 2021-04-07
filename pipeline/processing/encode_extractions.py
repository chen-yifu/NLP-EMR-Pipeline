"""
Encodes the extractions to numbers in code book.
"""

from typing import Dict, List, Union, Tuple
import spacy
from spacy.tokens import Span
from pipeline.utils.encoding import Encoding
from pipeline.utils.report import Report
from pipeline.utils.value import Value


def encode_extractions(reports: List[Report], code_book: Dict[str, List[Encoding]], tools: dict = {},
                       model: str = "en_core_sci_lg") -> List[Report]:
    """
    :param reports:
    :param code_book:
    :param tools:
    :param model:
    :return:
    """
    print("Beginning to encode the extractions using {}".format(model))
    nlp = spacy.load(model)

    def get_entities(val: str) -> List[Union[Span, str]]:
        """
        :param val:
        :return:
        """
        if val is None:
            val = ""
        entities = list(nlp(val).ents) if len(val.split()) > 5 else [val]
        return entities if len(entities) > 0 else [val]

    def encode_extraction_for_single_report(extractions: Dict[str, Value]) -> Dict[str, str]:
        """
        :param extractions:
        :return:
        """
        encoded_extractions_dict = {}
        for human_col, encodings in code_book.items():
            done_encoding = False

            def try_encoding(primary_value: List[Span], threshold: int = 0.6) -> Tuple[bool, str, int]:
                """
                :param primary_value:
                :param threshold:
                :return:
                """
                num = ""
                found = False
                pipeline_val_str = ""
                # init this to very low number
                alpha = float("-inf")
                for encoding in encodings:
                    for encoding_val in encoding.val:
                        code_book_doc = nlp(encoding_val)
                        for pipeline_val in primary_value:
                            pipeline_val_str = pipeline_val.text if isinstance(pipeline_val, Span) else pipeline_val
                            pipeline_doc = nlp(pipeline_val_str.lower())
                            sim = pipeline_doc.similarity(code_book_doc)
                            if sim > alpha and sim > threshold:
                                alpha = sim
                                num = str(encoding.num)
                                found = True
                            if alpha == 1 or encoding_val.lower() in pipeline_val_str:
                                return True, str(encoding.num), alpha
                if found:
                    return found, num, alpha
                else:
                    return found, "", alpha

            for encoding in encodings:
                # is the encoding is -1 it means it either depends on another column or uses a special function to be
                # encoded
                if encoding.num == -1:
                    # could either be that the column depends on another columns or has its own function to encode
                    try:
                        val_depends_on = encoded_extractions_dict[encoding.val[0]].strip()
                        encoded_extractions_dict[
                            human_col] = "0" if val_depends_on == "0" or val_depends_on == "" else "1"
                    except KeyError:
                        # means it probably has its own function
                        function_in_tools_name = encoding.val[0].strip().lower()
                        try:
                            func_in_tools = tools[function_in_tools_name]
                            encoded_extractions_dict[human_col] = func_in_tools(extractions[human_col].primary_value,
                                                                                encoded_extractions_dict)
                        except KeyError:
                            try:
                                func_in_tools = tools[function_in_tools_name]
                                encoded_extractions_dict[human_col] = func_in_tools(encoded_extractions_dict)
                            except Exception as e:
                                print(e)
                                encoded_extractions_dict[human_col] = "pipeline malfunction"
                    done_encoding = True

            # try to find the highest number, if its one then we return that num
            if not done_encoding:
                try:
                    primary_value = get_entities(extractions[human_col].primary_value)
                    alternative_val_list = extractions[human_col].alternative_value
                    has_alternative_value = alternative_val_list != []
                    alternative_value = get_entities(alternative_val_list[0]) if has_alternative_value else ""
                    found_primary, primary_encoded_value, primary_alpha = try_encoding(primary_value)
                    found_alternative, alternative_encoded_value, alternative_alpha = try_encoding(alternative_value)
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
