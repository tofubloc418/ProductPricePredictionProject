import multiprocessing
import os
import warnings
from datetime import timedelta
from multiprocessing import Pool
from os.path import join
from pathlib import Path

import numpy as np
import pandas as pd
from numpy import nan
from scipy import stats

from ARIMAForecaster.auto_arima import auto_arima_forecast
from ARIMAForecaster.constants import NUM_OF_SAMPLES, MIN_TRAINING_DAYS, FORECAST_DAYS, BAND_PERCENTILES
from ARIMAForecaster.plot_prices import save_df_column_plot
from ARIMAForecaster.utils import get_clean_per_product_data, set_loguru_level, \
    get_assigned_asins, log_exception_1line, get_product_result_file_path

FILE_DIR = os.path.dirname(os.path.realpath(__file__))
LOG_DIR = join(FILE_DIR, "percentile_band_auto_arima")

LOG_PROGRESS = False


def estimate_window_days(df, min_days, max_days, num_of_price_changes=4):
    """
    try to estimate a good rolling window based on how frequently prices change
    choosing a wider window since we are capturing bottoms which does not happen frequently
    """
    # convert to consecutively non-duplicate ts
    df_no_dup = df.loc[df.shift()["Prices"] != df["Prices"]]
    # a bit of guessing here as spot checking a few plots show 4 duration of 4 price changes is most versatile
    if len(df_no_dup) <= num_of_price_changes:
        return max_days
    day_counts = df_no_dup.index.to_series().diff(num_of_price_changes).dt.days.dropna()
    days = int(np.quantile(day_counts, 0.75))
    return min(max(days, min_days), max_days)


def percentile_band_auto_arima(ts_price, forecast_duration, band_percentile, band_window_days):
    """
    given historical prices and forecast duration, try to predict upper and lower band for future prices
    will use moving window to get upper band and lower band in the past
    bands will be defined as percentile from extreme.
    for example, band_percentile = 0.05 means we want the top & bottom 5% of price within each window
    """

    window = timedelta(days=band_window_days)

    def window_percentile(s_window):
        if len(s_window) >= window.days:
            return s_window.quantile(band_percentile)
        return nan

    # ts_lower_band = ts_price.rolling(window).apply(window_percentile).dropna()
    ts_lower_band = ts_price.rolling(window).apply(
        lambda s: s.quantile(band_percentile) if len(s) >= window.days else nan).dropna()
    df_lower_band_forecast = auto_arima_forecast(ts_lower_band, forecast_duration)
    df_combined = pd.DataFrame({"price": ts_price,
                                "lower train": df_lower_band_forecast["train"],
                                # "lower test": df_lower_band_forecast["test"],
                                "lower forecast": df_lower_band_forecast["forecast"],
                                },
                               index=ts_price.index)
    return df_combined


def eval_forecast(df, test_cutoff):
    df_test = df[df.index >= test_cutoff]
    result = {}
    is_touched = np.any(df_test["price"] <= df_test["lower forecast"])
    result["touched"] = is_touched
    if is_touched:
        # use first touched
        last_price_before_forecast = df["price"][df.index < test_cutoff][-1]
        avg_price = df_test["price"].mean()
        touched_forecast_price = df_test["lower forecast"][df_test["price"] <= df_test["lower forecast"]].iloc[0]
        touched_actual_price = df_test["price"][df_test["price"] <= df_test["lower forecast"]].iloc[0]

        result["forecast_percentile"] = stats.percentileofscore(df_test["price"], touched_forecast_price)
        result["actual_percentile"] = stats.percentileofscore(df_test["price"], touched_actual_price)
        if abs(avg_price) > 1e-9:
            result["forecast discount vs avg"] = 1 - touched_forecast_price / avg_price
            result["actual discount vs avg"] = 1 - touched_actual_price / avg_price
        if abs(last_price_before_forecast) > 1e-9:
            result["forecast discount vs start"] = 1 - touched_forecast_price / last_price_before_forecast
            result["actual discount vs start"] = 1 - touched_actual_price / last_price_before_forecast
    return result


def log_and_save_plot(asin, df, forecast_days, band_window_days, band_percentile=None, forecast_cutoff=None,
                      results=None,
                      num_of_samples=None):
    count = len(results)
    result = results[-1]
    try:
        title = f"{forecast_days}d rolling {band_window_days}d {round(band_percentile * 100)}pct"
        file_path = join(LOG_DIR, asin, title, f"{forecast_cutoff.date()}.jpg")
        save_df_column_plot(df, plot_title=f"{title} {asin}", file_path=file_path)
    except:
        print(f"failed to create chart on {forecast_cutoff.date()}")


def save_per_product_result_df(file_path, df):
    folder = os.path.dirname(file_path)
    Path(folder).mkdir(parents=True, exist_ok=True)
    df.to_feather(file_path)
    return file_path


