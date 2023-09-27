import datetime

CUTOFF_DATE = datetime.datetime(2023, 8, 1) - datetime.timedelta(days=5 * 365)
LATEST_FIRST_DATE = datetime.datetime(2023, 8, 1) - datetime.timedelta(days=3 * 365)
NUM_OF_SAMPLES = 366  # try for 1 year
MIN_TRAINING_DAYS = 366
FORECAST_DAYS = [30, 90]
BAND_PERCENTILES = [0.1]
