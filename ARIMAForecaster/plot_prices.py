import datetime
import os
from datetime import timedelta
from os.path import join
from pathlib import Path
from pprint import pprint

import pandas as pd
from matplotlib import pyplot as plt

from ARIMAForecaster.constants import CUTOFF_DATE
from Data import DATA_DIR
from DataProcessors.parse_raw_data import clean_raw_data

plt.ioff()


def run():
    df = clean_raw_data(join(DATA_DIR, "raw_data.feather"))
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.dropna(subset=["Prices"])
    big_gap = 0
    short_duration = 0
    total = len(df["ASIN"].unique())
    big_gap_days = 120
    min_duration_years = 3
    for id, df_product in df.groupby("ASIN"):
        df_plot = df_product.set_index("Date")
        # manual_scan(df_plot, count, total, bads)
        if detect_excessive_gap(df_plot, max_gap=timedelta(days=big_gap_days)):
            big_gap += 1
        if detect_short_duration(df_plot, years=min_duration_years):
            short_duration += 1
        # double_check(df_plot, count, total, [224, 327, 431, 535, 586, 587, 588, 589, 895, 1058], bads)
    print(f"found {big_gap} / {total} have day gap longer than {big_gap_days} days")
    print(f"found {short_duration} / {total} have duration shorter than {min_duration_years} years")


def double_check(df_plot, count, total, check_list, bads):
    if count in check_list:
        plot(df_plot, str(df_plot["Product Name"].unique()))
        good_or_bad = input(f"{count}/{total} Good(g) or Bad(b)?")
        if good_or_bad == "b":
            label = pd.unique(df_plot[["ASIN", "Product Name"]].values.ravel('K'))
            bads.append(label)
        elif good_or_bad == "q":
            raise Exception("User ended")


def manual_scan(df_plot, count, total, bads):
    plot(df_plot, str(df_plot["Product Name"].unique()))
    good_or_bad = input(f"{count}/{total} Good(g) or Bad(b)?")
    if good_or_bad == "b":
        label = pd.unique(df_plot[["ASIN", "Product Name"]].values.ravel('K'))
        bads.append(label)
    elif good_or_bad == "q":
        raise Exception("User ended")


def save_df_column_plot(df, plot_title, file_path, column_names=None, size=None):
    column_names = column_names or df.columns
    size = size or (15, 10)

    fig, ax = plt.subplots(1, figsize=size)
    for col in column_names:
        ax.plot(df.index, df[col], label=col)
    ax.legend(loc='upper left')
    ax.set_title(plot_title)
    folder = os.path.dirname(file_path)
    Path(folder).mkdir(parents=True, exist_ok=True)
    plt.savefig(file_path)


def plot_df_columns(df, plot_title, column_names=None, size=None, location=None):
    column_names = column_names or df.columns
    size = size or (15, 10)
    location = location or "+0+0"

    fig, ax = plt.subplots(1, figsize=size)
    for col in column_names:
        ax.plot(df.index, df[col], label=col)
    ax.legend(loc='upper left')
    ax.set_title(plot_title)

    fig_manager = plt.get_current_fig_manager()
    fig_manager.window.wm_geometry(location)
    plt.show()


def plot(df, description):
    fig, ax = plt.subplots(1, figsize=(15, 10))
    fig_manager = plt.get_current_fig_manager()
    fig_manager.window.wm_geometry("+0+0")
    x = df.index
    ax.scatter(x, df["Prices"], marker='.', s=1, color="blue", linewidths=0, label="Prices")
    #
    # plt.figure(figsize=(30, 15))
    # plt.plot(df.index, df['Prices'], "ro", label="Prices")
    plt.legend(loc='upper left')
    plt.title(description)
    plt.show()


def detect_short_duration(df, years):
    df = df.sort_index()
    duration = df.index[-1] - df.index[0]
    if duration < datetime.timedelta(days=years * 365.5):
        label = pd.unique(df[["ASIN", "Product Name"]].values.ravel('K'))
        print(f"{label} has total {duration.days} days of data")
        return True
    return False


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


if __name__ == "__main__":
    run()
