"""
Model Retraining Script - Fixed scaler bug
Bug: X_test_scaled = scaler.fit_transform(X_test)  -- WRONG
Fix: X_test_scaled = scaler.transform(X_test)       -- CORRECT
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, classification_report
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

print("="*60)
print("Heart Disease Model - Retraining with Fixed Scaler")
print("="*60)

# --- 1. Load Data ---
df = pd.read_csv(os.path.join(ROOT_DIR, 'heart.csv'))
print(f"\n[OK] Data loaded: {df.shape[0]} rows, {df.shape[1]} columns")
print(f"     Target distribution:\n{df['HeartDisease'].value_counts().to_string()}")

# --- 2. Preprocessing (One-Hot Encoding) ---
df_encoded = pd.get_dummies(df, columns=['Sex', 'ChestPainType', 'RestingECG', 'ExerciseAngina', 'ST_Slope'], drop_first=False)

X = df_encoded.drop('HeartDisease', axis=1)
y = df_encoded['HeartDisease']

# Exact columns that app.py expects
expected_cols = [
    'Age', 'RestingBP', 'Cholesterol', 'FastingBS', 'MaxHR', 'Oldpeak',
    'Sex_M', 'ChestPainType_ATA', 'ChestPainType_NAP', 'ChestPainType_TA',
    'RestingECG_Normal', 'RestingECG_ST', 'ExerciseAngina_Y',
    'ST_Slope_Flat', 'ST_Slope_Up'
]

# Add any missing cols as 0
for col in expected_cols:
    if col not in X.columns:
        print(f"     [WARN] Missing column added as 0: {col}")
        X[col] = 0

X = X[expected_cols]
print(f"\n[OK] Features: {list(X.columns)}")

# --- 3. Train/Test Split ---
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"[OK] Split: {len(X_train)} train, {len(X_test)} test")

# --- 4. FIXED Scaler ---
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)   # fit ONLY on train data
X_test_scaled  = scaler.transform(X_test)         # CORRECT: only transform test

print("[OK] Scaler fitted on TRAINING data only (bug FIXED)")

# --- 5. Find Best K and Train Model ---
print("\n[..] Finding best K for KNN...")
best_k, best_acc = 1, 0
for k in range(1, 21):
    knn = KNeighborsClassifier(n_neighbors=k)
    knn.fit(X_train_scaled, y_train)
    acc = accuracy_score(y_test, knn.predict(X_test_scaled))
    if acc > best_acc:
        best_acc, best_k = acc, k

print(f"     Best K = {best_k}, Test Accuracy = {best_acc*100:.2f}%")

model = KNeighborsClassifier(n_neighbors=best_k)
model.fit(X_train_scaled, y_train)

# --- 6. Evaluate ---
y_pred = model.predict(X_test_scaled)
accuracy = accuracy_score(y_test, y_pred)
print(f"[OK] Final Accuracy: {accuracy*100:.2f}%")
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# --- 7. Sanity Check ---
print("\n--- SANITY CHECK ---")

# Healthy 25 year old female (LOW RISK expected)
healthy = pd.DataFrame([{
    'Age': 25, 'RestingBP': 110, 'Cholesterol': 160, 'FastingBS': 0,
    'MaxHR': 175, 'Oldpeak': 0.0, 'Sex_M': 0,
    'ChestPainType_ATA': 1, 'ChestPainType_NAP': 0, 'ChestPainType_TA': 0,
    'RestingECG_Normal': 1, 'RestingECG_ST': 0,
    'ExerciseAngina_Y': 0, 'ST_Slope_Flat': 0, 'ST_Slope_Up': 1
}])
h_scaled = scaler.transform(healthy)
h_pred = model.predict(h_scaled)[0]
h_prob = model.predict_proba(h_scaled)[0][1] * 100
status = "PASS - LOW RISK" if h_pred == 0 else "FAIL - wrongly HIGH RISK"
print(f"  Healthy 25F  => Prediction={h_pred}, Prob={h_prob:.1f}%  [{status}]")

# Sick 65 year old male (HIGH RISK expected)
sick = pd.DataFrame([{
    'Age': 65, 'RestingBP': 180, 'Cholesterol': 300, 'FastingBS': 1,
    'MaxHR': 90, 'Oldpeak': 3.5, 'Sex_M': 1,
    'ChestPainType_ATA': 0, 'ChestPainType_NAP': 0, 'ChestPainType_TA': 0,
    'RestingECG_Normal': 0, 'RestingECG_ST': 1,
    'ExerciseAngina_Y': 1, 'ST_Slope_Flat': 1, 'ST_Slope_Up': 0
}])
s_scaled = scaler.transform(sick)
s_pred = model.predict(s_scaled)[0]
s_prob = model.predict_proba(s_scaled)[0][1] * 100
status = "PASS - HIGH RISK" if s_pred == 1 else "FAIL - wrongly LOW RISK"
print(f"  Sick 65M     => Prediction={s_pred}, Prob={s_prob:.1f}%  [{status}]")

# --- 8. Save Models ---
joblib.dump(model,         os.path.join(ROOT_DIR, 'KNN_heart.pkl'))
joblib.dump(scaler,        os.path.join(ROOT_DIR, 'scaler.pkl'))
joblib.dump(expected_cols, os.path.join(ROOT_DIR, 'columns.pkl'))

print("\n[SAVED] KNN_heart.pkl")
print("[SAVED] scaler.pkl")
print("[SAVED] columns.pkl")
print("\n" + "="*60)
print("DONE! Retrain complete. Now push to GitHub for Vercel deploy.")
print("="*60)
