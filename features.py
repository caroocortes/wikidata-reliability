import pandas as pd
import os
import numpy as np

from sklearn.preprocessing import MultiLabelBinarizer

from const import GOOD_COMMENT_KEYWORDS, BASE_COLS, WD_ENTITY_TYPES

feature_dict = {
    'single_change': {
        'categorical': ['time_of_day', 'time_of_week', 'type_of_next_edit'],
        'categorical_binary': ['is_reverted', 'reversion', 'refinement', 'unrefinement', 'textual_change', 're_formatting', 'link_change', 
                      'property_value_update', 'statement_insertion', 'statement_deletion'
                    #   , 'comment_has_keyword'
        ],
        # TODO: Agregar 'soft_deletion', 'soft_insertion' cuando agregue cambios de rank -> capaz que esto tiene que ser una feature
        # ej: rank is deprecated in the future o algo así
        'numerical': []
    },
    'user_model': {
        # NOTE: I add "_user" as suffix
        'categorical': ['user_type'],
        'categorical_binary' : ['user_is_expert'],
        'numerical': ['user_age_days_user', 'num_entities_user', 'num_revisions_user', 'num_properties_user', 
                    'num_creates_user', 'num_deletes_user', 'num_updates_user', 'num_value_changes_user', 
                    'num_reverted_edits_user', 'num_non_reverted_edits_user', 'avg_days_between_revisions_user',
                    'num_edits_morning_user', 'num_edits_afternoon_user', 'num_edits_night_user', 
                    'num_edits_weekday_user', 'num_edits_weekend_user', 'avg_entities_per_day_user', 'avg_properties_per_day_user']
    },
    'historical': {
        'categorical': [],
        'numerical': ['ratio_reverted_edits_up_to_t', 'ratio_non_reverted_edits_up_to_t',
                    'time_since_last_edit_days', 'time_to_next_edit_days',
                    'value_age_in_entity_in_days_up_to_t',
                    'num_changes_wd_values', 'num_value_reoccurrences',
                    'num_unique_registered_users', 'ratio_wikipedia_refs_up_to_t',
                    'ratio_non_wikipedia_refs_up_to_t', 
                    'num_wikipedia_refs_up_to_t', 'num_non_wikipedia_refs_up_to_t',
                    'num_references_up_to_t',
                    # 'total_changes_up_to_t', 'total_references_up_to_t', # this 2 features are used with the ratio of references
                    'num_statement_insertion',
                    'num_statement_deletion', 'num_property_value_update',
                    'num_link_change', 'num_refinement', 'num_unrefinement',
                    'num_textual_change', 'num_re_formatting']
    },
    'property': {
        'categorical': [],
        'categorical_binary': ['citation_needed'],
        'numerical': ['property_reference_rate'
                    #   , 'property_age_in_entity_in_days_up_to_t'
                    ]
    },
    'entity': {
        'categorical': [],
        # NOTE: not implemented yet
        'numerical': ['entity_reference_rate_up_to_t', 'entity_age_days']
    }
}

def single_change_features(df, df_user_model, df_prop_ref_rate):
    """
    - user type
    - time of day of the edit (morning, afternoon, night)
    - time of the week (weekday, weekend)
    - keywords in comments 
    - change type 
    - is reverted
    - reversion
    - type of next edit (create, delete, update, none)
    """
    df['hour'] = df['timestamp'].dt.hour
    time_of_day_conditions = [
        (df['hour'] <= 11) & (df['hour'] >= 6),
        (df['hour'] < 20) & (df['hour'] >= 12),
        (df['hour'] >= 20) | (df['hour'] < 6)
    ]
    time_of_day_choices = ['morning', 'afternoon', 'night']
    df['time_of_day'] = np.select(time_of_day_conditions, time_of_day_choices, default=None)
    df['time_of_week'] = np.where(df['timestamp'].dt.weekday > 4, 'weekend', 'weekday')

    df['type_of_next_edit'] = df.groupby(['entity_id', 'property_id', 'value_id'])['action'].shift(-1).fillna('None')

    df['comment_has_keyword'] = df['comment'].str.contains('|'.join(GOOD_COMMENT_KEYWORDS), case=False, na=False).astype(int)

    df_user_model['user_age_days'] = (pd.to_datetime(df_user_model['last_edit'], utc=True) - pd.to_datetime(df_user_model['first_edit'], utc=True)).dt.days
    
    df_user_model['avg_entities_per_day'] = df_user_model['avg_entities_per_day'].fillna(0)
    df_user_model['avg_properties_per_day'] = df_user_model['avg_properties_per_day'].fillna(0)

    # differentiate columns of the user model for merging with the main df
    df_user_model = df_user_model.add_suffix('_user')

    df_with_user_info = df.merge(df_user_model, left_on='user_id', right_on='user_id_user', how='left')

    df_with_user_info['property_id_expertise_list'] = df_with_user_info['property_id_expertise_list_user'].apply(
        lambda x: [s.strip() for s in x.strip('{}').split(',')] if isinstance(x, str) else []
    )

    df_with_user_info['user_is_expert'] = df_with_user_info.apply(
        lambda row: 1 if str(row['property_id']) in row['property_id_expertise_list'] else 0,
        axis=1
    )

    user_model_cols = [col for col in df_user_model.columns if col != 'user_id_user' and col != 'username_user' and col != 'user_type_user']
    

    df_final = df_with_user_info.merge(df_prop_ref_rate, on='property_id', how='left')

    df_final = df_final.rename(columns={'reference_rate': 'property_reference_rate'})

    single_change_cols = ['user_type', 'time_of_day', 'time_of_week', 'is_reverted', 'type_of_next_edit',
                          'reversion', 'comment_has_keyword', 'user_is_expert', 'citation_needed', 'property_reference_rate']

    return df_final, single_change_cols + user_model_cols


