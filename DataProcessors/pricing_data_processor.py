from os.path import join

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from Data import DATA_DIR
from DataProcessors.parse_raw_data import merge_prices

RAW_DATA_NEW_AMZN_USED_PATH = join(DATA_DIR, 'raw_data_new_amzn_used.feather')


def get_product_data(file, asin):
    df = pd.read_feather(file)
    product_df = df[df['ASIN'] == asin]
    if product_df.empty:
        print(f"ERROR: {asin} found no product.")
    return product_df


def calculate_delta_median(df):
    df['Date'] = pd.to_datetime(df['Date'])

    latest_3_months_median = np.nan
    latest_date = df['Date'].max()
    while pd.isna(latest_3_months_median):
        target_three_months_ago = latest_date - pd.DateOffset(months=3)
        df['Date Difference'] = abs(df['Date'] - target_three_months_ago)
        idx = df['Date Difference'].idxmin()
        actual_three_months_ago = df.loc[idx]['Date']
        latest_3_months_data = df[(df['Date'] >= actual_three_months_ago) & (df['Date'] <= latest_date)]
        latest_3_months_median = latest_3_months_data['Final Price'].median(skipna=True)
        latest_date -= pd.DateOffset(days=1)
    print(latest_3_months_median)

    earliest_3_months_median = np.nan
    earliest_date = df['Date'].min()
    while pd.isna(earliest_3_months_median):
        target_three_months_later = earliest_date + pd.DateOffset(months=3)
        df['Date Difference'] = abs(df['Date'] - target_three_months_later)
        actual_three_months_later = df.loc[df['Date Difference'].idxmin()]['Date']
        earliest_3_months_data = df[(df['Date'] <= actual_three_months_later) & (df['Date'] >= earliest_date)]
        earliest_3_months_median = earliest_3_months_data['Final Price'].median(skipna=True)
        earliest_date += pd.DateOffset(days=1)
    print(earliest_3_months_median)

    delta_median = latest_3_months_median - earliest_3_months_median
    print(delta_median)

    return delta_median


def calculate_standard_deviation(df):
    standard_deviation = df['Final Price'].std()
    return standard_deviation


def visualize_data(df):
    product_name = df.iloc[1]['Product Name']
    plt.figure(figsize=(25, 10))  # Set the figure size
    plt.plot(df['Date'], df['Final Price'], label='Price', color='blue')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.title(product_name)
    plt.legend()
    plt.grid(True)
    plt.show()


def run(asin):
    df = get_product_data(RAW_DATA_NEW_AMZN_USED_PATH, asin)
    merged_prices_df = merge_prices(df)

    delta_median = calculate_delta_median(merged_prices_df)
    standard_deviation = calculate_standard_deviation(merged_prices_df)

    return merged_prices_df, delta_median, standard_deviation


def add_stats_data(df):
    for index, row in df.iterrows():
        print(f'Adding stats to {row["Product Name"]}')
        product_asin = row['ASIN']
        _, delta_median, std = run(product_asin)
        df.at[index, 'Delta Median'] = delta_median
        df.at[index, 'Standard Deviation'] = std

    return df