def rolling_eval_percentile_band_auto_arima(asin, df_product_truncated, window, forecast_days, band_percentile,
                                            num_of_samples, band_window_days):
    results = []
    for df_window in df_product_truncated.rolling(window):
        if len(df_window) >= window.days:
            forecast_cutoff = df_window.index[-(forecast_days + 1)]
            try:
                df_combined = percentile_band_auto_arima(df_window["Prices"], timedelta(days=forecast_days),
                                                         band_percentile, band_window_days)
                result = eval_forecast(df_combined, forecast_cutoff)
                # result["forecast_cutoff"] = forecast_cutoff.date()
                result["forecast_days"] = forecast_days
                result["band_percentile"] = band_percentile
                results.append(result)

            except:
                pass

            else:
                if len(results) % 30 == 1:  # cannot log every day so just log 1st day of every month
                    log_and_save_plot(asin, df_combined, forecast_days, band_window_days, band_percentile,
                                      forecast_cutoff, results, num_of_samples)

    return results


def run_on_different_params(asin, num_of_samples, min_training_days, forecast_durations, band_percentiles):
    df_product = get_clean_per_product_data(asin)
    results = []
    if df_product.empty:
        raise Exception(f"{asin} data is empty")
    elif "Prices" not in df_product.columns:
        raise Exception(f"{asin} does not have Prices column!")
    else:
        try:
            for forecast_days in forecast_durations:
                print(f"*****  {asin} RUNNING forecast_days {forecast_days}")
                band_window_days = estimate_window_days(df_product, forecast_days * 2, int(min_training_days / 2))
                training_days = max(band_window_days, min_training_days)
                total_required_days = training_days + forecast_days + num_of_samples
                data_duration = df_product.index[-1] - df_product.index[0]
                if data_duration < timedelta(days=total_required_days):
                    raise Exception(
                        f"{asin}: avail data duration {data_duration.days} < "
                        f"{training_days}d+{forecast_days}d+{num_of_samples}d = {total_required_days}d total")
                cutoff_date = df_product.index[-1] - timedelta(days=total_required_days)
                df_product_truncated = df_product[df_product.index >= cutoff_date]
                window = timedelta(days=training_days + forecast_days)
                for band_percentile in band_percentiles:
                    results += rolling_eval_percentile_band_auto_arima(asin, df_product_truncated, window,
                                                                       forecast_days,
                                                                       band_percentile, num_of_samples,
                                                                       band_window_days)
        except BaseException as e:
            print(f"*****  {asin} skipped because {e} @ {log_exception_1line()}")
    df_result = pd.DataFrame(results)
    df_result["asin"] = asin
    return df_result


def run_per_product(asin):
    try:
        warnings.simplefilter("ignore")
        set_loguru_level("info")
        file_path = get_product_result_file_path(asin, LOG_DIR)
        if os.path.exists(file_path):
            df_result_asin = pd.read_feather(file_path)
            if df_result_asin.empty or \
                    "forecast_days" not in df_result_asin.columns or \
                    "band_percentile" not in df_result_asin.columns:
                msg = f"*****  {asin} skipped. it's EMPTY!"
            else:
                count_by_group = df_result_asin.groupby(["forecast_days", "band_percentile"])["asin"].count().to_dict()
                msg = f"*****  {asin} skipped. Collected {count_by_group} / {NUM_OF_SAMPLES} expected"
                for v in count_by_group.values():
                    if v < NUM_OF_SAMPLES / 2:
                        msg += " only!"
                        break
            print(msg.upper())
            return df_result_asin
        else:
            df_result_asin = run_on_different_params(asin, NUM_OF_SAMPLES, MIN_TRAINING_DAYS, FORECAST_DAYS,
                                                     BAND_PERCENTILES)
            save_per_product_result_df(file_path, df_result_asin)
            return df_result_asin
    except BaseException as e:
        print(f"*****  {asin} skipped because {e}")
        return pd.DataFrame()


def multi_process_run(index_range, num_processes=None, multiprocess=False):
    """
    make sure to run from terminal (not w/i pycharm)
    https://stackoverflow.com/a/71601871
    """
    unique_asins = get_assigned_asins(index_range)
    print(f"********    RUNNING ON {unique_asins[0]} ~ {unique_asins[-1]}    **********")
    all_results = []
    if multiprocess:
        with Pool(num_processes) as pool:
            all_results = pool.map(run_per_product, unique_asins)
    else:
        for asin in unique_asins:
            all_results.append(run_per_product(asin))
    df_all = pd.concat(all_results)
    print(f"********    RESULT DF HAS {df_all['asin'].unique()} UNIQUE ASINS    **********")
    return df_all


IDX_SPLIT = [(0, 300),
             (300, 600),
             (600, None)]

if __name__ == "__main__":
    """
    Multiprocess must run outside of pycharm in a conda/mamba shell:
    
    mamba activate py310ml
    cd C:\%HOMEPATH%\PycharmProjects\pppp_arima_only
    python -m ARIMAForecaster.percentile_band_forecast
    """
    warnings.simplefilter("ignore")
    cores_used = int(multiprocessing.cpu_count() / 3)
    print(f"Have {multiprocessing.cpu_count()} cores and using {cores_used} processes")

    df_all = multi_process_run(index_range=IDX_SPLIT[2], num_processes=cores_used, multiprocess=True)
