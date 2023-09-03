from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from tsai.basics import *
import sktime
import sklearn

from tsai.models.MINIROCKET import *
from sktime.transformations.panel.rocket import MiniRocket


def mini_rocket_test(df):
    features = []

    for asin, group in df.groupby('ASIN'):
        X = group['Final Price'].values  # Extract price time series for the product
        X = X.reshape(1, -1)

        # Create and fit MiniRocket
        transformer = MiniRocket()
        X_features = transformer.fit_transform(X)

        features.append(X_features)

    # Stack features and labels
    X_all_features = np.vstack(features)
    y_all_labels = np.array(labels)

    # Split data into training and testing sets
    from sklearn.model_selection import train_test_split

    X_train, X_test, y_train, y_test = train_test_split(
        X_all_features, y_all_labels, test_size=0.2, random_state=42
    )

    # Create and train MiniRocketClassifier
    classifier = MiniRocketClassifier()
    classifier.fit(X_train, y_train)

    # Make predictions
    y_pred = classifier.predict(X_test)
