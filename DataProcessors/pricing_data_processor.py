import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


RAW_DATA_NEW_AMZN_USED_PATH = r'C:\Users\Brandon\PycharmProjects\ProductPricePredictionProject\Data\raw_data_new_amzn_used.feather'


def get_product_data(file, asin):
    df = pd.read_feather(file)
    product_df = df[df['ASIN'] == asin]
    if product_df.empty:
        print(f"ERROR: {asin} found no product.")
    return product_df


def merge_price(df):
    final_prices = []

    for _, row in df.iterrows():
        amazon_price = row.get('$ Amazon')
        new_fba_price = row.get('$ New FBA')
        new_fma_price = row.get('$ New FMA')

        valid_prices = [price for price in [amazon_price, new_fba_price, new_fma_price] if price is not None]
        if valid_prices and not all(pd.isna(price) for price in valid_prices):
            final_price = min(valid_prices)
        else:
            final_price = None

        final_prices.append(final_price)

    df['Final Price'] = final_prices
    return df


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
    merged_prices_df = merge_price(df)

    delta_median = calculate_delta_median(merged_prices_df)
    standard_deviation = calculate_standard_deviation(merged_prices_df)

    return merged_prices_df, delta_median, standard_deviation
