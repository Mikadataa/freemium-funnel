-- 🧮 Core queries

-- 1) Conversion funnel (signup → activation within 7d → subscription within 30d)
-- signups: every user and their signup timestamp.
-- activated: users who had an activate event within 7 days of signup.
-- subscribed: users whose first subscription started within 30 days of signup.
-- Final SELECT: shows the three counts (funnel steps).

WITH signups AS (
  SELECT u.user_id, u.signup_ts
  FROM users u
),
activated AS (
  SELECT e.user_id
  FROM events e
  JOIN signups s USING (user_id)
  WHERE e.event_type='activate' AND e.event_ts <= s.signup_ts + INTERVAL '7 days'
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
  (SELECT COUNT(*) FROM signups)                     AS signup_users,
  (SELECT COUNT(*) FROM activated)                   AS activated_users,
  (SELECT COUNT(*) FROM subscribed)                  AS subscribed_users;

-- 2) Churn rate by month (paid users)
--   Groups subscriptions by the month they started.
--   Churn rate in that month = % of those subs that have a non-null cancel_ts (i.e., eventually churned).
--   It’s a simple, not time-aligned churn view (not survival analysis)

SELECT
  DATE_TRUNC('month', start_ts) AS cohort_month,
  COUNT(*) FILTER (WHERE cancel_ts IS NOT NULL) * 1.0
    / NULLIF(COUNT(*),0) AS churn_rate
FROM subscriptions
GROUP BY 1
ORDER BY 1;

-- 3) Retention cohort heatmap (active users by months since signup)
--   base: pairs each user’s signup month with any month they were “active” (based on event types).
--   cohorts: all users who signed up that month, not just those with events (cohort size)
--   activity: counts distinct active users by (signup_month, active_month) and computes months since signup
--   Final select: active_users ÷ cohort_size → retention%.
WITH activity AS (
  SELECT
    DATE_TRUNC('month', u.signup_ts) AS signup_month,
    DATE_TRUNC('month', e.event_ts)  AS active_month,
    COUNT(DISTINCT u.user_id)        AS active_users
  FROM users u
  JOIN events e
    ON e.user_id = u.user_id
   AND e.event_type IN ('session_start','activate','subscribe')
  GROUP BY 1, 2
),
cohorts AS (
  -- IMPORTANT: use ALL signups, not just those with events
  SELECT DATE_TRUNC('month', signup_ts) AS signup_month,
         COUNT(*) AS cohort_size
  FROM users
  GROUP BY 1
),
final AS (
  SELECT
    a.signup_month,
    EXTRACT(YEAR FROM age(a.active_month, a.signup_month))*12
      + EXTRACT(MONTH FROM age(a.active_month, a.signup_month)) AS months_since_signup,
    a.active_users,
    c.cohort_size
  FROM activity a
  JOIN cohorts c USING (signup_month)
)
SELECT
  signup_month,
  months_since_signup,
  active_users,
  ROUND(100.0 * active_users / NULLIF(cohort_size,0), 2) AS retention_pct
FROM final
ORDER BY signup_month, months_since_signup;


--4) Funnel by signup channel (7-day Activate, 30-day Subscribe)
/*Funnel by signup channel (7-day Activate, 30-day Subscribe)
What the SQL does (in plain English):

Build signups with user_id, signup_ts, channel.
activated: users with an activate event within 7 days of signup.
first_sub: each user’s first subscription start.
subscribed: users whose first sub started ≤30 days after signup.
Final SELECT counts signups, activated, subscribed and computes two rates:
act_rate_7d_pct = Activated / Signups * 100
sub_rate_30d_pct = Subscribed / Signups * 100*/

WITH signups AS (
  SELECT user_id, signup_ts, COALESCE(channel::text,'unknown') AS channel
  FROM users
),
activated AS (
  SELECT e.user_id
  FROM events e
  JOIN signups s USING(user_id)
  WHERE e.event_type='activate'
    AND e.event_ts <= s.signup_ts + INTERVAL '7 days'
  GROUP BY e.user_id
),
first_sub AS (
  SELECT user_id, MIN(start_ts) AS first_sub_ts
  FROM subscriptions
  GROUP BY user_id
),
subscribed AS (
  SELECT fs.user_id
  FROM first_sub fs
  JOIN signups s USING(user_id)
  WHERE fs.first_sub_ts <= s.signup_ts + INTERVAL '30 days'
)
SELECT
  s.channel,
  COUNT(*)                                                      AS signups,
  COUNT(*) FILTER (WHERE a.user_id  IS NOT NULL)               AS activated_7d,
  COUNT(*) FILTER (WHERE sub.user_id IS NOT NULL)              AS subscribed_30d,
  ROUND(100.0 * COUNT(*) FILTER (WHERE a.user_id  IS NOT NULL) / NULLIF(COUNT(*),0), 2) AS act_rate_7d_pct,
  ROUND(100.0 * COUNT(*) FILTER (WHERE sub.user_id IS NOT NULL) / NULLIF(COUNT(*),0), 2) AS sub_rate_30d_pct
