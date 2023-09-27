import warnings

import numpy as np
import pandas as pd
import pmdarima

from ARIMAForecaster.plot_prices import plot_df_columns
from ARIMAForecaster.utils import cached_get_clean_raw_data, get_clean_per_product_data
from DataProcessors.parse_raw_data import RAW_DATA_PATH


def auto_arima_on_product(asin, percent_test=0.2):
    df_product = get_clean_per_product_data(asin)
    ts = df_product["Prices"]
    count = len(ts)
    test_index = int(percent_test * count)
    ts_train = ts[:-test_index]
    df_forecast = auto_arima_forecast(ts_train, ts.index)
    plot_df_columns(df_forecast, plot_title=f"{asin} using {auto_arima_forecast}", column_names=df_forecast.columns)


def is_ts_constant(ts, delta=1e-9):
    values = ts / delta
    values = np.round(values)
    values = values.astype("int64")
    return values.unique().shape == (1,)


def auto_arima_forecast(ts, forecast_duration):
    forecast_cutoff = ts.index[-1] - forecast_duration
    ts_train = ts[ts.index < forecast_cutoff]
    forecast_index = ts.index[ts.index >= forecast_cutoff]
    ts_test = ts[forecast_index]

    # Auto-ARIMA consistently has trouble with constant value products, so we forecast it with the latest historical price value
    if is_ts_constant(ts_train):
        value = ts_train.iloc[-1]
        ts_forecast = pd.Series(value, index=forecast_index)
    else:
        raw_len = len(ts_train)
        ts_train = ts_train.dropna()
        if len(ts_train) / raw_len < 0.5:
            print(f"Excessive NaN. Only retaining {len(ts_train) / raw_len * 100:0.2f}% of original data")
        auto_arima = pmdarima.auto_arima(ts_train,
                                         test='kpss',  # use adf test to find optimal 'd'
                                         start_p=0, start_q=0,
                                         max_p=100, max_q=100,  # maximum p and q
                                         stepwise=True,
                                         seasonal=False)
        ts_forecast = auto_arima.predict(n_periods=len(forecast_index))
        ts_forecast.index = forecast_index
    df_forecast = pd.DataFrame({"train": ts_train, "forecast": ts_forecast, "test": ts_test},
                               index=ts.index)
    return df_forecast


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    # df = run()
    # demo()
    df_cleaned = cached_get_clean_raw_data(RAW_DATA_PATH)
    for asin in df_cleaned["ASIN"].unique():
        # auto_arima_on_product("B0002YTLZY")
        auto_arima_on_product(asin)
