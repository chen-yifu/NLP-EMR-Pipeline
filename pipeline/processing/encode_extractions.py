"""
Encodes the extractions to numbers in code book.
"""

from typing import Dict, List, Union, Tuple

import pandas as pd
import spacy
import torch
from scipy import spatial
from spacy.tokens import Span
from spacy.tokens.doc import Doc

from pipeline.bert.biobert import tokenizer, bert_model
from pipeline.processing.clean_text import table
from pipeline.processing.report_specific_encoding import do_nothing
from pipeline.utils.encoding import Encoding
from pipeline.utils.report import Report
from pipeline.utils.value import Value


def try_clean(val) -> Union[float, str]:
    if pd.isna(val):
        return ""
    cleaned_val = val.lower().strip()
    try:
        return float(cleaned_val)
    except:
        cleaned_val = " ".join(cleaned_val.translate(table).strip().split())
        return cleaned_val


def remove_stop_words(doc: Doc) -> str:
    clean_token = []
    for token in doc:
        if not token.is_stop:
            clean_token.append(token.text)
    return " ".join(clean_token)


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

    def get_embedding_BERT(text):
        """
        Get BERT embedding by retriving the last hidden state
        :param text: input text
        :return:     vector embedding
        """
        input_ids = torch.tensor(tokenizer.encode(text)).unsqueeze(0)
        outputs = bert_model(input_ids)
        last_hidden_states = outputs[0]
        # return last_hidden_states
        val = torch.mean(last_hidden_states, dim=1)
        return val.detach().numpy()

    def calculate_cosine_similarity(embedding1, embedding2):
        return spatial.distance.cosine(embedding1, embedding2)
        # return cosine_similarity

    def try_encoding_biobert(val_to_encode, encodings: List[Encoding], threshold: int = 0.15) -> Tuple[bool, str, int]:
        """
               :param encodings:
               :param val_to_encode:
               :param threshold:
               :return:
               """
        num = ""
        found = False
        pipeline_val_str_to_return = ""
        # init this to very large number
        alpha = 1
        for encoding in encodings:
            for encoding_val in encoding.val:
                code_book_doc = get_embedding_BERT(encoding_val)
                for pipeline_val in val_to_encode:
                    pipeline_val_str = pipeline_val.text if isinstance(pipeline_val, Span) else pipeline_val
                    pipeline_doc = get_embedding_BERT(pipeline_val_str.lower())
                    sim = calculate_cosine_similarity(pipeline_doc, code_book_doc)
                    if sim < alpha and sim < threshold:
                        alpha = sim
                        num = str(encoding.num)
                        found = True
                        pipeline_val_str_to_return = pipeline_val_str
                    if alpha == 0 or encoding_val.lower() in pipeline_val_str:
                        return True, str(encoding.num), alpha
        if found:
            return found, num, alpha
        else:
            return found, pipeline_val_str_to_return, alpha

    def try_encoding_scispacy(val_to_encode: List[Span], encodings: List[Encoding],
                              threshold: int = 0.6) -> Tuple[bool, str, int]:
        """
        :param encodings:
        :param val_to_encode:
        :param threshold:
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
                        print(pipeline_val_str, "<->", encoding_val, "score:", sim)
                        alpha = sim
                        num = str(encoding.num)
                        found = True
                        pipeline_val_str_to_return = pipeline_val_str
                    if alpha == 1 or encoding_val.lower() in pipeline_val_str:
                        return True, str(encoding.num), alpha
        if found:
            return found, num, alpha
        else:
            return found, pipeline_val_str_to_return, alpha

    def get_entities(val: str) -> List[Union[Span, str]]:
        """
        :param val:
        :return:
        """
        if val is None:
            return [""]
        doc = nlp(val)
        clean_token = []
        for token in doc:
            if not token.is_stop:
                clean_token.append(token.text)
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

            # try to find the highest number, if its one then we return that numyes
            if not done_encoding:
                try:
                    primary_val = extractions[human_col].primary_value
                    alternative_val_list = extractions[human_col].alternative_value
                    has_alternative_value = alternative_val_list != []
                    primary_val = try_clean(primary_val)
                    alternative_val = try_clean(alternative_val_list[0]) if has_alternative_value else ""
                    cleaned_primary_val = get_entities(primary_val)
                    cleaned_alternative_val = get_entities(alternative_val)
                    found_primary, primary_encoded_value, primary_alpha = try_encoding_scispacy(cleaned_primary_val,
                                                                                                encodings)
                    found_alternative, alternative_encoded_value, alternative_alpha = try_encoding_scispacy(
                        cleaned_alternative_val, encodings)
                    # found_primary, primary_encoded_value, primary_alpha = try_encoding_biobert(primary_value,
                    #                                                                            encodings)
                    # found_alternative, alternative_encoded_value, alternative_alpha = try_encoding_biobert(
                    #     alternative_value, encodings)
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
        print(report.report_id)
        report.encoded = encode_extraction_for_single_report(report.extractions)
    return reports
