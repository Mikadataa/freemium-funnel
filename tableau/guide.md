# Tableau guide (step-by-step)

## 1) Connect to Postgres
- **To a server** → *PostgreSQL*
  - Server: `localhost`
  - Port: `5432`
  - Database: `analytics`
  - Username: `postgres`
  - Password: `postgres`
- Choose **Live** (recommended) or **Extract** for performance.

## 2) Data model (logical layer)
Drag these tables from the left pane (public schema):
- `users`
- `events`
- `subscriptions`

Use **Relationships** (not physical joins):
- `users.user_id` ↔ `events.user_id`
- `users.user_id` ↔ `subscriptions.user_id`

## 3) Calculated fields
**a) Signup Month**
```tableau
DATETRUNC('month', [signup_ts])
```

**b) Active Month**
```tableau
DATETRUNC('month', [event_ts])
```

**c) Months Since Signup**
```tableau
DATEDIFF('month', [Signup Month], [Active Month])
```

**d) Activated (7 days)**
```tableau
{ FIXED [user_id] :
  MIN(
    IIF( MIN([event_type]) = 'activate'
      AND MIN([event_ts]) <= MIN([signup_ts]) + MAKEINTERVAL(0,0,0,7), 1, 0)
  )
}
```
*(If MAKEINTERVAL isn’t available in your Tableau version, use `DATEADD('day',7,[signup_ts])` and comparisons.)*

**e) Subscribed (30 days)**
```tableau
{ FIXED [user_id] :
  IIF( MIN([start_ts]) <= MIN([signup_ts]) + DATEADD('day',30,[signup_ts]), 1, 0)
}
```

**f) Funnel Step**
```tableau
IF [Activated (7 days)] = 0 THEN "Signup"
ELSEIF [Subscribed (30 days)] = 0 THEN "Activated"
ELSE "Subscribed" END
```

**g) Cohort Size**
```tableau
{ FIXED [Signup Month] : COUNTD([user_id]) }
```

**h) Active Users in Month**
```tableau
{ FIXED [Signup Month], [Active Month] : COUNTD(IF [event_type] = 'session_start' OR [event_type] = 'activate' OR [event_type] = 'subscribe' THEN [user_id] END) }
```

**i) Retention %**
```tableau
[Active Users in Month] / [Cohort Size]
```

**j) Churned Paid?**
```tableau
IF NOT ISNULL([cancel_ts]) THEN 1 ELSE 0 END
```

## 4) Build the visuals
### A) Funnel
- **Sheet**: Bar chart
- Columns: `Funnel Step`
- Rows: `{ FIXED [Funnel Step] : COUNTD([user_id]) }`
- Sort descending; add table calc for % of total (base = signups).

### B) Cohort Heatmap
- **Sheet**: Heatmap
- Rows: `Signup Month`
- Columns: `Months Since Signup`
- Color: `Retention %` (format as percentage, 0–100%)
- Tooltip: show cohort size & active users

### C) Churn Trend (Paid)
- **Sheet**: Line
- Columns: `DATETRUNC('month', [start_ts])`
- Rows: `AVG([Churned Paid?])` (format %)
- Filter out months with small n if needed

### D) Dashboard
- Combine Funnel + Cohort + Churn into one dashboard
- Add filters: Country, Device, Channel, Signup Month

## 5) Publish
- Export as packaged workbook (.twbx) for your portfolio
- Snapshot key views for the README
