import pandas as pd

from ARIMAForecaster import percentile_band_forecast
from ARIMAForecaster.utils import cached_get_clean_raw_data, ppdf, collect_results
from DataProcessors.parse_raw_data import RAW_DATA_PATH


def summarize_product_results(df_product, asin_to_name):
    """
    prediction is considered successful if:
        prediction curve is touched
        touched price is below avg of all prices during the test duration


    """
    summaries = []
    asin = df_product["asin"].unique()[0]
    name = asin_to_name[asin]
    for forecast_days, df_forecast in df_product.groupby("forecast_days"):
        df_saved = df_forecast[(df_forecast["forecast discount vs avg"] > 0)]
        success_rate = len(df_saved) / len(df_forecast)
        avg_forecast_discount = df_forecast["forecast discount vs avg"].mean()
        avg_actual_discount = df_forecast["actual discount vs avg"].mean()
        summary = {"ASIN": asin,
                   "Product Name": name,
                   "forecast_days": forecast_days,
                   "success rate": success_rate,
                   "average forecast discount": avg_forecast_discount,
                   "average actual discount": avg_actual_discount,
                   }
        summaries.append(summary)
    return summaries


def collect_summarized_results(module):
    df_raw = cached_get_clean_raw_data(RAW_DATA_PATH)
    df_asin_name = df_raw[["ASIN", "Product Name"]].drop_duplicates()
    asin_to_name = dict(zip(df_asin_name["ASIN"].values, df_asin_name["Product Name"].values))

    all_summary = []
    all_product_results = collect_results(module)
    for df_product in all_product_results:
        summaries = summarize_product_results(df_product, asin_to_name)
        all_summary += summaries

    df_all = pd.DataFrame(all_summary)
    return df_all


if __name__ == '__main__':
    df = collect_summarized_results(percentile_band_forecast)
    print(ppdf(df.groupby(["forecast_days", "type by success rate"]).describe()))
