import pandas as pd
from sqlalchemy import create_engine, text

# ──────────────────────────────────────────────
# 1. LOAD RAW DATA
# ──────────────────────────────────────────────

col_names = [
    "checking_status",      # A1  - status of checking account
    "duration_months",      # A2  - loan duration in months
    "credit_history",       # A3  - credit history
    "purpose",              # A4  - purpose of loan
    "credit_amount",        # A5  - loan amount (DM)
    "savings_account",      # A6  - savings account / bonds
    "employment_since",     # A7  - present employment since
    "installment_rate",     # A8  - installment rate % of income
    "personal_status",      # A9  - personal status and sex
    "other_debtors",        # A10 - other debtors / guarantors
    "residence_since",      # A11 - present residence since (years)
    "property",             # A12 - property type
    "age",                  # A13 - age in years
    "other_installments",   # A14 - other installment plans
    "housing",              # A15 - housing type
    "existing_credits",     # A16 - number of existing credits at bank
    "job",                  # A17 - job type
    "liable_people",        # A18 - number of dependants
    "telephone",            # A19 - telephone registered
    "foreign_worker",       # A20 - foreign worker
    "default_label"         # Target: 1 = Good (no default), 2 = Bad (default)
]

df = pd.read_csv(
    r"C:\Users\Misu\Documents\LoanDefaultRiskDashboard\statlog+german+credit+data\german.data",
    sep=" ",
    header=None,
    names=col_names
)

print(f"Loaded {len(df)} rows, {len(df.columns)} columns")

# ──────────────────────────────────────────────
# 2. DECODE CATEGORICAL CODES → READABLE LABELS
# ──────────────────────────────────────────────

checking_map = {
    "A11": "< 0 DM", "A12": "0-200 DM",
    "A13": ">= 200 DM", "A14": "no account"
}
credit_history_map = {
    "A30": "no credits taken", "A31": "all paid at this bank",
    "A32": "existing paid duly", "A33": "delay in past",
    "A34": "critical/other credits"
}
purpose_map = {
    "A40": "car (new)", "A41": "car (used)", "A42": "furniture/equipment",
    "A43": "radio/television", "A44": "domestic appliances", "A45": "repairs",
    "A46": "education", "A48": "retraining", "A49": "business", "A410": "others"
}
savings_map = {
    "A61": "< 100 DM", "A62": "100-500 DM", "A63": "500-1000 DM",
    "A64": ">= 1000 DM", "A65": "unknown/no savings"
}
employment_map = {
    "A71": "unemployed", "A72": "< 1 year", "A73": "1-4 years",
    "A74": "4-7 years", "A75": ">= 7 years"
}
personal_status_map = {
    "A91": "male: divorced/separated", "A92": "female: divorced/married",
    "A93": "male: single", "A94": "male: married/widowed", "A95": "female: single"
}
other_debtors_map = {
    "A101": "none", "A102": "co-applicant", "A103": "guarantor"
}
property_map = {
    "A121": "real estate", "A122": "life insurance/savings",
    "A123": "car/other", "A124": "unknown/no property"
}
other_installments_map = {
    "A141": "bank", "A142": "stores", "A143": "none"
}
housing_map = {
    "A151": "rent", "A152": "own", "A153": "free"
}
job_map = {
    "A171": "unemployed/unskilled non-resident", "A172": "unskilled resident",
    "A173": "skilled employee", "A174": "management/self-employed"
}
telephone_map = {"A191": "none", "A192": "yes"}
foreign_worker_map = {"A201": "yes", "A202": "no"}

df["checking_status"]    = df["checking_status"].map(checking_map)
df["credit_history"]     = df["credit_history"].map(credit_history_map)
df["purpose"]            = df["purpose"].map(purpose_map)
df["savings_account"]    = df["savings_account"].map(savings_map)
df["employment_since"]   = df["employment_since"].map(employment_map)
df["personal_status"]    = df["personal_status"].map(personal_status_map)
df["other_debtors"]      = df["other_debtors"].map(other_debtors_map)
df["property"]           = df["property"].map(property_map)
df["other_installments"] = df["other_installments"].map(other_installments_map)
df["housing"]            = df["housing"].map(housing_map)
df["job"]                = df["job"].map(job_map)
df["telephone"]          = df["telephone"].map(telephone_map)
df["foreign_worker"]     = df["foreign_worker"].map(foreign_worker_map)

