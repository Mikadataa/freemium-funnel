<<<<<<< HEAD
# freemium-funnel
=======
# 🎵 Freemium Funnel Project — KKBOX User Analytics  

[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/) 
[![SQL](https://img.shields.io/badge/SQL-queries-lightgrey.svg)]() 
[![Docker](https://img.shields.io/badge/Docker-Enabled-blue.svg)](https://www.docker.com/) 
[![pgAdmin](https://img.shields.io/badge/pgAdmin-4-orange.svg)](https://www.pgadmin.org/) 
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📖 Project Overview
This project analyzes **user activation, conversion, churn, and retention** using a subscription music service dataset (KKBOX).  
It demonstrates an end-to-end BI workflow with Docker, PostgreSQL, pgAdmin, and SQL — followed later by Python analysis and Tableau dashboards.

The analysis focuses on understanding the **freemium-to-paid funnel** and identifying key drivers of churn and retention.

---

## 🛠️ Tech Stack
- **Docker** → containerized Postgres + pgAdmin environment.  
- **PostgreSQL** → relational database for structured storage and SQL analysis.  
- **pgAdmin** → query console and database UI.  
- **Git Bash** → command line interface for Docker + SQL scripts.  
- **VS Code** → IDE for SQL and Python scripts.  
- **GitHub** → version control and portfolio publishing.  

---

## 📂 Data Model
Three core tables were built from Kaggle KKBOX data:

### users
| Column     | Type      | Description |
|------------|-----------|-------------|
| user_id    | text      | Unique user identifier |
| signup_ts  | timestamp | Signup datetime |
| channel    | bigint    | Encoded signup channel |
| country    | text      | Mostly null |
| device     | text      | Mostly null |

### subscriptions
| Column     | Type      | Description |
|------------|-----------|-------------|
| user_id    | text      | FK to users |
| start_ts   | timestamp | Subscription start |
| cancel_ts  | timestamp | Null if not cancelled |
| plan       | int       | Plan length in days |
| price      | numeric   | Amount paid |

### events
| Column     | Type      | Description |
|------------|-----------|-------------|
| user_id    | text      | FK to users |
| event_ts   | timestamp | Event datetime |
| event_type | text      | session_start / activate / subscribe |
| device     | text      | optional |
| source     | text      | optional |

---

## 🗄️ SQL Analysis
Core queries implemented (see `sql/analysis_stage1.sql`):

1. **Conversion funnel (signup → activate ≤7d → subscribe ≤30d)**  
2. **Churn rate by month** (subscriptions cancelled ÷ total started that month)  
3. **Retention cohort heatmap** (active users by month since signup)  
4. **Funnel by signup channel** (activation and conversion split by channel)  
5. **Funnel by first plan** (conversion rate within 30 days split by plan)  
6. **Churn by plan** (shorter plans churn more often)  
7. **Churn by channel** (acquisition quality differences)  
8. **Retention by channel** (0–12 months since signup)

---

## 📊 Results
CSV outputs are stored in `sql_results/`:

- `churn_by_channel.csv`  
- `churn_by_plan.csv`  
- `churn_rate.csv`  
- `conversion_funnel.csv`  
- `funnel_by_signup_channel.csv`  
- `funnel_by_plan_of_first_subscription.csv`  
- `retention_by_channel.csv`  

Visual exports:  
- `churn_rate.png`  
- `retention_pct_result.png`

📄 Detailed insights and recommendations are documented in [SQL_Insights.md](sql_results/SQL_Insights.md).


---

## 📸 Example Screenshots
Example outputs from pgAdmin queries:

- Churn by plan → `churn_rate.png`  
- Retention cohort → `retention_pct_result.png`

---

## 📈 Business Insights
- **Activation gap**: Very few signups activate within 7 days → onboarding improvements needed.  
- **Channel quality matters**: Some channels bring more conversions and lower churn.  
- **Plan impact**: Shorter plans have much higher churn vs longer plans.  
- **Retention cliff**: Users drop sharply after Month 1; certain channels retain better.  

### Recommendations
- Strengthen **early activation flows** (emails, push notifications, onboarding tutorials).  
- Invest in **high-quality acquisition channels**; cut spend on channels with high churn.  
- Incentivize **longer-term plans** to improve stickiness.  
- Mirror best practices from **high-retention channels** across weaker ones.

---

## 👩‍💻 Author
**Mikadataa**  
🔗 [LinkedIn](https://www.linkedin.com/in/smagulova/) | 🐙 [GitHub](https://github.com/Mikadataa)

---

## 📄 License
This project is licensed under the MIT License.
>>>>>>> e48888a (Stage 1: freemium-to-paid funnel Stage 1: SQL)
# freemium-funnel
# freemium-funnel
