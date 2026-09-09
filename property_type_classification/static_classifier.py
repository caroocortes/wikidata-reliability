import pandas as pd
import os
import json
import pickle

import numpy as np

from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PowerTransformer
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score, classification_report, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics.pairwise import cosine_similarity

from sentence_transformers import SentenceTransformer

EXTRA_COLUMNS = ['property_id', 'property_label']

def feature_selection():

    common_features = [
        'avg_ep_num_distinct_values', # single, multiple values
        # 'median_ep_num_distinct_values',

        'avg_epv_num_changes_after_birth_per_day', # this is per day because it has been 
        # 'median_epv_num_changes_after_birth_per_day'

        'avg_epv_avg_num_changes_per_value',
        # 'median_epv_avg_num_changes_per_value',

        'avg_epv_pct_values_ever_changed',
        # 'median_epv_pct_values_ever_changed',

        'avg_epv_avg_age_of_value_at_update_sec',
        # 'median_epv_avg_age_of_value_at_update_sec'
    ]

    routed_features = [

        ('avg_time_between_updates', 'avg_epv_avg_time_between_updates_sec', 'avg_ep_avg_time_bc_sec'),
        ('avg_min_time_between_updates', 'avg_epv_min_time_between_updates_sec', 'avg_ep_min_time_bc_sec'),
        ('avg_max_time_between_updates', 'avg_epv_max_time_between_updates_sec', 'avg_ep_max_time_bc_sec'),
        ('avg_median_time_between_updates', 'avg_epv_avg_median_time_between_updates_sec', 'avg_ep_median_time_between_updates_sec'),

        ('avg_num_close_in_time_changes', 'avg_epv_num_close_in_time_changes_per_day', 'avg_ep_num_close_in_time_changes_per_day'),
        ('avg_avg_time_bc_nc_in_time_sec', 'avg_epv_avg_time_bc_nc_in_time_sec', 'avg_ep_avg_time_bc_nc_in_time_sec'),
        
        ('avg_min_time_bc_nc_in_time_sec', 'avg_epv_min_time_bc_nc_in_time_sec', 'avg_ep_min_time_bc_nc_in_time_sec'),
        ('avg_max_time_bc_nc_in_time_sec', 'avg_epv_max_time_bc_nc_in_time_sec', 'avg_ep_max_time_bc_nc_in_time_sec'),

        ('null_rate_avg_time_between_updates_sec', 'null_rate_epv_avg_time_between_updates_sec', 'null_rate_ep_avg_time_bc_sec'),
    ]

    return common_features, routed_features


def feature_pipeline(clf):
    """
    Returns a feature pipeline for property type classification.
    """

    BIG_VALUE = 1e15

    return Pipeline([
        # I impute with a big value NULLs in all features
        # because for static properties this means they don't change
        ('impute', SimpleImputer(strategy='constant', fill_value=BIG_VALUE, add_indicator=False)),
        ('power', PowerTransformer(method='yeo-johnson')),
        ('classifier', clf),
    ])

def route_cols(df, flag_col='updates_as_creates_50'):
    common_features, routed_features = feature_selection()
    routed_feature_cols = [name for name, _, _ in routed_features]
    for name, epv_col, ep_col in routed_features:
        df[name] = np.where(df[flag_col] == 1, df[ep_col], df[epv_col])
    feature_cols = common_features + routed_feature_cols
    return df, feature_cols

def split_data(df, flag_col='updates_as_creates_50'):

    print('Target label distribution:')
    print(df['is_static'].value_counts())

    df, feature_cols = route_cols(df, flag_col=flag_col)

    # route the frequency of update features depending on the 
    # percentage of values that ever had a time qualifier (start time or point in time)
    
    y = df['is_static']
    X = df.drop(columns=['is_static', 'property_type'] + EXTRA_COLUMNS)[feature_cols].copy()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.20,
        stratify=y,
        random_state=42,
    )

    return X_train, X_test, y_train, y_test, X_train.index, X_test.index, feature_cols

