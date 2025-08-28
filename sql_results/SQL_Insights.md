# 📊 SQL Insights & Recommendations — Stage 1 (Freemium Funnel Project)

This document summarizes the insights gained from our SQL analysis, with direct reference to the queries used.  
All SQL scripts are available in `sql/analysis_stage1.sql`.  
CSV and PNG outputs are stored in `sql_results/`.

---

## 1. Conversion Funnel (Signup → Activation ≤7d → Subscription ≤30d)

**Query:**  
```sql
WITH signups AS (
  SELECT u.user_id, u.signup_ts
  FROM users u
),
activated AS (
  SELECT e.user_id
  FROM events e
  JOIN signups s USING (user_id)
  WHERE e.event_type='activate' 
    AND e.event_ts <= s.signup_ts + INTERVAL '7 days'
  GROUP BY e.user_id
),
subscribed AS (
  SELECT sub.user_id, MIN(sub.start_ts) AS first_sub_ts
  FROM subscriptions sub
  JOIN signups s USING (user_id)
  WHERE sub.start_ts <= s.signup_ts + INTERVAL '30 days'
  GROUP BY sub.user_id
)
SELECT
  (SELECT COUNT(*) FROM signups) AS signup_users,
  (SELECT COUNT(*) FROM activated) AS activated_users,
  (SELECT COUNT(*) FROM subscribed) AS subscribed_users;
```

**Insights:**  
- Very **few signups activated within 7 days**, a clear bottleneck in the funnel.  
- Even fewer users converted to paid subscription within 30 days.  
- Indicates **onboarding friction** — users signup but fail to take the first “aha” step.

**Recommendations:**  
- Introduce **activation nudges** in the first 7 days: welcome emails, in-app tutorials, push notifications.  
- Measure “time-to-first-activation” as a KPI.  
- Consider **early access perks** (e.g., free trial features) to encourage a first session.

---

## 2. Churn Rate by Subscription Month

**Query:**  
```sql
SELECT
  DATE_TRUNC('month', start_ts) AS cohort_month,
  COUNT(*) FILTER (WHERE cancel_ts IS NOT NULL) * 1.0
    / NULLIF(COUNT(*),0) AS churn_rate
FROM subscriptions
GROUP BY 1
ORDER BY 1;
```

**Insights:**  
- Churn rate fluctuates month-to-month.  
- Some cohorts see **70%+ churn** eventually, suggesting weak product stickiness.  
- This is **lifetime churn** per start month, not survival-based — so it’s an overestimation.

**Recommendations:**  
- Pair with **survival analysis** in Stage 2 (Python).  
- Investigate specific **plan lengths** and **channels** within each month.  
- Launch **exit surveys** to capture churn reasons (price, features, usability).

---

## 3. Retention Cohorts (0–12 Months Since Signup)

**Query (simplified):**  
```sql
WITH activity AS (
  SELECT
    DATE_TRUNC('month', u.signup_ts) AS signup_month,
    DATE_TRUNC('month', e.event_ts)  AS active_month,
    COUNT(DISTINCT u.user_id)        AS active_users
  FROM users u
  JOIN events e ON e.user_id = u.user_id
  WHERE e.event_type IN ('session_start','activate','subscribe')
  GROUP BY 1,2
),
cohorts AS (
  SELECT DATE_TRUNC('month', signup_ts) AS signup_month,
         COUNT(*) AS cohort_size
  FROM users
  GROUP BY 1
)
SELECT
  signup_month,
  EXTRACT(YEAR FROM age(a.active_month, a.signup_month))*12
    + EXTRACT(MONTH FROM age(a.active_month, a.signup_month)) AS months_since_signup,
  active_users,
  ROUND(100.0 * active_users / NULLIF(cohort_size,0), 2) AS retention_pct
FROM activity a
JOIN cohorts c USING (signup_month)
ORDER BY signup_month, months_since_signup;
```

**Insights:**  
- Retention drops sharply after **Month 1**, typical of freemium apps.  
- By Month 3, most cohorts retain **<5%** of original users.  
- Retention differs by channel (see section 8).

**Recommendations:**  
- Focus product development on **Month-1 engagement**.  
- Introduce **“habit-forming features”** (daily streaks, playlists, personalization).  
- Consider **win-back campaigns** around Month 2 when drop-off accelerates.

---

## 4. Funnel by Signup Channel

**Insights:**  
- Channels differ significantly in **activation and conversion rates**.  
- Some bring large volumes but very low conversion.  
- Others are smaller but with better quality.

**Recommendations:**  
- Reallocate spend to **higher-converting channels**.  
- Tailor onboarding per channel (ads vs referral users behave differently).  

---

## 5. Funnel by Plan of First Subscription

**Insights:**  
- Most users start with **short-term plans (30 days)**.  
- Average first price is low, indicating “trial mentality”.  
- Longer plans see fewer signups but potentially better revenue.

**Recommendations:**  
- Offer **discounted upgrades** (30 → 90 days).  
- Bundle premium features with longer plans to encourage commitment.  

---

## 6. Churn by Plan

**Insights:**  
- Shorter plans have the **highest churn rates**.  
- Longer plans reduce churn but have lower uptake.

**Recommendations:**  
- Push **annual plans** during signup with a discount.  
- Introduce **loyalty rewards** (bonus months, points).  

---

## 7. Churn by Channel

**Insights:**  
- Some acquisition channels deliver **high churn users**.  
- Others (likely organic/referrals) perform much better.

**Recommendations:**  
- Stop/reduce spend on **bad channels**.  
- Double-down on **channels with lower churn**.  

---

## 8. Retention by Channel (0–12 months)

**Insights:**  
- Channels differ in **retention curves**.  
- Some maintain ~5% users even at Month 12, others drop to zero.

**Recommendations:**  
- Analyze the **best channel** experience and replicate across others.  
- Adjust onboarding flows to mimic high-retention sources.  

---

# ✅ Next Steps
- **Stage 2 (Python):** Visualize cohorts, funnels, churn survival.  
- **Stage 3 (Tableau):** Build interactive dashboards for funnel/retention by channel and plan.  

---

📂 This file is part of `sql_results/SQL_Insights.md`.
