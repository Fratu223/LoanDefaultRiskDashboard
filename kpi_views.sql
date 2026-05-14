USE LoanCreditRisk;
GO

-- ──────────────────────────────────────────────
-- VIEW 1: Portfolio Overview
-- One row summary of the entire loan portfolio
-- ──────────────────────────────────────────────
CREATE OR ALTER VIEW vw_portfolio_overview AS
SELECT
    COUNT(*)                                            AS total_loans,
    SUM(loan_amount)                                    AS total_exposure,
    AVG(loan_amount)                                    AS avg_loan_amount,
    SUM(CASE WHEN loan_status = 'Charged Off'
        THEN 1 ELSE 0 END)                              AS total_defaults,
    CAST(
        100.0 * SUM(CASE WHEN loan_status = 'Charged Off'
        THEN 1 ELSE 0 END) / COUNT(*)
    AS DECIMAL(5,2))                                    AS default_rate_pct,
    SUM(CASE WHEN loan_status = 'Charged Off'
        THEN loan_amount ELSE 0 END)                    AS total_defaulted_amount,
    AVG(r.default_probability * 100)                    AS avg_default_probability_pct
FROM loans l
JOIN risk_scores r ON l.loan_id = r.loan_id;
GO

-- ──────────────────────────────────────────────
-- VIEW 2: Risk Tier Summary
-- Breakdown of loans, exposure and defaults by risk tier
-- ──────────────────────────────────────────────
CREATE OR ALTER VIEW vw_risk_tier_summary AS
SELECT
    r.risk_tier,
    COUNT(*)                                            AS total_loans,
    SUM(l.loan_amount)                                  AS total_exposure,
    AVG(l.loan_amount)                                  AS avg_loan_amount,
    SUM(CASE WHEN l.loan_status = 'Charged Off'
        THEN 1 ELSE 0 END)                              AS total_defaults,
    CAST(
        100.0 * SUM(CASE WHEN l.loan_status = 'Charged Off'
        THEN 1 ELSE 0 END) / COUNT(*)
    AS DECIMAL(5,2))                                    AS default_rate_pct,
    CAST(
        AVG(r.default_probability * 100)
    AS DECIMAL(5,2))                                    AS avg_default_prob_pct
FROM loans l
JOIN risk_scores r ON l.loan_id = r.loan_id
GROUP BY r.risk_tier;
GO

-- ──────────────────────────────────────────────
-- VIEW 3: Default Rate by Loan Purpose
-- Helps identify which loan types carry most risk
-- ──────────────────────────────────────────────
CREATE OR ALTER VIEW vw_default_by_purpose AS
SELECT
    l.purpose,
    COUNT(*)                                            AS total_loans,
    SUM(l.loan_amount)                                  AS total_exposure,
    SUM(CASE WHEN l.loan_status = 'Charged Off'
        THEN 1 ELSE 0 END)                              AS total_defaults,
    CAST(
        100.0 * SUM(CASE WHEN l.loan_status = 'Charged Off'
        THEN 1 ELSE 0 END) / COUNT(*)
    AS DECIMAL(5,2))                                    AS default_rate_pct,
    CAST(
        AVG(r.default_probability * 100)
    AS DECIMAL(5,2))                                    AS avg_default_prob_pct
FROM loans l
JOIN risk_scores r ON l.loan_id = r.loan_id
GROUP BY l.purpose;
GO

-- ──────────────────────────────────────────────
-- VIEW 4: Default Rate by Employment Length
-- Shows how job stability correlates with default risk
-- ──────────────────────────────────────────────
CREATE OR ALTER VIEW vw_default_by_employment AS
SELECT
    l.employment_length,
    COUNT(*)                                            AS total_loans,
    SUM(CASE WHEN l.loan_status = 'Charged Off'
        THEN 1 ELSE 0 END)                              AS total_defaults,
    CAST(
        100.0 * SUM(CASE WHEN l.loan_status = 'Charged Off'
        THEN 1 ELSE 0 END) / COUNT(*)
    AS DECIMAL(5,2))                                    AS default_rate_pct,
    CAST(
        AVG(r.default_probability * 100)
    AS DECIMAL(5,2))                                    AS avg_default_prob_pct
FROM loans l
JOIN risk_scores r ON l.loan_id = r.loan_id
GROUP BY l.employment_length;
GO

-- ──────────────────────────────────────────────
-- VIEW 5: Applicant Detail (for drill-down)
-- Full row per loan with risk score attached
-- Used for the individual applicant view in Power BI
-- ──────────────────────────────────────────────
CREATE OR ALTER VIEW vw_applicant_detail AS
SELECT
    l.loan_id,
    l.loan_amount,
    l.term,
    l.installment,
    l.grade                                             AS checking_status,
    l.sub_grade                                         AS credit_history,
    l.employment_length,
    l.home_ownership,
    l.purpose,
    l.open_accounts                                     AS existing_credits,
    l.loan_status,
    CASE WHEN l.loan_status = 'Charged Off'
        THEN 1 ELSE 0 END                               AS is_default,
    r.default_probability,
    CAST(r.default_probability * 100 AS DECIMAL(5,2))  AS default_prob_pct,
    r.risk_tier,
    r.scored_at
FROM loans l
JOIN risk_scores r ON l.loan_id = r.loan_id;
GO

-- ──────────────────────────────────────────────
-- QUICK CHECKS — run these to verify all views work
-- ──────────────────────────────────────────────
SELECT * FROM vw_portfolio_overview;
SELECT * FROM vw_risk_tier_summary      ORDER BY default_rate_pct DESC;
SELECT * FROM vw_default_by_purpose     ORDER BY default_rate_pct DESC;
SELECT * FROM vw_default_by_employment  ORDER BY default_rate_pct DESC;
SELECT TOP 10 * FROM vw_applicant_detail ORDER BY default_probability DESC;