def aggregated_features(df, df_references, change_types, datatype_map):
    GROUP = ['entity_id', 'property_id', 'value_id']

    df['num_reverted_edits_up_to_t'] = (
        df.groupby(['entity_id','property_id', 'value_id'])['is_reverted'] # is reverted is binary
        .cumsum()
    ).fillna(0)

    df['total_changes_up_to_t'] = (
        df.groupby(['entity_id','property_id', 'value_id'])
        .cumcount() + 1 # starts at 0, so +1 to count the current edit as well
    )

    # NOTE: I consider non-reverted those that are not reverted and that are also not reversions!!
    df['num_non_reverted_edits_up_to_t'] = (
        df.assign(is_clean=(df['is_reverted'] == 0) & (df['reversion'] == 0))
        .groupby(GROUP)['is_clean']
        .cumsum()
    ).fillna(0)

    df['last_edit_time'] = df['timestamp'].shift(1) # timestamps are ordered
    df['next_edit_time'] = df['timestamp'].shift(-1)

    df['time_since_last_edit_days'] = (
        df.groupby(GROUP)['timestamp']
        .diff()
        .dt.total_seconds() / 86400
    )
    df['time_to_next_edit_days'] = (
        df.groupby(GROUP)['timestamp']
        .diff(-1)
        .dt.total_seconds() / 86400 * -1  # diff(-1) gives negative, flip sign
    )

    df['time_to_next_edit_days'] = df['time_to_next_edit_days'].replace(0, 13*365) # if there's no next edit, set to 13 years (max observed time in the whole dataset)

    df['min_timestamp'] = df.groupby(GROUP)['timestamp'].transform('min')

    df['value_age_in_entity_in_days_up_to_t'] = (df['timestamp'] - df['min_timestamp']).dt.total_seconds() / 86400  # in days

    #  number of edits per user type
    for user_type in ['human', 'bot', 'anonymous']:
        df[f'num_edits_{user_type}'] = (
            df[df['user_type'] == user_type]
            .groupby(GROUP)
            .cumcount()
        )
    # for creates and deletes one of them is NULL
    df['old_datatype'] = df['old_datatype'].fillna('')
    df['new_datatype'] = df['new_datatype'].fillna('')

    df['expected_datatype'] = df['property_id'].map(datatype_map)
    df['is_wd_value_change'] = np.where(
        ((df['old_datatype'] == 'unknown-values') | (df['new_datatype'] == 'unknown-values')) & ((df['old_datatype'].notna()) & (df['new_datatype'].notna())),
        1, 0
    )

    df['num_changes_wd_values'] = (
        df.groupby(GROUP)['is_wd_value_change']
        .cumsum()
    )
    
    for change_type in change_types:
        df[f'num_{change_type}'] = (
            df.assign(is_type=df[change_type] == 1)
            .groupby(GROUP)['is_type']
            .cumsum()
        )
    
    df['num_value_reoccurrences'] = (
        df.assign(is_same_value=1)
        .groupby(GROUP + ['new_value'])['is_same_value'] # grouping by new_value makes 1 group per value for the property-entity-value-id
        .cumsum() - 1  # -1 so the first appearance is 0, not 1
    )

    df['num_unique_registered_users'] = ( 
        df.groupby(GROUP)['user_id'].transform(lambda x: x.expanding().apply(lambda s: s.nunique()))
    )

    # ---------------------------- WIKIPEDIA REFERENCES ----------------------------

    # deduplicate: one row per ref_hash per action (keep first occurrence)
    # this is because references can have multiple attributes, so I have to count 1 per hash, not 1 per attribute
    df_references_deduped = (
        df_references
        .sort_values('timestamp')
        .drop_duplicates(subset=['entity_id', 'property_id', 'value_id', 'ref_hash', 'action'])
    )

    # CREATE +1, DELETE -1
    df_references_deduped['ref_delta'] = df_references_deduped['action'].map({'CREATE': 1, 'DELETE': -1})

    df_references_wikipedia = df_references_deduped[df_references_deduped['ref_property_id'] == 143].copy() # filter the property "imported from Wikipedia project"

    # running sum of active references at each point per entity,property,value_id
    df_references_wikipedia['wiki_refs_up_to_t'] = (
        df_references_wikipedia
        .sort_values('timestamp')
        .groupby(GROUP)['ref_delta']
        .cumsum()
    )

    df = df.sort_values('timestamp')
    df_references_wikipedia = df_references_wikipedia.sort_values('timestamp')

    df = pd.merge_asof(
        df,
        df_references_wikipedia[['entity_id', 'property_id', 'value_id', 'change_target', 'timestamp', 'wiki_refs_up_to_t']],
        on='timestamp',
        by=['entity_id', 'property_id', 'value_id', 'change_target'],
        direction='backward'  # match to the nearest earliest time
    )

    df['num_wikipedia_refs_up_to_t'] = df['wiki_refs_up_to_t'].fillna(0)

    # ---------------------------- non WIKIPEDIA REFERENCES ----------------------------
    df_references_non_wikipedia = df_references_deduped[df_references_deduped['ref_property_id'] != 143].copy()

    # running sum of active references at each point per entity,property,value_id
    df_references_non_wikipedia['non_wiki_refs_up_to_t'] = (
        df_references_non_wikipedia
        .sort_values('timestamp')
        .groupby(GROUP)['ref_delta']
        .cumsum()
    )

    df = df.sort_values('timestamp')
    df_references_non_wikipedia = df_references_non_wikipedia.sort_values('timestamp')

    df = pd.merge_asof(
        df,
        df_references_non_wikipedia[['entity_id', 'property_id', 'value_id', 'change_target', 'timestamp', 'non_wiki_refs_up_to_t']],
        on='timestamp',
        by=['entity_id', 'property_id', 'value_id', 'change_target'],
        direction='backward'  # take the latest reference row with timestamp <= current
    )

    df['num_non_wikipedia_refs_up_to_t'] = df['non_wiki_refs_up_to_t'].fillna(0)

    df['num_references_up_to_t'] = df['num_wikipedia_refs_up_to_t'] + df['num_non_wikipedia_refs_up_to_t']

    # NOTE: remove for now, I don't think this count makes much sense
    # ---------------------------- QUALIFIERS ----------------------------
    # df_qualifiers['qual_delta'] = df_qualifiers['action'].map({'CREATE': 1, 'DELETE': -1})
    # # running sum of active references at each point per entity,property,value_id
    # df_qualifiers['quals_up_to_t'] = (
    #     df_qualifiers
    #     .sort_values('timestamp')
    #     .groupby(GROUP)['qual_delta']
    #     .cumsum()
    # )

    # df = df.sort_values('timestamp')
    # df_qualifiers = df_qualifiers.sort_values('timestamp')

    # df = pd.merge_asof(
    #     df,
    #     df_qualifiers[['entity_id', 'property_id', 'value_id', 'change_target', 'timestamp', 'quals_up_to_t']],
    #     on='timestamp',
    #     by=['entity_id', 'property_id', 'value_id', 'change_target'],
    #     direction='backward'  # take the latest reference row with timestamp <= current
    # )

    # df['num_qualifiers_up_to_t'] = df['quals_up_to_t'].fillna(0)

    # ------- Add totals for the measure ---------

    df['ratio_reverted_edits_up_to_t'] = np.where(df['total_changes_up_to_t'] > 0, df['num_reverted_edits_up_to_t'] / df['total_changes_up_to_t'], 0)
    df['ratio_non_reverted_edits_up_to_t'] = np.where(df['total_changes_up_to_t'] > 0, df['num_non_reverted_edits_up_to_t'] / df['total_changes_up_to_t'], 0)

    df['total_references_up_to_t'] = df['num_wikipedia_refs_up_to_t'] + df['num_non_wikipedia_refs_up_to_t']

    df['ratio_non_wikipedia_refs_up_to_t'] = np.where(df['total_references_up_to_t'] > 0, df['num_non_wikipedia_refs_up_to_t'] / df['total_references_up_to_t'], 0)
    df['ratio_wikipedia_refs_up_to_t'] = np.where(df['total_references_up_to_t'] > 0, df['num_wikipedia_refs_up_to_t'] / df['total_references_up_to_t'], 0)

    feature_cols = [

        'num_reverted_edits_up_to_t',
        'num_non_reverted_edits_up_to_t',
        'ratio_reverted_edits_up_to_t',
        'ratio_non_reverted_edits_up_to_t',
        'time_since_last_edit_days',
        'time_to_next_edit_days',
        'value_age_in_entity_in_days_up_to_t',

        'num_changes_wd_values',
        'num_value_reoccurrences',
        'num_unique_registered_users',

        'num_references_up_to_t',
        'num_wikipedia_refs_up_to_t',
        'num_non_wikipedia_refs_up_to_t',
        'ratio_non_wikipedia_refs_up_to_t',
        'ratio_wikipedia_refs_up_to_t',
        # 'num_qualifiers_up_to_t',
        'total_changes_up_to_t',
        'total_references_up_to_t'
    ]

    for change_type in change_types:
        feature_cols.append(f'num_{change_type}')

    return df, feature_cols   

