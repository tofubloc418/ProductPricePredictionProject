from os.path import join

from Data import DATA_DIR
from DataProcessors.parse_raw_data import clean_raw_data

RAW_DATA_NEW_AMZN_USED_PATH = join(DATA_DIR, 'raw_data_new_amzn_used.feather')


def set_multi_indexed_data(df):
    df = df.sort_values(['ASIN', 'Date'])
    multi_indexed_data = df.set_index(['ASIN', 'Date'])['Final Price']

    print(multi_indexed_data.head(10))
    return multi_indexed_data


def get_minirocket_training_data():
    df_cleaned = clean_raw_data(RAW_DATA_NEW_AMZN_USED_PATH)


get_minirocket_training_data()
