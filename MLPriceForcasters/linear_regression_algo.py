
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

import DataProcessors.processor_scripts
from DataProcessors import pricing_data_processor


def linear_regression_test(df):
    X = df[['Date']]  # Independent variable (time)
    y = df['Final Price']  # Dependent variable (price)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, shuffle=False)

    # Create a linear regression model
    lr = LinearRegression()

    # Fit the model to your data
    lr.fit(X_train, y_train)

    # Predict prices
    y_pred = lr.predict(X_test)

    # Calculate performance metrics
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)


def run_test():
    training_data = DataProcessors.processor_scripts.get_training_unique_products_data_for_classifiers()
    for _, product in training_data.iterrows():
        if product['Pricing Pattern'] == 'Flat' or product['Pricing Pattern'] == 'Trendy':
            asin = product['ASIN']
            df, _, _, = pricing_data_processor.run(asin)
            product_name = df.iloc[0]['Product Name']
            print('Performing linear regression on: ', product_name, '\n', asin)
            linear_regression_test(df)


run_test()
