import time

import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import KeepaScraper
import AmazonScraper
from selenium.common.exceptions import TimeoutException


def activate_driver():
    options = Options()
    # options.add_argument('-headless')
    return webdriver.Firefox(options=options)


def run():
    driver = activate_driver()
    driver.maximize_window()
    try:
        product_links = AmazonScraper.compile_product_urls(driver)
    except TimeoutException:
        driver.refresh()
        product_links = AmazonScraper.compile_product_urls(driver)

    existing_df = pd.read_csv(r'C:\Users\Brandon\PycharmProjects\ProductPricePredictionProject\Data\raw_data.csv', index_col=0)
    existing_links = existing_df["Link"].unique()

    total_products = len(product_links)
    products_finished_count = len(existing_links)
    print("Products detected: " + str(products_finished_count))
    for product in product_links:
        department = product[0]
        link = product[1]
        if link not in existing_links:
            try:
                df = KeepaScraper.get_single_product_data_df(driver, link, department)
                df.to_csv(r'C:\Users\Brandon\PycharmProjects\ProductPricePredictionProject\Data\raw_data.csv'
                          , mode='a', index=False, header=False)

                products_finished_count += 1
                print(str(products_finished_count) + ' / ' + str(total_products) + " completed!")

                time.sleep(1)
            except TimeoutException:
                pass

    driver.quit()


def test_run():
    driver = activate_driver()
    driver.maximize_window()
    KeepaScraper.get_single_product_data_df(driver, 'https://keepa.com/#!product/1-B08C1W5N87', 'test')


run()
# test_run()
