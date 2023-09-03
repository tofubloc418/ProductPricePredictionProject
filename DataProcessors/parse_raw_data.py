import pandas as pd
from DataProcessors import pricing_data_processor

KNN_DATA_PATH = r'C:\Users\Brandon\PycharmProjects\ProductPricePredictionProject\Data\knn_data.feather'
KNN_DATA_TEMP_PATH = r'C:\Users\Brandon\PycharmProjects\ProductPricePredictionProject\Data\knn_data_temp.feather'
KNN_TRAINING_DATA_PATH = r'C:\Users\Brandon\PycharmProjects\ProductPricePredictionProject\Data\knn_training_data.feather'
RAW_DATA_NEW_AMZN_USED_PATH = r'C:\Users\Brandon\PycharmProjects\ProductPricePredictionProject\Data\raw_data_new_amzn_used.feather'


def get_unique_products():
    df = pd.read_feather(RAW_DATA_NEW_AMZN_USED_PATH,
                         usecols=['Product Name', 'ASIN', 'Keepa Link', 'Rating', '# of Reviews', 'Department',
                                  'Department Tree'], index_col=None)
    df_unique_products = df.drop_duplicates(subset=['ASIN'])

    num_of_products = len(df_unique_products)
    print(str(num_of_products) + " products detected!")

    df_unique_products.loc[:, 'Pricing Pattern'] = None
    return df_unique_products


def clean_raw_data(filename):
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


def add_stats_data(df):
    for index, row in df.iterrows():
        print(f'Adding stats to {row["Product Name"]}')
        product_asin = row['ASIN']
        _, delta_median, std = pricing_data_processor.run(product_asin)
        df.at[index, 'Delta Median'] = delta_median
        df.at[index, 'Standard Deviation'] = std

    return df


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


def get_new_data():
    knn_df = pd.read_feather(KNN_DATA_PATH)
    new_products_df = pd.DataFrame()
    for _, row in knn_df.iterrows():
        if row['Pricing Pattern'] is None:
            new_products_df = pd.concat([new_products_df, row.to_frame().T], ignore_index=True)
    new_products_df = assign_category_values(new_products_df)

    return new_products_df


def get_training_data():
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
