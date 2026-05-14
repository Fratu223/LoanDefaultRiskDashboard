import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import (
    classification_report, roc_auc_score, confusion_matrix
)
import warnings
warnings.filterwarnings("ignore")

# ──────────────────────────────────────────────
# 1. CONNECT & PULL DATA FROM SQL SERVER
# ──────────────────────────────────────────────

connection_string = (
    "mssql+pyodbc://DESKTOP-4P709V8\\SQLEXPRESS/LoanCreditRisk"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&trusted_connection=yes"
)

engine = create_engine(connection_string, fast_executemany=True)

df = pd.read_sql("SELECT * FROM loans", engine)
print(f"Pulled {len(df)} rows from SQL Server")

# ──────────────────────────────────────────────
# 2. PREPARE FEATURES
# ──────────────────────────────────────────────

# Target: 1 = default, 0 = no default
df["is_default"] = (df["loan_status"] == "Charged Off").astype(int)

# Select the most predictive features available in this dataset
features = [
    "grade",            # checking account status (proxy for creditworthiness)
    "sub_grade",        # credit history
    "employment_length",# employment stability
    "home_ownership",   # housing situation
    "purpose",          # loan purpose
    "installment",      # installment rate % of income
    "open_accounts",    # number of existing credits
    "loan_amount",      # credit amount
]

df_model = df[features + ["is_default", "loan_id"]].copy()

# Encode all categorical columns to numbers (LabelEncoder per column)
label_encoders = {}
for col in ["grade", "sub_grade", "employment_length", "home_ownership", "purpose"]:
    le = LabelEncoder()
    df_model[col] = le.fit_transform(df_model[col].astype(str))
    label_encoders[col] = le

print("Features prepared and encoded")
print(f"   Feature columns : {features}")
print(f"   Default rate    : {df_model['is_default'].mean():.1%}")

# ──────────────────────────────────────────────
# 3. TRAIN / TEST SPLIT
# ──────────────────────────────────────────────

X = df_model[features]
y = df_model["is_default"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\nSplit: {len(X_train)} train rows, {len(X_test)} test rows")

# ──────────────────────────────────────────────
# 4. TRAIN MODEL 1 — LOGISTIC REGRESSION
# ──────────────────────────────────────────────

print("\n── Logistic Regression ──────────────────────")
lr = LogisticRegression(max_iter=1000, random_state=42)
lr.fit(X_train, y_train)

lr_pred  = lr.predict(X_test)
lr_proba = lr.predict_proba(X_test)[:, 1]
lr_auc   = roc_auc_score(y_test, lr_proba)

print(classification_report(y_test, lr_pred, target_names=["No Default", "Default"]))
print(f"ROC-AUC : {lr_auc:.4f}")

# ──────────────────────────────────────────────
# 5. TRAIN MODEL 2 — GRADIENT BOOSTING
# ──────────────────────────────────────────────

print("\n── Gradient Boosting ────────────────────────")
gb = GradientBoostingClassifier(
    n_estimators=200,
    learning_rate=0.05,
    max_depth=4,
    random_state=42
)
gb.fit(X_train, y_train)

gb_pred  = gb.predict(X_test)
gb_proba = gb.predict_proba(X_test)[:, 1]
gb_auc   = roc_auc_score(y_test, gb_proba)

print(classification_report(y_test, gb_pred, target_names=["No Default", "Default"]))
print(f"ROC-AUC : {gb_auc:.4f}")

# ──────────────────────────────────────────────
# 6. PICK BEST MODEL
# ──────────────────────────────────────────────

print("\n── Model Comparison ─────────────────────────")
print(f"Logistic Regression  ROC-AUC : {lr_auc:.4f}")
print(f"Gradient Boosting    ROC-AUC : {gb_auc:.4f}")

if gb_auc >= lr_auc:
    best_model = gb
    best_proba = gb.predict_proba(X)[:, 1]   # score ALL rows
    print("Selected: Gradient Boosting")
else:
    best_model = lr
    best_proba = lr.predict_proba(X)[:, 1]
    print("Selected: Logistic Regression")

# ──────────────────────────────────────────────
# 7. ASSIGN RISK TIERS
# ──────────────────────────────────────────────

def assign_risk_tier(prob):
    if prob < 0.25:
        return "Low"
    elif prob < 0.50:
        return "Medium"
    else:
        return "High"

scores_df = pd.DataFrame({
    "loan_id":             df_model["loan_id"].values,
    "default_probability": np.round(best_proba, 4),
    "risk_tier":           [assign_risk_tier(p) for p in best_proba]
})

print(f"\nRisk tier distribution:")
print(scores_df["risk_tier"].value_counts().to_string())

# ──────────────────────────────────────────────
# 8. WRITE SCORES BACK TO SQL SERVER
# ──────────────────────────────────────────────

with engine.connect() as conn:
    conn.execute(text("DELETE FROM risk_scores"))
    conn.commit()
    print("\nCleared existing risk_scores")

scores_df.to_sql(
    name="risk_scores",
    con=engine,
    if_exists="append",
    index=False,
    chunksize=200
)

print(f"Inserted {len(scores_df)} risk scores into [LoanCreditRisk].[dbo].[risk_scores]")

# ──────────────────────────────────────────────
# 9. VERIFY WITH SQL
# ──────────────────────────────────────────────

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT
            r.risk_tier,
            COUNT(*)                                AS total_loans,
            CAST(AVG(r.default_probability * 100)
                AS DECIMAL(5,2))                    AS avg_default_prob_pct,
            SUM(CASE WHEN l.loan_status = 'Charged Off'
                THEN 1 ELSE 0 END)                  AS actual_defaults
        FROM risk_scores r
        JOIN loans l ON r.loan_id = l.loan_id
        GROUP BY r.risk_tier
        ORDER BY avg_default_prob_pct DESC
    """))
    rows = result.fetchall()

print(f"\nVerification from SQL Server:")
print(f"{'Risk Tier':<12} {'Loans':>8} {'Avg Prob%':>10} {'Actual Defaults':>16}")
print("-" * 50)
for row in rows:
    print(f"{row[0]:<12} {row[1]:>8} {row[2]:>9}% {row[3]:>16}")

print("\nScoring complete — risk scores are live in SQL Server!")