def create_change_types_columns(df):
    mlb = MultiLabelBinarizer()
    df['label'] = df['label'].str.replace('value_update', 'property_value_update')

    df['change_type'] = df['change_type'].fillna('')
    df['label'] = df['label'].fillna('')

    df['labels_list'] = np.where(df['label'] == '', df['change_type'], np.where(df['change_type'] == '', df['label'], df['change_type'] + ',' + df['label']))
    df['labels_list'] = df['labels_list'].fillna('')

    df['labels_list'] = df['labels_list'].str.split(',').apply(lambda x: [l.strip() for l in x])
    labels = mlb.fit_transform(df['labels_list'])

    df = df.reset_index(drop=True)
    df = pd.concat([df, pd.DataFrame(labels, columns=mlb.classes_)], axis=1)

    change_types = mlb.classes_.tolist()
    return df, change_types

def create_features():
    # load changes
    df = pd.read_csv(os.path.join("data", "sample_value_changes.csv"), parse_dates=['timestamp'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df = df.sort_values(['property_id', 'entity_id', 'value_id', 'timestamp'])

    # load references 
    df_ref = pd.read_csv(os.path.join("data", "sample_references.csv"), parse_dates=['timestamp'])
    df_ref['timestamp'] = pd.to_datetime(df_ref['timestamp'], utc=True)
    df_ref = df_ref.sort_values(['property_id', 'entity_id', 'value_id', 'timestamp'])

    # load qualifiers
    # df_qual = pd.read_csv(os.path.join("data", "sample_qualifiers.csv"), parse_dates=['timestamp'])
    # df_qual['timestamp'] = pd.to_datetime(df_qual['timestamp'], utc=True)
    # df_qual = df_qual.sort_values(['property_id', 'entity_id', 'value_id', 'timestamp'])

    df_prop_ref_rate = pd.read_csv(os.path.join("data", "prop_ref_rate.csv"), usecols=['property_id', 'reference_rate', 'citation_needed'])
    
    #  load user model features
    df_user_model = pd.read_csv(os.path.join("data", "user_model.csv"))

    df['new_value'] = df['new_value'].replace(r'^\{\}$', None, regex=True)
    df['old_value'] = df['old_value'].replace(r'^\{\}$', None, regex=True)

    df, change_types = create_change_types_columns(df)

    # create single change features
    df, features_single_change = single_change_features(df, df_user_model, df_prop_ref_rate)

    datatype_map = df.groupby('property_id')['new_datatype'].agg(lambda x: x.mode()[0]).to_dict()

    # create historical features
    df, features_aggregated = aggregated_features(df, df_ref, change_types, datatype_map)

    feature_cols = features_single_change + features_aggregated + change_types

    features_df = df[BASE_COLS + feature_cols].fillna(0)

    
    features_df['new_value_label'] = np.where(
            (features_df['new_value'].notna()) & (features_df['new_datatype'].isin(WD_ENTITY_TYPES)) & (features_df['new_value_label'] != 0), 
            features_df['new_value_label'], 
            np.where(
            (features_df['new_value'].notna()) & (features_df['new_datatype'].isin(WD_ENTITY_TYPES)) & (features_df['new_value_label'] == 0),
            'Unknown', 
            None)
    )
    
    features_df['old_value_label'] = np.where(
            (features_df['old_value'].notna()) & (features_df['old_datatype'].isin(WD_ENTITY_TYPES)) & (features_df['old_value_label'] != 0), 
            features_df['old_value_label'], 
            np.where(
            (features_df['old_value'].notna()) & (features_df['old_datatype'].isin(WD_ENTITY_TYPES)) & (features_df['old_value_label'] == 0),
            'Unknown', 
            None)
    )
    features_df.to_csv(os.path.join("data", "features.csv"), index=False)

    features_df['comment'].fillna('', inplace=True)

    return features_df


if __name__ == "__main__":

    if not os.path.exists(os.path.join("data", "features.csv")):
        features_df = create_features()
    else:
        print('Features already created in data/features.csv')