def classification(df):
    """
        The property type classification is a multi-class classification.
        I use as labels the properties that have the "stability of property value" defined in Wikidata.
        I map:
        - never changes -> static
        - sometimes changes -> irregular
        - continuously changes -> regular

        However, there's little examples for regular.
        Therefore, I first do a binary classification between static and non-static (irregular + regular)

        Labeled examples from "stability of property value" in Wikidata:
        static       2778
        irregular     962
        regular        69

        Target label distribution:
        is_static
        1    2778 -> 80% are ID properties, given the imbalance dataset, I only select 60% of static properties that are ID properties
        0    1031
    """
    # NOTE: even though I classify ID properties as static, I still use 
    # the labels obtained from Wikidata to train
    df_labeled = df[df['property_type'].notnull()].copy()

    # NOTE: Do binary classification for static vs. non-static
    
    df_labeled['is_static'] = (df_labeled['property_type'] == 'static').astype(int)

    print('[LABEL DISTRIBUTION BEFORE UNDERSAMPLING]')
    print(df_labeled['is_static'].value_counts())

    df_sample_60_ids = df_labeled[(df_labeled['property_label'].str.contains(' ID')) & (df_labeled['property_type'] == 'static')].sample(frac=0.6, random_state=42)
    df_sample_non_ids = df_labeled[(~df_labeled['property_label'].str.contains(' ID')) & (df_labeled['property_type'] == 'static')].copy()
    df_non_static = df_labeled[df_labeled['property_type'] != 'static'].copy()
    df_labeled = pd.concat([df_sample_60_ids, df_sample_non_ids, df_non_static], axis=0)

    print('[LABEL DISTRIBUTION AFTER UNDERSAMPLING] - Took only 60% of static properties that are ID properties')
    print(df_labeled['is_static'].value_counts())

    X_train, X_test, y_train, y_test, train_indices, test_indices, feature_cols = split_data(df_labeled)

    params = {
        'n_estimators': [100, 200, 300],
        'max_depth': [5, 10],
        'min_samples_split': [2, 5],
        'min_samples_leaf': [1, 2],
        'max_features': ['sqrt', 'log2']
    }

    rf = RandomForestClassifier(class_weight='balanced', random_state=42)
    clf = GridSearchCV(rf, params, refit=True, cv=3, scoring='f1',  verbose=3)
    final_clf = feature_pipeline(clf)

    final_clf.fit(X_train, y_train)

    y_pred = final_clf.predict(X_test)

    print('[TEST SET] - Distribution of labels:')
    print(y_test.value_counts())
    print()

    print('[TEST SET] - Metrics:')
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, final_clf.predict_proba(X_test)[:, 1])
    classification_rep = classification_report(y_test, y_pred)

    print(f'Precision (Positive class): {precision:.4f}')
    print(f'Recall (Positive class): {recall:.4f}')
    print(f'F1-Score: {f1:.4f}')
    print(f'ROC AUC: {roc_auc:.4f}')
    print(classification_rep)

    os.makedirs('training_results', exist_ok=True)

    df_test = df_labeled.loc[test_indices].copy()
    df_test['prediction'] = y_pred
    df_test['pred_proba'] = final_clf.predict_proba(X_test)[:, 1]
    df_test.to_csv(f'training_results/df_test_predictions.csv', index=False)

    with open('training_results/static_classifier.pkl', 'wb') as f:
        pickle.dump(final_clf, f)

    with open('training_results/feature_cols.pkl', 'wb') as f:
        pickle.dump(feature_cols, f)

