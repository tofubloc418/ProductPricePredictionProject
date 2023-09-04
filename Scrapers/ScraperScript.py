import os
import random
import time
from os.path import join

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.firefox.options import Options

import AmazonScraper
from Data import DATA_DIR

RAW_DATA_PATH = join(DATA_DIR, 'raw_data.feather')


class TooLittleDataException(Exception):
    """Raised when the number of days is less than 800"""
    pass


random.seed(42)
new_fba_clicked = False
new_fma_clicked = False


def set_new_fba_clicked(new_value):
    global new_fba_clicked
    new_fba_clicked = new_value


def set_new_fma_clicked(new_value):
    global new_fma_clicked
    new_fma_clicked = new_value


def activate_driver():
    options = Options()
    options.add_argument('-headless')
    return webdriver.Firefox(options=options)


def run():
    from KeepaScraper import get_single_product_data_df
    driver = activate_driver()
    driver.maximize_window()
    try:
        product_info = AmazonScraper.compile_products(driver)
    except TimeoutException:
        driver.refresh()
        product_info = AmazonScraper.compile_products(driver)

    if os.path.exists(RAW_DATA_PATH):
        existing_df = pd.read_feather(RAW_DATA_PATH)
    else:
        existing_df = pd.DataFrame()

    existing_asins = existing_df["ASIN"].unique()

    total_products = len(product_info)
    products_finished_count = len(existing_asins)
    products_thrown_away_count = 0
    print("Products detected: " + str(products_finished_count))

    for product in random.sample(product_info, len(product_info)):
        department = product[0]
        asin = product[1]
        if asin not in existing_asins:
            try:
                df = get_single_product_data_df(driver, asin, department)

                existing_df = pd.concat([existing_df, df], ignore_index=True)
                existing_df.to_feather(RAW_DATA_PATH)

                products_finished_count += 1
                print(str(products_finished_count) + ' / ' + str(total_products) + " collected!\n")

                time.sleep(1)
            except TimeoutException:
                print("No data available")
                products_thrown_away_count += 1
                print(str(products_thrown_away_count), ' products thrown away!\n')
            except TooLittleDataException:
                print("Too little data!")
                products_thrown_away_count += 1
                print(str(products_thrown_away_count), ' products thrown away!\n')
            except ValueError:
                print("ValueError: Date out of bounds")
                products_thrown_away_count += 1
                print(str(products_thrown_away_count), ' products thrown away!\n')
            except StaleElementReferenceException:
                print("Stale Element error!")
                products_thrown_away_count += 1
                print(str(products_thrown_away_count), ' products thrown away!\n')

    print('All products completed.')
    driver.quit()


def test_run():
    from KeepaScraper import get_single_product_data_df

    driver = activate_driver()
    driver.maximize_window()
    get_single_product_data_df(driver, 'B08C1W5N87', 'test')


run()
# test_run()
