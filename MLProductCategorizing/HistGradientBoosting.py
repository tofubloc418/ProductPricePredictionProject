from os.path import join

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from Data import DATA_DIR
from DataProcessors import parse_raw_data

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

CLASSIFICATION_TRAINING_DATA_WITH_PREDICTIONS_PATH = join(DATA_DIR, "classification_training_data_with_predictions.feather")


def save_predictions(df, filename):
    df_only_predictions = pd.DataFrame(columns=df.columns)

    for _, row in df.iterrows():
        if pd.notnull(row['Predicted Pricing Pattern']):
            df_only_predictions = pd.concat([df_only_predictions, row.to_frame().T], ignore_index=True)

    df_only_predictions.to_feather(filename, compression='zstd')


def hgb_test(df):
    # Split data into training and test set
    X = df[["Rating", "# of Reviews", "Department Num Value", "Delta Median", "Standard Deviation"]]
    y = df["Pricing Pattern"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    hgb = HistGradientBoostingClassifier(
        max_iter=1000,
        learning_rate=0.1,
        max_depth=3,
        random_state=42,
        verbose=0
    )
    # Train the classifier
    hgb.fit(X_train, y_train)
    # Make predictions
    y_pred = hgb.predict(X_test)
    # Evaluate the model's performance
    accuracy = accuracy_score(y_test, y_pred)
    print("Accuracy:", accuracy)

    # Save predictions to dataframe
    df.loc[X_test.index, 'Predicted Pricing Pattern'] = y_pred

    return df


def kmeans_and_hgb_test(df):

    X = df[["Rating", "# of Reviews", "Department Num Value", "Delta Median", "Standard Deviation"]]
    y = df["Pricing Pattern"]

    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Apply k-means clustering
    n_clusters = 3
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    cluster_labels_train = kmeans.fit_predict(X_train)
    cluster_labels_test = kmeans.predict(X_test)

    # Store classifiers for each cluster
    cluster_classifiers = {}

    # Train a classifier for each cluster
    for cluster_id in range(n_clusters):
        # Filter data points belonging to the current cluster
        cluster_mask_train = cluster_labels_train == cluster_id

        if np.any(cluster_mask_train):
            # Train a classifier on the data points within the current cluster
            classifier = HistGradientBoostingClassifier(max_iter=100)
            classifier.fit(X_train[cluster_mask_train], y_train[cluster_mask_train])

            # Store the trained classifier for the current cluster
            cluster_classifiers[cluster_id] = classifier

    # Make predictions using the cluster-specific classifiers
    cluster_predictions = np.zeros_like(y_test)
    for cluster_id, classifier in cluster_classifiers.items():
        cluster_mask = cluster_labels_test == cluster_id
        cluster_predictions[cluster_mask] = classifier.predict(X_test[cluster_mask])

    # Evaluate the overall accuracy
    accuracy = accuracy_score(y_test, cluster_predictions)
    print(f"Accuracy: {accuracy:.2f}")


def kmeans_test(df):
    X = df[["Rating", "# of Reviews", "Department Num Value", "Delta Median", "Standard Deviation"]]
    y = df["Pricing Pattern"]

    scaler = StandardScaler()
    X_normalized = scaler.fit_transform(X)

    n_clusters = 3
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    cluster_labels = kmeans.fit_predict(X_normalized)

    cluster_df = pd.DataFrame({"Cluster": cluster_labels, "Pricing Pattern": y})
    print(cluster_df)


def run():
    training_df = parse_raw_data.get_training_unique_products_data()

    df = hgb_test(training_df)
    save_predictions(df, CLASSIFICATION_TRAINING_DATA_WITH_PREDICTIONS_PATH)


run()
