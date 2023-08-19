import time
import random

import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import KeepaScraper
import AmazonScraper
from selenium.common.exceptions import TimeoutException
from KeepaScraper import TooLittleDataException


def activate_driver():
    options = Options()
    options.add_argument('-headless')
    return webdriver.Firefox(options=options)


def run():
    driver = activate_driver()
    driver.maximize_window()
    try:
        product_info = AmazonScraper.compile_products(driver)
    except TimeoutException:
        driver.refresh()
        product_info = AmazonScraper.compile_products(driver)

    existing_df = pd.read_csv(r'C:\Users\Brandon\PycharmProjects\ProductPricePredictionProject\Data\raw_data.csv')
    existing_asins = existing_df["ASIN"].unique()

    total_products = len(product_info)
    products_finished_count = len(existing_asins)
    print("Products detected: " + str(products_finished_count))
    for product in random.sample(product_info, len(product_info)):
        department = product[0]
        asin = product[1]
        if asin not in existing_asins:
            try:
                df = KeepaScraper.get_single_product_data_df(driver, asin, department)
                df.to_csv(r'C:\Users\Brandon\PycharmProjects\ProductPricePredictionProject\Data\raw_data.csv'
                          , mode='a', index=False, header=False)

                products_finished_count += 1
                print(str(products_finished_count) + ' / ' + str(total_products) + " completed!\n")

                time.sleep(1)
            except TimeoutException:
                print("No data available\n")
                pass
            except TooLittleDataException:
                print("Too little data!\n")
                pass
            except ValueError:
                print("ValueError: Date out of bounds\n")
                pass

    driver.quit()


def test_run():
    driver = activate_driver()
    driver.maximize_window()
    KeepaScraper.get_single_product_data_df(driver, 'B08C1W5N87', 'test')


run()
# test_run()