def inference(df, flag_col='updates_as_creates_50'):

    final_clf = pickle.load(open('training_results/static_classifier.pkl', 'rb'))

    df_unlabeled = df[df['final_property_type'].isnull()].copy()

    df_unlabeled, feature_cols = route_cols(df_unlabeled, flag_col=flag_col)
    X_unlabeled = df_unlabeled.drop(columns=['property_type'] + EXTRA_COLUMNS)[feature_cols].copy()

    # NOTE: final_clf is a pipeline, so it will already do the pre-processing on the features
    df_unlabeled['prediction_static'] = final_clf.predict(X_unlabeled)

    df_unlabeled_index = df_unlabeled.index

    df.loc[df_unlabeled_index, 'prediction_static'] = df_unlabeled['prediction_static']

    df['final_property_type'] = np.where(df['final_property_type'].notnull(), df['final_property_type'], np.where((df['prediction_static'] == 1.0), 'static', None))

    df.to_csv(f'training_results/df_with_static_predictions.csv', index=False)

def id_properties_classifier(df):
    # NOTE: Label all ID properties that don't have a proeprty type as static
    df['final_property_type'] = np.where((df['property_label'].str.contains(' ID')) & (df['property_type'].isnull()), 'static', df['property_type'])
    # NOTE: keep the property type for those that have it
    df['final_property_type'] = np.where(df['property_type'].notnull(), df['property_type'], df['final_property_type'])
    return df


def create_property_embeddings(df, only_label=False):
    model = SentenceTransformer('all-mpnet-base-v2') # 768 dimensions for each embedding

    if only_label:
        texts = df['property_label']
        
    else:
        texts = df['property_label'] + '. ' + df['property_description'].fillna('')

    suffix = '_only_label' if only_label else ''
    
    embeddings = model.encode(texts.tolist(), show_progress_bar=True)

    df['embedding'] = [json.dumps(e.tolist()) for e in embeddings]
    df_embeddings = df[['property_id', 'property_label', 'property_description', 'property_type', 'embedding']].copy()
    
    df_embeddings.to_csv(f'data/property_embeddings{suffix}.csv', index=False)

    df_embeddings['embedding'] = df_embeddings['embedding'].apply(json.loads)

    df_embeddings_labeled_props = df_embeddings[df_embeddings['property_type'].notnull()].copy()

    X_all = np.vstack(df_embeddings['embedding'].values)
    X_labeled = np.vstack(df_embeddings_labeled_props['embedding'].values)

    # similarity matrix: (n_all, n_labeled)
    sims = cosine_similarity(X_all, X_labeled)

    K = 4
    # argsort ascending, take last K, reverse for descending order
    # I want the ones wiht highest sim so I take the last K since it's ascending order
    topk_idx = np.argsort(sims, axis=1)[:, -K:][:, ::-1]

    labeled_ids = df_embeddings_labeled_props['property_id'].values
    labeled_types = df_embeddings_labeled_props['property_type'].values
    labeled_prop_labels = df_embeddings_labeled_props['property_label'].values

    # map indices -> actual property_ids and their types, per row
    nearest_ids = labeled_ids[topk_idx]          # shape (n_all, K)
    nearest_types = labeled_types[topk_idx]      # shape (n_all, K)
    nearest_prop_labels = labeled_prop_labels[topk_idx]      # shape (n_all, K)
    nearest_sims = np.take_along_axis(sims, topk_idx, axis=1)

    df_embeddings['nearest_property_ids'] = [json.dumps([int(x) for x in r]) for r in nearest_ids]
    df_embeddings['nearest_property_types'] = [json.dumps([x for x in r]) for r in nearest_types]
    df_embeddings['nearest_property_labels'] = [json.dumps([x for x in r]) for r in nearest_prop_labels]
    df_embeddings['nearest_similarities'] = [json.dumps([float(x) for x in r]) for r in nearest_sims]

    df_embeddings[['property_id', 'property_label', 'property_type', 'nearest_property_ids', 'nearest_property_labels', 'nearest_property_types', 'nearest_similarities']] \
        .to_csv(f'data/property_nearest_neighbors_{suffix}.csv', index=False)

