"""
Encodes the extractions to numbers in code book.
"""

from typing import Dict, List, Union, Tuple
import spacy
from spacy.tokens import Span
from pipeline.util.encoding import Encoding
from pipeline.util.report import Report
from pipeline.util.value import Value


def encode_extractions(reports: List[Report], code_book: Dict[str, List[Encoding]], tools: dict = {},
                       model: str = "en_core_sci_lg") -> List[Report]:
    nlp = spacy.load(model)

    def get_entities(val: str, human_col) -> List[Union[Span, str]]:
        if val is None:
            val = ""
        entities = list(nlp(val).ents) if len(val.split()) > 3 else [val]
        return entities if len(entities) > 0 else [val]

    def encode_extraction_for_single_report(extractions: Dict[str, Value], report_id: str, lat: str) -> Dict[str, str]:
        encoded_extractions_dict = {}
        for human_col, encodings in code_book.items():
            done_encoding = False

            def try_encoding(primary_value: List[Span], alternative_value: List[str],
                             threshold: int = 0.5) -> Tuple[bool, str]:
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
                                return True, str(encoding.num)
                if found:
                    return found, num
                else:
                    return found, pipeline_val_str

            for encoding in encodings:
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
                    primary_value = get_entities(extractions[human_col].primary_value, human_col)
                    alternative_val_list = extractions[human_col].alternative_value
                    has_alternative_value = alternative_val_list != []
                    alternative_value = get_entities(alternative_val_list[0],
                                                     human_col) if has_alternative_value else ""
                    found, encoded_value = try_encoding(primary_value, alternative_value)
                    encoded_extractions_dict[human_col] = encoded_value if found else ""
                except KeyError:
                    print("This should of not occurred.")

        return encoded_extractions_dict

    for report in reports:
        report.encoded = encode_extraction_for_single_report(report.extractions, report.report_id, report.laterality)
    return reports
