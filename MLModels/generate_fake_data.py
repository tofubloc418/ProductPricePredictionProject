import pandas as pd
import random

random.seed(42)  # For consistency


def generate_data(num_products):
    data = []
    departments = [
        "Electronics > Computers & Tablets",
        "Home & Kitchen > Furniture",
        "Books > Fiction",
        "Health & Personal Care > Vitamins",
        "Toys & Games > Board Games",
        "Clothing, Shoes & Jewelry > Women",
        "Sports & Outdoors > Camping",
        "Electronics > Audio & Headphones",
        "Home & Kitchen > Cookware",
        "Books > Non-Fiction",
        # ... add more departments here ...
    ]

    for i in range(1, num_products + 1):
        product_id = i
        rating = round(random.uniform(3.5, 4.8), 1)
        num_reviews = random.randint(0, 80000)
        department = random.choice(departments)
        product_type = random.randint(0, 3)
        data.append([product_id, rating, num_reviews, department, product_type])

    return data


def run():
    data = generate_data(num_products=1000)

    # Creating a DataFrame and displaying all rows
    columns = ["Product ID", "Rating", "# of Reviews", "Department Tree", "Product Type"]
    df = pd.DataFrame(data, columns=columns)
    pd.set_option("display.max_rows", None)  # Display all rows
    print(df)
    return df
