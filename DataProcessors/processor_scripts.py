import pandas as pd

from DataProcessors.parse_raw_data import get_unique_products, KNN_TRAINING_DATA_PATH, KNN_DATA_TEMP_PATH, \
    KNN_DATA_PATH, assign_category_values
from DataProcessors.pricing_data_processor import add_stats_data


def create_knn_df():
    df_unique_products = get_unique_products()
    df_train = pd.read_feather(KNN_TRAINING_DATA_PATH)
    knn_df = df_train.copy()
    for _, row in df_unique_products.iterrows():
        if row['ASIN'] not in knn_df['ASIN'].values:
            knn_df = pd.concat([knn_df, row.to_frame().T], ignore_index=True)

    knn_df = add_stats_data(knn_df)

    knn_df.to_feather(KNN_DATA_TEMP_PATH)

    return knn_df


def get_new_unique_products_data():
    knn_df = pd.read_feather(KNN_DATA_PATH)
    new_products_df = pd.DataFrame()
    for _, row in knn_df.iterrows():
        if row['Pricing Pattern'] is None:
            new_products_df = pd.concat([new_products_df, row.to_frame().T], ignore_index=True)
    new_products_df = assign_category_values(new_products_df)

    return new_products_df


def get_training_unique_products_data():
    knn_df = pd.read_feather(KNN_TRAINING_DATA_PATH)
    training_products_df = pd.DataFrame()
    for _, row in knn_df.iterrows():
        if row['Pricing Pattern'] is not None and pd.notna(row['Pricing Pattern']) and row['Pricing Pattern'] != 'BAD':
            training_products_df = pd.concat([training_products_df, row.to_frame().T], ignore_index=True)
    training_products_df = assign_category_values(training_products_df)

    return training_products_df


def copy_temp_knn_data_to_knn_data():
    df = pd.read_feather(KNN_DATA_TEMP_PATH)
    df.to_feather(KNN_DATA_PATH)