FROM signups s
LEFT JOIN activated a  ON a.user_id  = s.user_id
LEFT JOIN subscribed sub ON sub.user_id = s.user_id
GROUP BY s.channel
ORDER BY signups DESC;


--5) Funnel by plan of first subscription
/*What the SQL does:
first_sub: first subscription row per user (captures plan and price).
converted_30d: users whose first sub happened ≤30 days after signup.
Final SELECT groups by first_plan_days and reports:
converters_30d (how many converted in 30 days)
avg_first_price
*/
WITH signups AS (
  SELECT user_id, signup_ts FROM users
),
first_sub AS (
  SELECT DISTINCT ON (user_id)
         user_id, start_ts, plan::text AS plan_days, price
  FROM subscriptions
  ORDER BY user_id, start_ts
),
converted_30d AS (
  SELECT fs.user_id
  FROM first_sub fs
  JOIN signups s USING(user_id)
  WHERE fs.start_ts <= s.signup_ts + INTERVAL '30 days'
)
SELECT
  COALESCE(fs.plan_days,'unknown') AS first_plan_days,
  COUNT(*)                         AS signups_seen,          -- context
  COUNT(c.user_id)                 AS converters_30d,
  ROUND(AVG(fs.price)::numeric,2)  AS avg_first_price
FROM signups s
LEFT JOIN converted_30d c ON c.user_id = s.user_id
LEFT JOIN first_sub     fs ON fs.user_id = s.user_id
GROUP BY COALESCE(fs.plan_days,'unknown')
ORDER BY converters_30d DESC;

--6) Churn by plan 
/*What the SQL does:
Groups subscriptions by plan (cast to text for display).
churn_rate_pct = COUNT(cancelled) / COUNT(all) per plan.
*/
SELECT
  COALESCE(plan::text,'unknown')         AS plan_days,
  COUNT(*)                                AS subs,
  COUNT(*) FILTER (WHERE cancel_ts IS NOT NULL) AS churned,
  ROUND(100.0 * COUNT(*) FILTER (WHERE cancel_ts IS NOT NULL) / NULLIF(COUNT(*),0), 2) AS churn_rate_pct
FROM subscriptions
GROUP BY 1
ORDER BY subs DESC;

--7) Churn by channel 
/*What the SQL does:
Joins subscriptions to users to attribute churn to original signup channel.
Computes churn rate per channel.*/
SELECT
  COALESCE(u.channel::text,'unknown')     AS channel,
  COUNT(*)                                AS subs,
  COUNT(*) FILTER (WHERE s.cancel_ts IS NOT NULL) AS churned,
  ROUND(100.0 * COUNT(*) FILTER (WHERE s.cancel_ts IS NOT NULL) / NULLIF(COUNT(*),0), 2) AS churn_rate_pct
FROM subscriptions s
JOIN users u ON u.user_id = s.user_id
GROUP BY 1
ORDER BY subs DESC;

--8)Retention by channel (long form, 0–12 months)
/*What the SQL does:
activity: distinct active users per (signup_month, active_month, channel) from events.
cohorts: total signups per (signup_month, channel) for the denominator.
Calculates months_since_signup and retention_pct = active / cohort_size * 100*/

WITH activity AS (
  SELECT
    DATE_TRUNC('month', u.signup_ts) AS signup_month,
    DATE_TRUNC('month', e.event_ts)  AS active_month,
    COALESCE(u.channel::text,'unknown') AS channel,
    COUNT(DISTINCT u.user_id)        AS active_users
  FROM users u
  JOIN events e ON e.user_id = u.user_id
  WHERE e.event_type IN ('session_start','activate','subscribe')
    AND e.event_ts < u.signup_ts + INTERVAL '13 months'
  GROUP BY 1,2,3
),
cohorts AS (
  SELECT DATE_TRUNC('month', signup_ts) AS signup_month,
         COALESCE(channel::text,'unknown') AS channel,
         COUNT(*) AS cohort_size
  FROM users
  GROUP BY 1,2
),
final AS (
  SELECT
    a.signup_month,
    a.channel,
    (EXTRACT(YEAR FROM age(a.active_month, a.signup_month))*12
     + EXTRACT(MONTH FROM age(a.active_month, a.signup_month)))::int AS months_since_signup,
    a.active_users,
    c.cohort_size
  FROM activity a
  JOIN cohorts c USING (signup_month, channel)
)
SELECT
  signup_month::date,
  channel,
  months_since_signup,
  active_users,
  ROUND(100.0 * active_users / NULLIF(cohort_size,0), 2) AS retention_pct
FROM final
WHERE months_since_signup BETWEEN 0 AND 12
ORDER BY signup_month, channel, months_since_signup; 