def classify_by_nearest_neighbor(only_label=False):

    suffix = '_only_label' if only_label else ''
    df_nearest_neighbors = pd.read_csv(f'data/property_nearest_neighbors_{suffix}.csv')

    df_nearest_neighbors = df_nearest_neighbors[(df_nearest_neighbors['property_type'].notnull()) & (~df_nearest_neighbors['property_label'].str.contains(' ID'))].copy()

    df_nearest_neighbors['nearest_property_ids'] = df_nearest_neighbors['nearest_property_ids'].apply(json.loads)
    df_nearest_neighbors['nearest_property_types'] = df_nearest_neighbors['nearest_property_types'].apply(json.loads)
    df_nearest_neighbors['nearest_property_labels'] = df_nearest_neighbors['nearest_property_labels'].apply(json.loads)
    df_nearest_neighbors['nearest_similarities'] = df_nearest_neighbors['nearest_similarities'].apply(json.loads)

    print(df_nearest_neighbors['property_type'].value_counts())

    def get_nearest_non_self(row):
        # Because of how I calculated the nearest 4, the first one is the closest
        for pid, ptype, sim in zip(row['nearest_property_ids'], row['nearest_property_types'], row['nearest_similarities']):
            if pid != row['property_id']:
                return ptype, sim
        return None, None

    df_nearest_neighbors[['nn_property_type', 'nn_sim']] = df_nearest_neighbors.apply(
        lambda r: pd.Series(get_nearest_non_self(r)), axis=1)
    
    df_nearest_neighbors['sim_bucket'] = pd.cut(df_nearest_neighbors['nn_sim'], bins=[0, 0.3, 0.5, 0.7, 1.0])
    print('Bucket sizes', df_nearest_neighbors.groupby('sim_bucket').size())
    print('PCT of properties that match their nearest neighbor property type with their similarity on the respective bucket:')
    print(df_nearest_neighbors.groupby('sim_bucket').apply(
        lambda g: (g['property_type'] == g['nn_property_type']).mean()))
    
    num_correct_predictions = len(df_nearest_neighbors[df_nearest_neighbors['property_type'] == df_nearest_neighbors['nn_property_type']])
    total_predictions = len(df_nearest_neighbors)
    accuracy = num_correct_predictions / total_predictions if total_predictions > 0 else 0
    print(f'NN overall accuracy: {accuracy:.4f} ({num_correct_predictions}/{total_predictions})')
    print()

    num_correct_predictions_regular = len(df_nearest_neighbors[(df_nearest_neighbors['property_type'] == df_nearest_neighbors['nn_property_type']) & (df_nearest_neighbors['property_type'] == 'regular')])
    total_regular = len(df_nearest_neighbors[df_nearest_neighbors['property_type'] == 'regular'])
    accuracy = num_correct_predictions_regular / total_regular if total_regular > 0 else 0
    print(f'REGULAR accuracy: {accuracy:.4f} ({num_correct_predictions_regular}/{total_regular})')

    num_correct_predictions_static = len(df_nearest_neighbors[(df_nearest_neighbors['property_type'] == df_nearest_neighbors['nn_property_type']) & (df_nearest_neighbors['property_type'] == 'static')])
    total_static = len(df_nearest_neighbors[df_nearest_neighbors['property_type'] == 'static'])
    accuracy = num_correct_predictions_static / total_static if total_static > 0 else 0
    print(f'STATIC accuracy: {accuracy:.4f} ({num_correct_predictions_static}/{total_static})')

    num_correct_predictions_irregular = len(df_nearest_neighbors[(df_nearest_neighbors['property_type'] == df_nearest_neighbors['nn_property_type']) & (df_nearest_neighbors['property_type'] == 'irregular')])
    total_irregular = len(df_nearest_neighbors[df_nearest_neighbors['property_type'] == 'irregular'])
    accuracy = num_correct_predictions_irregular / total_irregular if total_irregular > 0 else 0
    print(f'IRREGULAR accuracy: {accuracy:.4f} ({num_correct_predictions_irregular}/{total_irregular})')

if __name__ == "__main__":
    df = pd.read_csv('data/features_property_type.csv')

    # id_properties_classifier(df)

    # classification(df)

    # inference(df)
    only_label = True
    create_property_embeddings(df, only_label=only_label)

    classify_by_nearest_neighbor(only_label=only_label)

