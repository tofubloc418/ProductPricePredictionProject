import os.path
from os.path import join

import pandas as pd

from Data import DATA_DIR
from DataProcessors.parse_raw_data import get_unique_products, LABELED_PRODUCTS_PATH, \
    UNIQUE_PRODUCTS_WITH_FEATURES_TEMP_PATH, \
    UNIQUE_PRODUCTS_WITH_FEATURES_PATH, assign_category_values, clean_raw_data, RAW_DATA_PATH, scale_data
from DataProcessors.pricing_data_processor import add_stats_data

MINIROCKET_TEST_DATA_PATH = join(DATA_DIR, "minirocket_test_data.feather")


def create_knn_df():
    df_unique_products = get_unique_products()
    df_train = pd.read_feather(LABELED_PRODUCTS_PATH)
    knn_df = df_train.copy()
    for _, row in df_unique_products.iterrows():
        if row['ASIN'] not in knn_df['ASIN'].values:
            knn_df = pd.concat([knn_df, row.to_frame().T], ignore_index=True)

    knn_df = add_stats_data(knn_df)

    knn_df.to_feather(UNIQUE_PRODUCTS_WITH_FEATURES_TEMP_PATH)

    return knn_df


def get_new_unique_products_data_for_classifiers():
    knn_df = pd.read_feather(UNIQUE_PRODUCTS_WITH_FEATURES_PATH)
    new_products_df = pd.DataFrame()
    for _, row in knn_df.iterrows():
        if row['Pricing Pattern'] is None:
            new_products_df = pd.concat([new_products_df, row.to_frame().T], ignore_index=True)
    new_products_df = assign_category_values(new_products_df)

    return new_products_df


def get_training_unique_products_data_for_classifiers():
    knn_df = pd.read_feather(LABELED_PRODUCTS_PATH)
    training_products_df = pd.DataFrame()
    for _, row in knn_df.iterrows():
        if row['Pricing Pattern'] is not None and pd.notna(row['Pricing Pattern']) and row['Pricing Pattern'] != 'BAD':
            training_products_df = pd.concat([training_products_df, row.to_frame().T], ignore_index=True)
    training_products_df = assign_category_values(training_products_df)

    return training_products_df


def copy_temp_knn_data_to_knn_data():
    df = pd.read_feather(UNIQUE_PRODUCTS_WITH_FEATURES_TEMP_PATH)
    df.to_feather(UNIQUE_PRODUCTS_WITH_FEATURES_PATH)


def minirocket_test_add_pricing_patterns(df):
    df_labeled_products = pd.read_feather(LABELED_PRODUCTS_PATH)
    df = df.merge(df_labeled_products[['ASIN', 'Pricing Pattern']], on='ASIN', how='inner')

    return df


def get_minirocket_test_data_original():
    df = clean_raw_data(RAW_DATA_PATH)
    df_scaled = scale_data(df)
    df_with_pricing_patterns = minirocket_test_add_pricing_patterns(df_scaled)

    return df_with_pricing_patterns


def get_minirocket_test_data(use_cache=False):
    if use_cache and os.path.isfile(MINIROCKET_TEST_DATA_PATH) and os.path.getsize(MINIROCKET_TEST_DATA_PATH) > 0:
        print('****    READ MINIROCKET TEST DATA FROM CACHE   ****')
        df_with_pricing_patterns = pd.read_feather(MINIROCKET_TEST_DATA_PATH)
        df_with_pricing_patterns.columns = [int(c) if c.isnumeric() else c for c in df_with_pricing_patterns]
    else:
        df = clean_raw_data(RAW_DATA_PATH)
        df_scaled = scale_data(df)
        df_with_pricing_patterns = minirocket_test_add_pricing_patterns(df_scaled)
        save_minirocket_test_data_to_feather(df_with_pricing_patterns)

    return df_with_pricing_patterns


def save_minirocket_test_data_to_feather(df):
    df.columns = [str(c) for c in df.columns]  # feather requires column names to be str
    df.to_feather(MINIROCKET_TEST_DATA_PATH, compression='zstd')
