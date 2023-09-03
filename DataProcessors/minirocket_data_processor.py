import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


RAW_DATA_NEW_AMZN_USED_PATH = r'C:\Users\Brandon\PycharmProjects\ProductPricePredictionProject\Data\raw_data_new_amzn_used.feather'


def merge_price(df):
    final_prices = []

    for _, row in df.iterrows():
        amazon_price = row.get('$ Amazon')
        new_price = row.get('$ New')
        new_fba_price = row.get('$ New FBA')
        new_fma_price = row.get('$ New FMA')

        valid_prices = [price for price in [amazon_price, new_fba_price, new_fma_price] if price is not None]
        if valid_prices and not all(pd.isna(price) for price in valid_prices):
            final_price = min(valid_prices)
        elif new_price is not None:
            final_price = new_price
        else:
            final_price = None

        final_prices.append(final_price)

    df['Final Price'] = final_prices
    return df


def set_multi_indexed_data(df):
    df = df.sort_values(['ASIN', 'Date'])
    multi_indexed_data = df.set_index(['ASIN', 'Date'])['Final Price']

    print(multi_indexed_data.head(10))
    return multi_indexed_data


def run():
    df = pd.read_feather(RAW_DATA_NEW_AMZN_USED_PATH)
    df_merged_prices = merge_price(df)


run()
