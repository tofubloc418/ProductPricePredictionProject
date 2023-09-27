import numpy as np
from sklearn.linear_model import RidgeClassifierCV
from sklearn.metrics import accuracy_score
from sktime.datasets import load_arrow_head  # Example dataset
from sktime.transformations.panel.rocket import MiniRocket


def run():
    X_train, y_train = load_arrow_head(split="train", return_X_y=True)
    X_test, y_test = load_arrow_head(split="test", return_X_y=True)
    # Initialize MiniRocket and transform data
    minirocket = MiniRocket()
    minirocket.fit(X_train)
    X_train_transform = minirocket.transform(X_train)
    X_test_transform = minirocket.transform(X_test)
    classifier = RidgeClassifierCV(alphas=np.logspace(-6, 6, 13))
    classifier.fit(X_train_transform, y_train)
    y_pred = classifier.predict(X_test_transform)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {accuracy:.3f}")


if __name__ == '__main__':
    run()
