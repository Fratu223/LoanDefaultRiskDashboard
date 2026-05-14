# Loan Default Risk Dashboard

An end-to-end credit risk analytics project built to simulate the work of a data analytics team at a captive finance company. The pipeline ingests raw loan applicant data, scores each applicant using a machine learning model, stores results in a relational database, and surfaces insights through an interactive Power BI dashboard.

---

## Project Overview

The core question this project answers is: **given a loan applicant's profile, how likely are they to default — and how should the portfolio be monitored as a result?**

This mirrors the real-world workflow of a credit risk team: collecting and cleaning data, building predictive models, calculating KPIs, and presenting findings to decision-makers through a dashboard.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Database | Microsoft SQL Server Express 2025 |
| Data ingestion | Python (pandas, SQLAlchemy, pyodbc) |
| Machine learning | Python (scikit-learn) |
| KPI layer | SQL views (T-SQL) |
| Dashboard | Microsoft Power BI Desktop |

---

## Project Structure

```
LoanDefaultRiskDashboard/
├── ingest.py                        # Loads and cleans raw data into SQL Server
├── score.py                         # Trains credit scoring model, writes risk scores to DB
├── kpi_views.sql                    # Creates 5 SQL views used by Power BI
├── LoanDefaultRiskDashboard.pbix    # Power BI dashboard file
├── statlog+german+credit+data/      # Raw dataset (UCI German Credit Dataset)
│   ├── german.data
│   ├── german.data-numeric
│   ├── german.doc
│   └── Index
└── venv/                            # Python virtual environment
```

---

## Pipeline

### 1. Data Ingestion (`ingest.py`)
- Loads the UCI German Credit Dataset (1,000 loan applicants, 20 features)
- Decodes all categorical codes into readable labels (e.g. `A11` → `< 0 DM`)
- Maps data to a relational schema and loads it into SQL Server via SQLAlchemy
- Verifies row counts and default rate directly from the database

### 2. Credit Scoring Model (`score.py`)
- Pulls loan data from SQL Server
- Trains and evaluates two classifiers: Logistic Regression and Gradient Boosting
- Selects the best model based on ROC-AUC score
- Assigns each applicant a default probability (0–100%) and a risk tier (Low / Medium / High)
- Writes scores back to the `risk_scores` table in SQL Server

### 3. KPI Layer (`kpi_views.sql`)
- Creates 5 SQL views on top of the `loans` and `risk_scores` tables:
  - `vw_portfolio_overview` — single-row portfolio summary
  - `vw_risk_tier_summary` — exposure and defaults by risk tier
  - `vw_default_by_purpose` — default rate by loan purpose
  - `vw_default_by_employment` — default rate by employment length
  - `vw_applicant_detail` — full per-applicant detail with risk scores

### 4. Power BI Dashboard (`LoanDefaultRiskDashboard.pbix`)
- Connects directly to SQL Server views
- **Page 1 — Portfolio Overview:** KPI cards, donut chart by risk tier, default rate by purpose and employment length
- **Page 2 — Applicant Deep Dive:** interactive slicers (risk tier, purpose, home ownership), applicant table, default probability by credit history

---

## Key Findings

- The portfolio has a **30% default rate** across 1,000 loans and €3.27M total exposure
- The credit scoring model achieved a **ROC-AUC of 0.73**, meaning it correctly ranks a defaulter above a non-defaulter 73% of the time
- Risk tier separation is strong: **High tier defaults at 54.8%** vs **Low tier at 13.7%** — a 4x difference
- **Education and "other" purpose loans** carry the highest default rates (44% and 42% respectively)
- **Applicants employed less than 1 year** default at 40.7%, nearly double the rate of those employed 4–7 years (22.4%)

---

## Dataset

**UCI Statlog German Credit Dataset**
- 1,000 loan applicants, 20 features, binary target (good/bad credit)
- Source: [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data)

---

## How to Run

1. Clone the repository and navigate to the project folder
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install pandas pyodbc sqlalchemy scikit-learn
   ```
4. Set up SQL Server Express and create the database/schema (see `kpi_views.sql` for reference)
5. Run the ingestion script:
   ```bash
   python ingest.py
   ```
6. Run the scoring script:
   ```bash
   python score.py
   ```
7. Execute `kpi_views.sql` in SSMS to create the views
8. Open `LoanDefaultRiskDashboard.pbix` in Power BI Desktop and refresh the data connection
