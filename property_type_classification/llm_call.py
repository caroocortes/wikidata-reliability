import json

from openai import OpenAI
import pandas as pd
import time
import os
from pydantic import BaseModel
from transformers import AutoTokenizer

from sklearn.metrics.pairwise import cosine_similarity

import numpy as np

class PropertyTypeResponse(BaseModel):
    property_type: str

class LLMCall():
    def __init__(self, vllm_server_node):
        self.config = {
            "llm_id": "Qwen/Qwen3.5-35B-A3B-FP8",
            "base_url": f"http://{vllm_server_node}:8001/v1",
            "temperature": 0.0,
            "max_tokens": 2048, # affects the length of the response
            "api_key": "EMPTY"
        }
        # from doc: https://huggingface.co/Qwen/Qwen3.5-35B-A3B-FP8
        self.base_url = self.config.get('base_url', '')
        self.api_key = self.config.get('api_key', 'EMPTY')

        self.llm_id = self.config.get('llm_id', '')
        
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )

        self.temperature = self.config.get('temperature', 0.0)
        self.max_tokens = self.config.get('max_tokens', 2048)

        model_name = "Qwen/Qwen3.5-35B-A3B-FP8"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

    def build_content(self, data, with_features=False):

        if data['pct_values_temporal_qualifier'] < 0.5:
            avg_col, min_col, max_col, avg_col_nc = (
                'avg_epv_avg_time_between_updates_sec',
                'avg_epv_min_time_between_updates_sec',
                'avg_epv_max_time_between_updates_sec',
                'avg_epv_avg_time_bc_nc_in_time_sec'
            )
        else:
            avg_col, min_col, max_col, avg_col_nc = (
                'avg_ep_avg_time_bc_sec',
                'avg_ep_min_time_bc_sec',
                'avg_ep_max_time_bc_sec',
                'avg_ep_avg_time_bc_nc_in_time_sec'
            )

        if data[avg_col] is None or np.isnan(data[avg_col]):
            avg_time_between_updates = min_time_between_updates = max_time_between_updates = 'No updates after creation'
        else:
            avg_time_between_updates = data[avg_col] / 86400
            min_time_between_updates = data[min_col] / 86400
            max_time_between_updates = data[max_col] / 86400

        if data[avg_col_nc] is None or np.isnan(data[avg_col_nc]):
            avg_time_between_updates_nc = 'No updates after creation'
        else:
            avg_time_between_updates_nc = data[avg_col_nc] / 86400

        lines = [
            f"Property: {data['property_label']}(P{data['property_id']})",
            f"Description: {data['property_description']}",
        ]

        if data['nn_sim'] is not None:
            lines.append(
                f"This property is semantically similar to {data['nn_property_label']} "
                f"(P{data['nn_property_id']}) classified as {data['nn_property_type']}"
            )

        if with_features:
            lines.append("Observed edit behavior:")
            lines.append(f"    Average time between updates in days: {avg_time_between_updates}")
            lines.append(f"    Average minimum time between updates in days: {min_time_between_updates}")
            lines.append(f"    Average maximum time between updates in days: {max_time_between_updates}")
            lines.append(f"    Average time between updates not within an hour: {avg_time_between_updates_nc}")
            if data['pct_values_temporal_qualifier'] > 0.5:
                lines.append('    Values are typically time-stamped when added with "point in time" or "start time".')

        return "\n".join(lines) + "\n"

    def build_context(self, static_example_props, df_static_examples, regular_example_props, df_regular_examples, irregular_example_props, df_irregular_examples, with_features=False):

        static_examples = ""
        for prop in static_example_props:
            static_examples += self.build_content(df_static_examples[df_static_examples['property_id'] == prop].iloc[0], with_features) + "Property type: static"

        regular_examples = ""
        for prop in regular_example_props:
            regular_examples += self.build_content(df_regular_examples[df_regular_examples['property_id'] == prop].iloc[0], with_features) + "Property type: regular"

        irregular_examples = ""
        for prop in irregular_example_props:
            irregular_examples += self.build_content(df_irregular_examples[df_irregular_examples['property_id'] == prop].iloc[0], with_features) + "Property type: irregular"

        context = f'''
            You are a domain expert of Wikidata, the free and open knowledge base.

            Classify the given Wikidata property into exactly one of three temporal types:
            Static properties: the value is fixed at creation and essentially never revised (may occasionally be corrected for errors, but does not change due to the world changing).
            Regular properties: value is expected to be updated at predictable intervals because the real-world value itself changes periodically (e.g., measured/reported on a schedule).
            Irregular properties: value changes in response to real-world events that occur unpredictably, not on any schedule.

            Examples for static properties:
            {static_examples} \n
            Examples for regular properties:
            {regular_examples} \n
            Examples for irregular properties:
            {irregular_examples}

            Take into account the description of the property when classifying it.
            These are properties used on Wikidata entities, so they are instanced for different entities.
            Return the property type which is one of (static, regular, or irregular) in the following JSON format: {{"property_type": "static/regular/irregular"}}
        '''

        return context

    def call_llm(self, data, context, with_features=False):
        """ 
            Sends request to classify a single change to the LLM and returns the predicted class.
        """

        prompt = [
            {"role": "system", 
            "content": context}, 
            {'role': 'user',
            'content': self.build_content(data, with_features)}
        ]
        try:

            # Instruct (or non-thinking) mode for general tasks:
            # temperature=0.7, top_p=0.8, top_k=20, min_p=0.0, presence_penalty=1.5, repetition_penalty=1.0

            response = self.client.beta.chat.completions.parse(
                model=self.llm_id,
                messages=prompt,
                response_format=PropertyTypeResponse,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=0.8,
                extra_body={
                    "top_k": 20,
                    "chat_template_kwargs": {"enable_thinking": False}
                }
            )
            result = response.choices[0].message.parsed

            return result.property_type
        
        except Exception as e:
            print(f"Error making request: {e}")
            return '', ''

    def get_results(self, path, with_features=True, sample_size=None):

        df = pd.read_csv(path)

        df_nearest_neighbors = pd.read_csv('data/property_nearest_neighbors.csv')
        df_nearest_neighbors['nearest_property_ids'] = df_nearest_neighbors['nearest_property_ids'].apply(json.loads)
        df_nearest_neighbors['nearest_property_types'] = df_nearest_neighbors['nearest_property_types'].apply(json.loads)
        df_nearest_neighbors['nearest_property_labels'] = df_nearest_neighbors['nearest_property_labels'].apply(json.loads)
        df_nearest_neighbors['nearest_similarities'] = df_nearest_neighbors['nearest_similarities'].apply(json.loads)

        def get_nearest_non_self(row):
            # Because of how I calculated the nearest 4, the first one is the closest
            for pid, plabel, ptype, sim in zip(row['nearest_property_ids'], row['nearest_property_labels'], row['nearest_property_types'], row['nearest_similarities']):
                if pid != row['property_id']:
                    return ptype, pid, plabel, sim
            return None, None, None, None

        df_nearest_neighbors[['nn_property_type', 'nn_property_id', 'nn_property_label', 'nn_sim']] = df_nearest_neighbors.apply(
            lambda r: pd.Series(get_nearest_non_self(r)), axis=1)

        df_merge = pd.merge(df, df_nearest_neighbors[['property_id', 'nn_property_type', 'nn_property_id', 'nn_property_label', 'nn_sim']], on='property_id', how='left')

        # Only use high ones as examples of semantically similar
        df_merge['nn_sim'] = np.where(df_merge['nn_sim'] >=0.75, df_merge['nn_sim'], None)

        #  ------------------------------------------------------------------------------------------
        # Select examples before filtering for non labeled and IDs
        #  ------------------------------------------------------------------------------------------
        # STATIC PROPERTIES
        static_example_props = [1164, 1458, 1714, 10894]
        # 1164 group cardinality
        # 1458 color index 
        # 1714 Journalisted ID 
        # 10894 spoken by 
        df_static_examples = df_merge[df_merge['property_id'].isin(static_example_props)].copy()

        # REGULAR PROPERTIES
        regular_example_props = [2060, 169, 1092, 1603]
        # 2060 luminosity
        # 169  chief executive officer
        # 1092 total produced
        # 1603  number of cases
        df_regular_examples = df_merge[df_merge['property_id'].isin(regular_example_props)].copy()

        # IRREGULAR PROPERTIES
        irregular_example_props = [196, 612, 11922, 15]
        # 196 minor planet group
        # 612 mother house
        # 11922 verdict
        # 15 route map
        df_irregular_examples = df_merge[df_merge['property_id'].isin(irregular_example_props)].copy()

        # NOTE: remove the notnull() for full classification
        df = df_merge[(df_merge['property_type'].notnull()) & (~df_merge['property_label'].str.contains(' ID'))].copy() 

        if sample_size is not None:
            df_static = df[(df['property_type'] == 'static')].sample(n=sample_size, random_state=42)
            df_regular = df[df['property_type'] == 'regular'].sample(n=sample_size, random_state=42)
            df_irregular = df[df['property_type'] == 'irregular'].sample(n=sample_size, random_state=42)
        else:
            df_static = df[(df['property_type'] == 'static')].copy()
            df_regular = df[df['property_type'] == 'regular'].copy()
            df_irregular = df[df['property_type'] == 'irregular'].copy()

        df = pd.concat([df_static, df_regular, df_irregular], ignore_index=True)

        t0 = time.time()

        context = self.build_context(static_example_props, 
                                     df_static_examples, 
                                     regular_example_props, 
                                     df_regular_examples, 
                                     irregular_example_props, 
                                     df_irregular_examples, 
                                     with_features)

        tokens = self.tokenizer.tokenize(context)
        token_count = len(tokens)
        print(f"Total tokens of context: {token_count}")
        
        print(f"Calling LLM to classify {len(df)} properties with features={with_features}")
        df[f'property_type_llm'] = df.apply(lambda row: self.call_llm(row, context, with_features), axis=1, result_type='expand')
        t1 = time.time()
        print(f" completed in {t1-t0:.2f} seconds", flush=True)

        os.makedirs('llm_results', exist_ok=True)
        if len(df) > 0:
            df.to_csv(f'llm_results/df_with_llm_predictions.csv', index=False)

        num_correct = len(df[df['property_type'] == df['property_type_llm']])
        print(f'Overall Accuracy: {num_correct / len(df):.4f}')

        num_correct_static = len(df[(df['property_type'] == df['property_type_llm']) & (df['property_type'] == 'static')])
        print(f'Accuracy for STATIC properties: {num_correct_static / len(df[df["property_type"] == "static"]):.4f}')

        num_correct_irregular = len(df[(df['property_type'] == df['property_type_llm']) & (df['property_type'] == 'irregular')])
        print(f'Accuracy for IRREGULAR properties: {num_correct_irregular / len(df[df["property_type"] == "irregular"]):.4f}')

        num_correct_regular = len(df[(df['property_type'] == df['property_type_llm']) & (df['property_type'] == 'regular')])
        print(f'Accuracy for REGULAR properties: {num_correct_regular / len(df[df["property_type"] == "regular"]):.4f}')

