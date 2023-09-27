import numpy as np
import pandas as pd
from pandas import Series
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from tsai.models.MINIROCKET import MiniRocketClassifier

from DataProcessors.processor_scripts import get_minirocket_test_data


def convert_x(X):
    """
    https://www.sktime.net/en/v0.20.1/examples/02_classification.html
    need to convert my data into same format as example
    here X_train has only one column
    each cell contains a series wrapping another series of actual data
    """
    converted = [Series(Series(r)) for r in X]
    return pd.DataFrame({"prices": converted})


def minirocket_test(df):
    # Get data
    X = df.iloc[:, 1:-1].to_numpy()
    y = df['Pricing Pattern'].to_numpy()

    # Convert string labels to integers
    encoder = LabelEncoder()
    y_encoder = encoder.fit_transform(y)

    # Reshape the y to a 1 by 1 matrix
    y_encoder = np.reshape(y_encoder, (-1, 1))

    # Split the data into train and test
    X_train, X_valid, y_train, y_valid = train_test_split(X, y_encoder, test_size=0.25, random_state=42)
    X_train = convert_x(X_train)
    X_valid = convert_x(X_valid)

    # Transform data with MiniRocket
    # minirocket = MiniRocket()  # MiniRocket instance
    # minirocket.fit(X_train)
    # X_train_transformed = minirocket.transform(X_train)
    # X_test_transformed = minirocket.transform(X_test)
    minirocketClassifier = MiniRocketClassifier()
    minirocketClassifier.fit(X_train, y_train)
    print(f'valid accuracy    : {minirocketClassifier.score(X_valid, y_valid):.3%}')

    # Classify using RidgeClassifier
    # classifier = RidgeClassifierCV(alphas=np.logspace(-6, 6, 13))
    # classifier.fit(X_train_transformed, y_train)  # CODE BREAKS HERE | FOCUS ON THE X THAT THE MINIROCKET TRANSFORMED
    # y_pred = classifier.predict(X_test_transformed)
    # accuracy = accuracy_score(y_test, y_pred)
    # print(f"Accuracy: {accuracy * 100:.2f}%")


if __name__ == "__main__":
    df_minirocket_test = get_minirocket_test_data(use_cache=True)
    minirocket_test(df_minirocket_test)
