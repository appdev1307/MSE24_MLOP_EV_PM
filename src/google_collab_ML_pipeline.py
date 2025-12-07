import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from xgboost import XGBClassifier
import lightgbm as lgb
from sklearn.model_selection import train_test_split
import joblib

DATA_PATH = "/content/drive/MyDrive/shared/EV_Predictive_Maintenance_Dataset_15min.csv"

# ===== LOAD DATA =====
df = pd.read_csv(DATA_PATH)

# 🔧 Select features
features = ["SoC", "Battery_Voltage", "Battery_Current", 
            "Motor_Temperature", "Speed", "Torque", 
            "Odometer", "Power_kw"]

X = df[features]

# 🎯 Target column must exist
fault_col = "Fault_Class"
df[fault_col] = df[fault_col].astype(int)

# Filter data for RUL regression (only fault cases)
df_rul = df[df[fault_col] != 0]  
X_rul = df_rul[features]
y_rul = df_rul["RUL"]

# ======== MODEL 1: ANOMALY (Unsupervised) ========
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

iso = IsolationForest(
    n_estimators=200,
    contamination=0.05,
    random_state=42
)
iso.fit(X_scaled)

# ======== MODEL 2: CLASSIFIER (Fault Detection) ========
X_train, X_test, y_train, y_test = train_test_split(
    X, df[fault_col], test_size=0.2, random_state=42
)

clf = XGBClassifier(
    n_estimators=150,
    max_depth=4,
    learning_rate=0.12,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="multi:softmax",
    eval_metric="mlogloss",
    tree_method="hist"
)
clf.fit(X_train, y_train)

# ======== MODEL 3: RUL Regression ========
X_train_rul, X_test_rul, y_train_rul, y_test_rul = train_test_split(
    X_rul, y_rul, test_size=0.2, random_state=42
)
rul_model = lgb.LGBMRegressor(
    n_estimators=500,
    learning_rate=0.08,
    max_depth=8,
)
rul_model.fit(X_train_rul, y_train_rul)

# ===== SAVE MODELS =====
joblib.dump(iso, "isoforest.pkl")
joblib.dump(scaler, "scaler.pkl")
joblib.dump(clf, "xgb_classifier.pkl")
joblib.dump(rul_model, "lgbm_rul.pkl")
joblib.dump(features, "features.pkl")

print("🎉 SUCCESS: All models trained and exported!")
