import math

from DataProcessors import parse_raw_data

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
from sklearn.neighbors import KNeighborsClassifier


def knn_test(df):
    # Split data into training and test set
    X = df[["Rating", "# of Reviews", "Department Num Value", "Delta Median", "Standard Deviation"]]
    y = df["Pricing Pattern"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, shuffle=True, random_state=42)

    # Scale features
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    # Run KNN
    num_neighbors = int(math.sqrt(len(X_train)))
    knn = KNeighborsClassifier(n_neighbors=num_neighbors)
    knn.fit(X_train, y_train)

    # Predict using test data
    y_pred = knn.predict(X_test)

    # Calculate model accuracy
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Square root of total points accuracy: {accuracy:.2f}")
    for i in range(1, len(X_train)):
        # KNN with k = i
        knn = KNeighborsClassifier(n_neighbors=i)
        knn.fit(X_train, y_train)

        # Predict using test data
        y_pred = knn.predict(X_test)

        # Calculate model accuracy
        accuracy = accuracy_score(y_test, y_pred)
        print(f"{i} : {accuracy:.2f}")


def run():
    training_df = parse_raw_data.get_training_data()

    knn_test(training_df)


run()
