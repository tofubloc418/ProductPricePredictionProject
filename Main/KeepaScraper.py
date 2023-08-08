from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
import datetime as dt
import pandas as pd
import time


def parse_date(s_date, data_points_collected):
    year = '2023'
    date_split = s_date.split(' ')
    day_of_week = date_split[0]
    month = date_split[1]
    day = date_split[2]
    time = date_split[3]
    if len(day) < 2:
        day = '0' + day
    if len(time) < 5:
        time = '0' + time
    s_date = day_of_week + ' ' + month + ' ' + day + ', ' + year + ' ' + time
    date = dt.datetime.strptime(s_date, '%a, %b %d, %Y %H:%M').date()
    if date >= dt.date.today() and data_points_collected > 10:
        year = '2022'
        s_date = day_of_week + ' ' + month + ' ' + day + ', ' + year + ' ' + time
    date = dt.datetime.strptime(s_date, '%a, %b %d, %Y %H:%M')

    return date


def click_useless_lines(driver):
    amazon = driver.find_element(By.CSS_SELECTOR, 'td[data-type="0"]')
    amazon.click()
    used = driver.find_element(By.CSS_SELECTOR, 'td[data-type="2"]')
    used.click()
    buy_box = driver.find_element(By.CSS_SELECTOR, 'td[data-type="18"]')
    buy_box.click()
    warehouse = driver.find_element(By.CSS_SELECTOR, 'td[data-type="9"]')
    warehouse.click()


def check_click_year(driver):
    try:
        # Try for YEAR
        graph_range = driver.find_element(By.CSS_SELECTOR, 'td[range="8760"]')
    except NoSuchElementException:
        # Go for ALL
        graph_range = driver.find_elements(By.CSS_SELECTOR, '.legendRange')[-1]
        graph_range.click()
    graph_range.click()


def get_single_product_data(driver, link):
    # TEMPORARY DATA STORAGE
    data = [[], [], [], []]
    data_points_collected = 0

    # Open KEEPA page
    driver.get(link)
    wait = WebDriverWait(driver, 20)
    action = webdriver.ActionChains(driver)

    # Graph info
    time.sleep(2)
    graph = wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, 'canvas.flot-overlay')))
    name = (wait.until(ec.presence_of_element_located((By.CLASS_NAME, 'productTableDescriptionTitle'))).text
            .replace("  ", " | ").replace(" ", " | "))

    print(name)
    width = graph.size['width']

    # Set range to YEAR or ALL
    check_click_year(driver)

    # Move to right most part of graph
    action.move_to_element_with_offset(graph, width / 2 - 6, 0).perform()
    # TESTER
    # action.move_to_element_with_offset(graph, -500, 0).perform()

    # Set pace of cursor movement
    pace = -1
    while True:
        # Get the date
        s_date = driver.find_elements(By.ID, 'flotTipDate')[0].text

        # Split the date | Make day of month have 2 digits | Add year
        if s_date:
            date = parse_date(s_date, data_points_collected)
            s_date = dt.datetime.strftime(date, '%a, %b %d, %Y %H:%M')
        else:
            break

        # Get the price
        s_price = driver.find_element(By.ID, 'flotTip1').text

        # Split the price | Remove extra stuff
        price = float(s_price.split('$ ')[1]) if '$' in s_price else None

        # Add name, date, price to list
        if date in data[1] or price is None:
            pass
        else:
            data[0].append(name)
            data[1].append(link)
            data[2].append(date)
            data[3].append(price)
            print(s_date + ' | ' + str(price))
            data_points_collected += 1

        # Move cursor left
        action.move_by_offset(pace, 0).perform()

    print(data_points_collected)
    return data


def convert_to_df(department, data):
    df = pd.DataFrame({"Product Name": data[0], "Department": department, "Link": data[1], "Date": data[2], "Price": data[3]})
    return df


def get_single_product_data_df(driver, link, department):

    data = get_single_product_data(driver, link)
    df = convert_to_df(department, data)
    return df
