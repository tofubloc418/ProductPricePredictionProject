import numpy as np
from sklearn.linear_model import RidgeClassifierCV
from sklearn.preprocessing import StandardScaler

from sktime.datasets import load_arrow_head  # univariate dataset
from sktime.transformations.panel.rocket import (
    MiniRocket,
)


def minirocket_test(df):
    # get data
    #

    minirocket = MiniRocket()
    minirocket.fit(X_train)
    X_train_transform = minirocket.transform(X_train)
    # test shape of transformed training data
    X_train_transform.shape

    scaler = StandardScaler(with_mean=False)
    classifier = RidgeClassifierCV(alphas=np.logspace(-3, 3, 10))

    X_train_scaled_transform = scaler.fit_transform(X_train_transform)
    classifier.fit(X_train_scaled_transform, y_train)

    X_test, y_test = load_arrow_head(split="test", return_X_y=True)
    X_test_transform = minirocket.transform(X_test)

    X_test_scaled_transform = scaler.transform(X_test_transform)
    classifier.score(X_test_scaled_transform, y_test)
