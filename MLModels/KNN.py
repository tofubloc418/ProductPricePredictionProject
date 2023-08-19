import assign_category_values

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
from sklearn.neighbors import KNeighborsClassifier

# Get data
df = assign_category_values.run()

# Split data into training and test set
X = df[["Rating", "# of Reviews", "Department Num Value"]]
y = df["Product Type"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=True, random_state=42)

# Scale features
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# Run KNN
num_neighbors = 5

knn = KNeighborsClassifier(n_neighbors=num_neighbors)
knn.fit(X_train, y_train)

# Predict using test data
y_pred = knn.predict(X_test)

# Calculate model accuracy
accuracy = accuracy_score(y_test, y_pred)
print(f"Accuracy: {accuracy:.2f}")
