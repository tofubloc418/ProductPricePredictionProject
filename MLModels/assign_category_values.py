import pandas as pd
import random
import generate_fake_data

random.seed(42)  # For consistency


def get_unique_products():
    df = pd.read_csv(r'C:\Users\Brandon\PycharmProjects\ProductPricePredictionProject\Data\raw_data.csv',
                     usecols=['Product Name', 'ASIN', 'Keepa Link', 'Rating', '# of Reviews', 'Department', 'Department Tree'])
    df_no_dupes = df.drop_duplicates(subset=['ASIN'])

    num_of_products = len(df_no_dupes)
    print(str(num_of_products) + " products detected!")

    # Generate random product types
    product_types = []
    for i in range(num_of_products):
        product_types.append(random.randint(0, 3))

    df_no_dupes.loc[:, 'Pricing Pattern'] = product_types
    df_no_dupes.to_csv(r'C:\Users\Brandon\PycharmProjects\ProductPricePredictionProject\Data\knn_data.csv'
                       , mode='a', index=False, header=False)
    return df_no_dupes


def assign_value(df):
    df["dpt list"] = df["Department Tree"].str.split(" > ")
    dpt_by_level = {}
    for dpt_levels in df["dpt list"]:
        for i, l in enumerate(dpt_levels):
            s = dpt_by_level.get(i, set())
            s.add(l)
            dpt_by_level[i] = s
    dpt_by_level_numerical = {}
    for digit, value in dpt_by_level.items():
        value = sorted(value)
        dpt_by_level_numerical[digit] = dict((item, value.index(item)) for item in value)
    base = max([len(v) for v in dpt_by_level.values()])
    dpt_num_values = []
    for dpt_levels in df["dpt list"]:
        num_value = 0
        for i, l in enumerate(dpt_levels):
            num_value += num_value * base + dpt_by_level_numerical[i][l]
        dpt_num_values.append(num_value)
    df["Department Num Value"] = dpt_num_values
    return df


def run():
    initial_df = get_unique_products()
    df = assign_value(initial_df)
    return df
