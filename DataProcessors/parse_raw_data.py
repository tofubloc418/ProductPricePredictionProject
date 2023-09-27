import datetime
from os.path import join
from pprint import pprint

import pandas as pd

from Data import DATA_DIR

CUTOFF_DATE = datetime.datetime(2023, 8, 1) - datetime.timedelta(days=5 * 365)

UNIQUE_PRODUCTS_WITH_FEATURES_PATH = join(DATA_DIR, 'unique_products_with_features.feather')
UNIQUE_PRODUCTS_WITH_FEATURES_TEMP_PATH = join(DATA_DIR, 'unique_products_with_features_temp.feather')
LABELED_PRODUCTS_PATH = join(DATA_DIR, 'labeled_products.feather')
RAW_DATA_NEW_AMZN_USED_PATH = join(DATA_DIR, 'raw_data_new_amzn_used.feather')
RAW_DATA_PATH = join(DATA_DIR, 'raw_data.feather')


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


def general_clean_data(df):
    # Remove rows with duplicate dates
    df = df.drop_duplicates(subset=['Date']).copy()

    # Convert date column to datetime
    df['Date'] = pd.to_datetime(df['Date'])
    return df


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


def truncate_data(df):
    df.sort_values(by=['ASIN', 'Date'], inplace=True)
    df_truncated = df.groupby('ASIN').tail(900)
    return df_truncated


def scale_data(df):
    # Initialize an empty DataFrame to store the resampled data
    resampled_df = pd.DataFrame()

    # Number of samples = num of days in 5 years
    num_samples = 365 * 5  # Not accounting for leap years

    # List of unique products in the dataframe
    products = df['ASIN'].unique()

    progress_count = 0
    total_count = len(products)

    for product in products:
        print(product)
        product_data = df[df['ASIN'] == product]

        # Sort the product data based on date
        product_data = product_data.sort_values('Date')

        # Set the date as the index for resampling
        product_data.set_index('Date', inplace=True)

        # Calculate the target frequency
        total_seconds = (product_data.index[-1] - product_data.index[0]).total_seconds()
        target_freq = total_seconds / num_samples

        # Resample based on the target frequency
        resampled_data = product_data.resample(f"{int(target_freq)}S").ffill()

        # Reset index and append the resampled data to the new dataframe
        resampled_data.reset_index(inplace=True)
        resampled_df = pd.concat([resampled_df, resampled_data])

        progress_count += 1

        print(f"{progress_count} / {total_count} resampled!!!")

    # Pivot the data
    columns = ['ASIN', 'Date', 'Prices']
    resampled_df = resampled_df[columns]
    resampled_df = resampled_df.dropna(subset='ASIN')
    resampled_df['sequence'] = resampled_df.groupby('ASIN').cumcount() + 1
    pivoted_df = resampled_df.pivot(index='ASIN', columns='sequence', values='Prices')

    # Last fill checks and reset index
    pivoted_df = pivoted_df.ffill(axis=1).bfill(axis=1)
    pivoted_df.reset_index()

    return pivoted_df


def detect_excessive_gap(df, max_gap):
    df = df.sort_index()
    df = df[df.index > CUTOFF_DATE]
    last_ts = df.index[0]
    big_gaps = []
    for ts in df.index:
        gap = abs(ts - last_ts)
        if gap > max_gap:
            big_gaps.append((last_ts, ts, gap.days))
        last_ts = ts
    if big_gaps:
        label = pd.unique(df[["ASIN", "Product Name"]].values.ravel('K'))
        print(f"{label} has gaps at:")
        pprint(big_gaps)
        # plot(df, str(df["Product Name"].unique()))
        return True
    return False


def detect_short_duration(df, years):
    df = df.sort_index()
    duration = df.index[-1] - df.index[0]
    if duration < datetime.timedelta(days=years * 365.5):
        label = pd.unique(df[["ASIN", "Product Name"]].values.ravel('K'))
        print(f"{label} has total {duration.days} days of data")
        return True
    return False


def detect_bad_products(df):
    bad_products = []
    big_gap = 0
    short_duration = 0
    big_gap_days = 120
    min_duration_years = 2
    total = len(df["ASIN"].unique())
    for asin, df_product in df.groupby("ASIN"):
        df_product = df_product.dropna(subset=['Prices'])
        df_plot = df_product.set_index("Date")
        try:
            if detect_excessive_gap(df_plot, max_gap=datetime.timedelta(days=big_gap_days)):
                big_gap += 1
                bad_products.append(asin)
            if detect_short_duration(df_plot, years=min_duration_years):
                short_duration += 1
                bad_products.append(asin)
        except IndexError:
            bad_products.append(asin)

    print(f"found {big_gap} / {total} have day gap longer than {big_gap_days} days")
    print(f"found {short_duration} / {total} have duration shorter than {min_duration_years} years")

    return bad_products


def remove_bad_products(df, bad_products):
    df = df[~df['ASIN'].isin(bad_products)]

    return df


def clean_raw_data(file):
    df_og = pd.read_feather(file)
    df_merged = merge_prices(df_og)
    df_cleaned = general_clean_data(df_merged)
    bad_products = detect_bad_products(df_cleaned)
    df_no_bad_products = remove_bad_products(df_cleaned, bad_products)

    return df_no_bad_products
