from openai import OpenAI
import pandas as pd
import time
import os
from pydantic import BaseModel
from transformers import AutoTokenizer
import numpy as np

from const import WD_ENTITY_TYPES, CHANGE_TYPE_DEFINITIONS

class ScoreResponse(BaseModel):
    score: float
    explanation: str


class LLMCall():
    def __init__(self, vllm_server_node):
        self.config = {
            "llm_id": "Qwen/Qwen3.5-35B-A3B-FP8",
            "base_url": f"http://{vllm_server_node}:8001/v1",
            "temperature": 0.7,
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

        self.temperature = self.config.get('temperature', 0)
        self.max_tokens = self.config.get('max_tokens', 2048)

        model_name = "Qwen/Qwen3.5-35B-A3B-FP8"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

    def build_context_needs_reference(self,with_user_model=False, with_historic_features=False, with_change_type=False):

        context = f'''
        You are a domain expert of Wikidata, the free and open knowledge base.

        You are given a change made to an entity on Wikidata {"with:" if with_user_model or with_historic_features or with_change_type else "."}.
        {"- user information (e.g., user type, user age, number of edits, etc.) " if with_user_model else ""}
        {"- historic features (e.g., time since last change, number of value re-occurrences, etc.) " if with_historic_features else ""}
        {"- change type: " + CHANGE_TYPE_DEFINITIONS if with_change_type else ""}

        Assess whether the NEW VALUE of the change should have a reference or not.
            - These values correspond to static properties, those that shouldn't change (e.g., the birth date of a person). \n
            - If the old value is None/NULL then this represents a value insertion, if both values are present then this represents an update. In both cases, the needs_reference should be assessed for the new value (i.e., for insertions, the needs_reference of the inserted value; for updates, the needs_reference of the updated value). \n

        Return 2 values: one indicating if the value should have a reference (1) or not (0) and an explanation of why it should (or shouldn't) have a reference in the format: {{"score": <value>, "explanation": <explanation>}}. Keep the explanation under 30 words. \n

        Next I will give you each change.
        '''

        return context
    
    
    def build_context_accuracy(self,with_user_model=False, with_historic_features=False, with_change_type=False):

        context = f'''
        You are a domain expert of Wikidata, the free and open knowledge base.

        Consider the following definitions of Accuracy: 
        - “Accuracy is the extent to which data are correct, reliable and certified.” Wang and Strong [1996]
        - "Data are accurate when the data values stored in the database correspond to real-world values." Ballou and Pazer [1985]
        
        You are given a change made to an entity on Wikidata {"with:" if with_user_model or with_historic_features or with_change_type else "."}.
        {"- user information (e.g., user type, user age, number of edits, etc.) " if with_user_model else ""}
        {"- historic features (e.g., time since last change, number of value re-occurrences, etc.) which are calculated up to time t" if with_historic_features else ""}
        {"- change type: " + CHANGE_TYPE_DEFINITIONS if with_change_type else ""}

        Assess the accuracy of the NEW VALUE of the change, considering the following guidelines:
            - These values correspond to static properties, those that shouldn't change (e.g., the birth date of a person). \n
            - If the old value is None/NULL then this represents a value insertion, if both values are present then this represents an update. In both cases, the accuracy should be assessed for the new value (i.e., for insertions, the accuracy of the inserted value; for updates, the accuracy of the updated value). \n

        Return an accuracy score between 1 and 5 and an explanation for the score in the format {{'score': <value>, 'explanation': <explanation>}}. Keep the explanation under 50 words. \n

        Next I will give you each change.
        '''

        # tokens = self.tokenizer.tokenize(context)
        # token_count = len(tokens)

        # print(f"Total tokens of context: {token_count}")

        return context
    
    
    def build_content(self, data, old_datatype, new_datatype, with_user_model=False, with_historic_features=False, with_change_type=False, dimension='accuracy'):

        user_info = {}
        change_type_info = {}
        historical_info = {}

        if with_user_model:
            if data['user_type'] != 'anonymous':
                user_info = {
                    'user_type': data['user_type'],
                    'user_age_days_user': data['user_age_days_user'],
                    'num_entities_user': data['num_entities_user'],
                    'num_revisions_user': data['num_revisions_user'],
                    'num_properties_user': data['num_properties_user'],
                    'num_creates_user': data['num_creates_user'],
                    'num_deletes_user': data['num_deletes_user'],
                    'num_updates_user': data['num_updates_user'],
                    'num_reverted_edits_user': data['num_reverted_edits_user'],
                    'num_non_reverted_edits_user': data['num_non_reverted_edits_user'],
                    'avg_days_between_revisions_user': data['avg_days_between_revisions_user'],
                    'num_edits_morning_user': data['num_edits_morning_user'],
                    'num_edits_afternoon_user': data['num_edits_afternoon_user'],
                    'num_edits_night_user': data['num_edits_night_user'],
                    'num_edits_weekday_user': data['num_edits_weekday_user'],
                    'num_edits_weekend_user': data['num_edits_weekend_user'],
                    'avg_entities_per_day_user': data['avg_entities_per_day_user'],
                    'avg_properties_per_day_user': data['avg_properties_per_day_user'],
                    'property_in_top_10_most_edited_properties_by_the_user': data['user_is_expert'],
                }

            elif with_user_model and data['user_type'] == 'anonymous':
                #  don't add anything because user_type is on the single_change_info
                user_info = {
                    'user_type': data['user_type']
                }

        if with_change_type:

            change_type = data['label']

            if data['refinement'] == 1:
                change_type += ', refinement'

            if data['unrefinement'] == 1:
                change_type += ', unrefinement'
            
            if data['textual_change'] == 1:
                change_type += ', textual change'
            
            if data['re_formatting'] == 1:
                change_type += ', re-formatting'
            
            if data['property_value_update'] > 0:
                change_type += ', property value update'

            if data['link_change'] == 1:
                change_type += ', link change'

            change_type_info = {
                'change_type': change_type,
                'is_reverted': data['is_reverted'],
                'reversion': data['reversion']
            }

        if with_historic_features:
            historical_info = {
                'ratio_reverted_edits_up_to_t': data['ratio_reverted_edits_up_to_t'],
                'ratio_non_reverted_edits_up_to_t': data['ratio_non_reverted_edits_up_to_t'],
                'time_since_last_edit_days': 'First edit for this value' if data['time_since_last_edit_days'] == 0 else data['time_since_last_edit_days'],
                'time_to_next_edit_days': 'No next edit' if data['time_to_next_edit_days'] == 13*365 else data['time_to_next_edit_days'],
                'age_in_days_up_to_t': data['age_in_days_up_to_t'],
                'num_changes_wd_values_up_to_t (changes from a specific value to "no value" or "some value")': data['num_changes_wd_values'],
                'num_value_reoccurrences_up_to_t': data['num_value_reoccurrences'],
                'num_unique_registered_users_up_to_t': data['num_unique_registered_users'],
                # 'num_qualifiers_up_to_t': data['num_qualifiers_up_to_t'],
                'num_statement_insertion_up_to_t': data['num_statement_insertion'],
                'num_statement_deletion_up_to_t': data['num_statement_deletion'],
                'num_property_value_update_up_to_t': data['num_property_value_update'],
                'num_link_change_up_to_t': data['num_link_change'],
                'num_refinement_up_to_t': data['num_refinement'],
                'num_unrefinement_up_to_t': data['num_unrefinement'],
                'num_textual_change_up_to_t': data['num_textual_change'],
                'num_re_formatting_up_to_t': data['num_re_formatting']
            }

            if dimension == 'accuracy':
                historical_info['ratio_wikipedia_refs_up_to_t'] =  data['ratio_wikipedia_refs_up_to_t']
                historical_info['ratio_non_wikipedia_refs_up_to_t'] = data['ratio_non_wikipedia_refs_up_to_t']


        if not data['old_value']:
            old_value = ''
        else:
            if old_datatype in WD_ENTITY_TYPES and data['old_value_label'] == 'Unknown':
                old_value_label = 'No label known'
            elif old_datatype in WD_ENTITY_TYPES and data['old_value_label'] != 'Unknown':
                old_value_label = data['old_value_label']

            old_value = str(data['old_value']) + (f" ({old_value_label})" if old_datatype in WD_ENTITY_TYPES else '')

        if not data['new_value']:
            new_value = ''
        else:
            if new_datatype in WD_ENTITY_TYPES and data['new_value_label'] == 'Unknown':
                new_value_label = 'No label known'
            elif new_datatype in WD_ENTITY_TYPES and data['new_value_label'] != 'Unknown':
                new_value_label = data['new_value_label']

            new_value = str(data['new_value']) + (f" ({new_value_label})" if new_datatype in WD_ENTITY_TYPES else '')
        

        change_details = {
            'entity': data['entity_label'] + f" (Q{str(data['entity_id'])})",
            'property': data['property_label'] + f" (P{str(data['property_id'])})",
            'old_value': old_value,
            'new_value': new_value,
            'comment': data['comment'] if data['comment'] != '0' else 'No comment',
            'username': data['username'],
            'timestamp': data['timestamp'],
            'type_of_edit': data['action']
        }
        
        content = f'''
            Change details: \n
            {change_details}
        '''
        
        if with_change_type:
            content += f'''
                Change type: \n
                {change_type_info}
            '''

        if with_user_model:
            content += f'''
                User information: \n
                {user_info}
            '''

        if with_historic_features:
            content += f'''
                Value's historical information up to the change (t): \n
                {historical_info}
            '''

        # Get the exact token count
        # tokens = self.tokenizer.tokenize(content)
        # token_count = len(tokens)

        # print(f"Total tokens of content: {token_count}")

        # print('Max tokens set: ', self.max_tokens)

        # print('Response has to be within 50 tokens')

        return content

    def call_llm(self, change, context, old_datatype, new_datatype, with_user_model=False, with_historic_features=False, with_change_type=False, dimension='accuracy'):
        """ 
            Sends request to classify a single change to the LLM and returns the predicted class.
        """

        prompt = [
            {"role": "system", 
            "content": context}, 
            {'role': 'user',
            'content': self.build_content(change, old_datatype, new_datatype, with_user_model, with_historic_features, with_change_type, dimension)}
        ]
        try:

            # Instruct (or non-thinking) mode for general tasks:
            # temperature=0.7, top_p=0.8, top_k=20, min_p=0.0, presence_penalty=1.5, repetition_penalty=1.0

            response = self.client.beta.chat.completions.parse(
                model=self.llm_id,
                messages=prompt,
                response_format=ScoreResponse,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=0.8,
                extra_body={
                    "top_k": 20,
                    "chat_template_kwargs": {"enable_thinking": False}
                }
            )
            result = response.choices[0].message.parsed

            return result.score, result.explanation
        
        
        except Exception as e:
            print(f"Error making request: {e}")
            return '', ''

    def get_results(self, path, with_user_model=False, with_historic_features=False, with_change_type=False, dimension='accuracy'):
        """
        Parameters:
        - with_user_model - adds only user model features
        - with_historic_features - adds only historical features
        - with_change_type - adds only change type features (e.g., change_type, is_reverted and reversion)
        """

        # NOTE: Remove deletions since I'm asking for the accuracy of a value and for deletions
        # I have to ask if the absence of a value is accurate, and there I'm asking about the action, not about the value
        # itself

        df = pd.read_csv(path)

        print(f'Total number of changes: {len(df)}', flush=True)

        df_no_delete = df[df['label'] != 'statement_deletion'].copy()

        print(f'Total number of changes after filtering deletes: {len(df_no_delete)}', flush=True)

        df_no_delete_create = df_no_delete[df_no_delete['label'] == 'statement_insertion'].head(100).copy()
        df_no_delete_update = df_no_delete[(df_no_delete['label'] != 'statement_insertion') & (df_no_delete['change_type'] != '')].head(100).copy()

        df_to_process = pd.concat([df_no_delete_create, df_no_delete_update])
        print(f'Processing ' + str(len(df_to_process)) + f' changes. Parameters: with_user_model={with_user_model}, with_historic_features={with_historic_features}, with_change_type={with_change_type}, dimension={dimension}', flush=True)

        t0 = time.time()
        if dimension == 'accuracy':
            context = self.build_context_accuracy(with_user_model, with_historic_features, with_change_type)
        else:
            context = self.build_context_needs_reference(with_user_model, with_historic_features, with_change_type)
        
        suffix = ''

        if with_historic_features and with_user_model and with_change_type:
            suffix += '_all_features'

        elif with_user_model:
            suffix = '_with_user_model'
        
        elif with_historic_features:
            suffix = '_with_historic_features'
        
        elif with_change_type:
            suffix = '_with_change_type'

        elif not with_historic_features and not with_user_model and not with_change_type:
            suffix = '_no_context'
        
        df_to_process[[f'{dimension}_score_{suffix}', f'{dimension}_explanation_{suffix}']] = df_to_process.apply(lambda row: self.call_llm(row, context, row['old_datatype'], row['new_datatype'], with_user_model, with_historic_features, with_change_type, dimension), axis=1, result_type='expand')
        t1 = time.time()
        print(f" completed in {t1-t0:.2f} seconds", flush=True)

        os.makedirs('results', exist_ok=True)
        if len(df_to_process) > 0:
            df_to_process.to_csv(f'results/llm_{dimension}.csv', index=False)

        runtime = t1 - t0
        print(f"LLM {dimension} score completed in {runtime:.2f} seconds, affected {len(df_to_process)} changes. Results saved to results/llm_{dimension}.csv\n", flush=True)

        with open(f'results/llm_{dimension}_runtime.txt', 'a') as f:
            f.write(f"LLM {dimension} score completed in {runtime:.2f} seconds, affected {len(df_to_process)} changes.\n")

