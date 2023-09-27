import os
import traceback
from functools import cache
from os import listdir
from os.path import getsize, isdir, join
from pathlib import Path

import pandas as pd
from tabulate import tabulate

from DataProcessors.parse_raw_data import merge_prices, general_clean_data, RAW_DATA_PATH


def ppdf(df):
    return tabulate(df, headers='keys', tablefmt='psql')


def get_clean_raw_data(file):
    df_og = pd.read_feather(file)
    df_merged = merge_prices(df_og)
    df_filled = general_clean_data(df_merged)
    return df_filled


def cleanup_per_product_data(df):
    df.set_index("Date", inplace=True)
    df = df.sort_index()
    df = df.dropna(subset=["Prices"])
    # df = df[df.index > CUTOFF_DATE]
    df = df[["Prices"]].resample("1D").ffill().dropna()
    return df


@cache
def cached_get_clean_raw_data(file):
    return get_clean_raw_data(file)


@cache
def cached_get_clean_per_product_data(asin):
    return get_clean_per_product_data(asin)


def get_clean_per_product_data(asin):
    df_cleaned = cached_get_clean_raw_data(RAW_DATA_PATH)
    df_product = df_cleaned[df_cleaned["ASIN"] == asin]
    if df_product.empty:
        raise Exception(f"{asin} not found in df_cleaned of {df_cleaned.shape}")
    df_sorted = cleanup_per_product_data(df_product)
    return df_sorted


def get_assigned_asins(index_range):
    unique_asins = get_all_asins_sorted()
    start_idx, end_idx = index_range
    end_idx = len(unique_asins) if end_idx is None else end_idx
    assigned_asins = unique_asins[start_idx: end_idx]
    return assigned_asins


def get_all_asins_sorted():
    df_cleaned = cached_get_clean_raw_data(RAW_DATA_PATH)
    unique_asins = sorted(df_cleaned["ASIN"].unique())
    return unique_asins


def get_folder_size(folder_path):
    return sum(getsize(file) for file in Path(folder_path).rglob('*'))


def get_sub_folder_sizes(folder_path):
    folder_sizes = [(f, get_folder_size(join(folder_path, f)) / 1e6) for f in listdir(folder_path) if
                    isdir(join(folder_path, f))]
    return pd.DataFrame(folder_sizes, columns=["folder", "size MB"])


def log_exception_1line():
    trace = traceback.format_exc()
    src_line = trace.split('\n')[1].lstrip()
    return src_line


def get_product_result_file_path(asin, log_dir):
    return join(log_dir, asin, "result.feather")


def collect_results(module):
    results = []
    log_dir = module.LOG_DIR
    for asin in os.listdir(log_dir):
        result_df_path = get_product_result_file_path(asin, log_dir)
        if os.path.exists(result_df_path):
            try:
                df_result = pd.read_feather(result_df_path)
                if not df_result.empty:
                    results.append(df_result)
            except BaseException as e:
                print(f"{asin} failed to read result.feather from {result_df_path} because {e}")
    return results