# Convert target to a clear boolean: 1 = default, 0 = no default
df["default_label"] = df["default_label"].map({1: 0, 2: 1})
df.rename(columns={"default_label": "is_default"}, inplace=True)

print("Categorical columns decoded")

# ──────────────────────────────────────────────
# 3. BASIC DATA QUALITY CHECKS
# ──────────────────────────────────────────────

print(f"\nDefault rate: {df['is_default'].mean():.1%}")
print(f"Missing values:\n{df.isnull().sum()[df.isnull().sum() > 0]}")
print(f"Age range: {df['age'].min()}–{df['age'].max()} years")
print(f"Credit amount range: {df['credit_amount'].min()}–{df['credit_amount'].max()} DM")

# ──────────────────────────────────────────────
# 4. MAP TO loans TABLE SCHEMA
# ──────────────────────────────────────────────

loans_df = pd.DataFrame({
    "member_id":           range(1, len(df) + 1),
    "loan_amount":         df["credit_amount"],
    "funded_amount":       df["credit_amount"],           # same in this dataset
    "term":                df["duration_months"].astype(str) + " months",
    "interest_rate":       None,                          # not in this dataset
    "installment":         df["installment_rate"],
    "grade":               df["checking_status"],
    "sub_grade":           df["credit_history"],
    "employment_length":   df["employment_since"],
    "home_ownership":      df["housing"],
    "annual_income":       None,                          # not in this dataset
    "verification_status": df["foreign_worker"],
    "issue_date":          None,
    "loan_status":         df["is_default"].map({0: "Fully Paid", 1: "Charged Off"}),
    "purpose":             df["purpose"],
    "dti":                 None,                          # not in this dataset
    "delinq_2yrs":         None,
    "open_accounts":       df["existing_credits"],
    "total_accounts":      df["existing_credits"],
    "revolving_balance":   None,
    "revolving_util":      None
})

print(f"\nMapped to loans schema: {loans_df.shape}")

# ──────────────────────────────────────────────
# 5. LOAD INTO SQL SERVER
# ──────────────────────────────────────────────

connection_string = (
    "mssql+pyodbc://DESKTOP-4P709V8\\SQLEXPRESS/LoanCreditRisk"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&trusted_connection=yes"
)

engine = create_engine(connection_string, fast_executemany=True)

# Clear existing data before reload (safe for dev)
with engine.connect() as conn:
    conn.execute(text("DELETE FROM risk_scores"))
    conn.execute(text("DELETE FROM loans"))
    conn.commit()
    print("Cleared existing data from loans and risk_scores tables")

loans_df.to_sql(
    name="loans",
    con=engine,
    if_exists="append",     # append since table already exists with our schema
    index=False,
    chunksize=200
)

print(f"Inserted {len(loans_df)} rows into [LoanCreditRisk].[dbo].[loans]")

# ──────────────────────────────────────────────
# 6. VERIFY
# ──────────────────────────────────────────────

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT
            COUNT(*)                                    AS total_loans,
            SUM(CASE WHEN loan_status = 'Charged Off'
                THEN 1 ELSE 0 END)                      AS total_defaults,
            CAST(
                100.0 * SUM(CASE WHEN loan_status = 'Charged Off'
                THEN 1 ELSE 0 END) / COUNT(*)
            AS DECIMAL(5,2))                            AS default_rate_pct
        FROM loans
    """))
    row = result.fetchone()
    print(f"\nVerification from SQL Server:")
    print(f"   Total loans    : {row[0]}")
    print(f"   Total defaults : {row[1]}")
    print(f"   Default rate   : {row[2]}%")

print("\nPipeline complete — data is live in SQL Server!")
