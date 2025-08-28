import os
import pandas as pd
from sqlalchemy import create_engine, text
import streamlit as st

st.set_page_config(page_title="Freemium Funnel", layout="wide")

conn_str = st.secrets.get("conn", os.getenv("DB_CONN", "postgresql+psycopg2://postgres:postgres@localhost:5432/analytics"))
engine = create_engine(conn_str, future=True)

st.title("Freemium Conversion Funnel & Cohorts")

@st.cache_data(ttl=300)
def get_funnel():
    q = open("sql/analysis.sql").read().split(';')[0] + ';'  # first statement
    with engine.connect() as c:
        df = pd.read_sql(q, c)
    return df

@st.cache_data(ttl=300)
def get_cohorts():
    q = open("sql/analysis.sql").read()
    q = q.split('-- 3) Retention cohort heatmap')[1]
    with engine.connect() as c:
        df = pd.read_sql(q, c)
    return df

f = get_funnel()
col1, col2, col3 = st.columns(3)
col1.metric("Signups", int(f['signup_users'][0]))
col2.metric("Activated (<=7d)", int(f['activated_users'][0]))
col3.metric("Subscribed (<=30d)", int(f['subscribed_users'][0]))

st.header("Cohort Retention Heatmap")
coh = get_cohorts()
pivot = coh.pivot_table(index="signup_month", columns="months_since_signup", values="retention_pct")
st.dataframe(pivot.round(1))
