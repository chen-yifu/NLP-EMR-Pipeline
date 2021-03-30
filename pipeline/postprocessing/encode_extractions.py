from typing import Dict, List, Union, Tuple
import pandas as pd
import re
from nltk import edit_distance
from spacy.tokens import Span
from transformers import BertModel, BertTokenizer
import torch
import scispacy
import spacy

from pipeline.util.column import Column
from pipeline.util.encoding import Encoding
from pipeline.util.report import Report
from pipeline.util.value import Value


def encode_extractions(reports: List[Report], code_book: Dict[str, List[Encoding]],
                       model: str = "en_core_sci_lg") -> List[Report]:
    nlp = spacy.load(model)

    def encode_extraction_for_single_report(extractions: Dict[str, Value], report_id: str) -> Dict[str, str]:
        encoded_extractions_dict = {}
        for human_col, encodings in code_book.items():
            def get_entities(val: str) -> List[Union[Span, str]]:
                entities = list(nlp(val).ents)
                print(report.report_id)
                print(human_col + " " + str(entities))
                return entities if len(entities) > 0 else [val]

            def try_encoding(primary_value: List[Span], alternative_value: List[str],
                             threshold: int = 0.5) -> Tuple[bool, str]:
                num = ""
                found = False
                # init this to very low number
                alpha = float("-inf")
                for encoding in encodings:
                    for encoding_val in encoding.val:
                        code_book_doc = nlp(encoding_val)
                        for pipeline_val in primary_value:
                            pipeline_doc = nlp(pipeline_val.text) if isinstance(pipeline_val, Span) else nlp(
                                pipeline_val)
                            sim = pipeline_doc.similarity(code_book_doc)
                            if sim > alpha and sim > threshold:
                                alpha = sim
                                num = str(encoding.num)
                                found = True
                            if alpha == 1:
                                return True, str(encoding.num)
                return found, num

            # find the corresponding value from extractions

            # try to findest the highest number, if its one then we return that num
            try:
                primary_value = get_entities(extractions[human_col].primary_value)
                alternative_val_list = extractions[human_col].alternative_value
                has_alternative_value = alternative_val_list != []
                alternative_value = get_entities(alternative_val_list[0]) if has_alternative_value else ""
                found, encoded_value = try_encoding(primary_value, alternative_value)
                encoded_extractions_dict[human_col] = encoded_value if found else ""
            except KeyError:
                print("This should of not occurred.")

            for encoding in encodings:
                if encoding.num == -1:
                    val_depends_on = encoded_extractions_dict[encoding.val[0]].strip()
                    encoded_extractions_dict[human_col] = "0" if val_depends_on == "0" or val_depends_on == "" else "1"
        return encoded_extractions_dict

    for report in reports:
        report.encoded = encode_extraction_for_single_report(report.extractions, report.report_id)
    return reports