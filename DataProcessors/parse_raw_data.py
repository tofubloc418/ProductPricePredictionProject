from os.path import join

import pandas as pd

from Data import DATA_DIR

KNN_DATA_PATH = join(DATA_DIR, 'knn_data.feather')
KNN_DATA_TEMP_PATH = join(DATA_DIR, 'knn_data_temp.feather')
KNN_TRAINING_DATA_PATH = join(DATA_DIR, 'knn_training_data.feather')
RAW_DATA_NEW_AMZN_USED_PATH = join(DATA_DIR, 'raw_data_new_amzn_used.feather')


def get_unique_products():
    df = pd.read_feather(RAW_DATA_NEW_AMZN_USED_PATH,
                         usecols=['Product Name', 'ASIN', 'Keepa Link', 'Rating', '# of Reviews', 'Department',
                                  'Department Tree'], index_col=None)
    df_unique_products = df.drop_duplicates(subset=['ASIN'])

    num_of_products = len(df_unique_products)
    print(str(num_of_products) + " products detected!")

    df_unique_products.loc[:, 'Pricing Pattern'] = None
    return df_unique_products


def merge_prices(df):
    df_prices = df[['$ Amazon', '$ New FBA', '$ New FMA']]
    df['Prices'] = df_prices.min(axis=1)
    return df


def fill_null_values(df):
    # Forward filling
    df.fillna(method='ffill', inplace=True)
    return df


def remove_bad_products(filename):
    # Removes products with more than 50% null
    df = pd.read_feather(filename, index_col=None)
    unique_asins = df['ASIN'].unique()

    products_removed = 0

    for asin in unique_asins:
        product_df = df[df['ASIN'] == asin]
        no_price_point_count = 0
        for _, row in product_df.iterrows():
            amazon_price = row.get('$ Amazon')
            new_price = row.get('$ New')
            new_fba_price = row.get('$ New FBA')
            new_fma_price = row.get('$ New FMA')

            if pd.isna(amazon_price) and pd.isna(new_price) and pd.isna(new_fba_price) and pd.isna(new_fma_price):
                no_price_point_count += 1

        total_price_points = len(product_df)
        fraction_none = no_price_point_count / total_price_points

        if fraction_none >= 0.5:
            df = df[df['ASIN'] != asin]
            products_removed += 1

    df.to_feather(filename, mode='w', index=False, header=True, compression='zstd')
    print('Products removed: ', products_removed)


def map_pricing_patterns_to_numbers(df):
    df_numerical_pricing_patterns = df.loc[df["Pricing Pattern"] != 'BAD']

    # Map pricing patterns to numerical values
    pricing_pattern_mapping = {'Flat': 0, 'Trendy': 1, 'Rangebound': 2, 'Spiky': 3, 'Wavy': 4, 'Moving Average': 5}
    df_numerical_pricing_patterns["Numerical Pricing Pattern"] = df_numerical_pricing_patterns["Pricing Pattern"].map(
        pricing_pattern_mapping)

    return df_numerical_pricing_patterns


def assign_category_values(df):
    df["dpt list"] = df["Department Tree"].str.split(" > ")
    dpt_by_level = {}
    for dpt_levels in df["dpt list"]:
        for i, l in enumerate(dpt_levels):
            s = dpt_by_level.get(i, set())
            s.add(l)
            dpt_by_level[i] = s
    dpt_by_level_numerical = {}
    for digit, value in dpt_by_level.items():
        value = sorted(value)
        dpt_by_level_numerical[digit] = dict((item, value.index(item)) for item in value)
    base = max([len(v) for v in dpt_by_level.values()])
    dpt_num_values = []
    for dpt_levels in df["dpt list"]:
        num_value = 0
        for i, l in enumerate(dpt_levels):
            num_value += num_value * base + dpt_by_level_numerical[i][l]
        dpt_num_values.append(num_value)
    df["Department Num Value"] = dpt_num_values
    return df


def clean_raw_data(file):
    df_og = pd.read_feather(file)
    df_merged = merge_prices(df_og)
    df_filled = fill_null_values(df_merged)

    return df_filled


def truncate_data(df):
    df.sort_values(by=['ASIN', 'Date'], inplace=True)
    df_truncated = df.groupby('ASIN').tail(900)
