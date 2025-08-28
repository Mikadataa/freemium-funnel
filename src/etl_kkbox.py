#!/usr/bin/env python
"""ETL for KKBOX/WSDM to canonical freemium schema.

Expected raw files in: data/raw/kkbox/
- members.csv
- transactions.csv
- user_logs.csv   (may be split into parts by Kaggle; adapt the loader)

Usage:
  python src/etl_kkbox.py --conn postgresql+psycopg2://postgres:postgres@localhost:5432/analytics
"""
import argparse, os, glob, pandas as pd
from sqlalchemy import create_engine

def load_members(path):
    df = pd.read_csv(path)
    # Map to users table
    users = pd.DataFrame({
        "user_id": df["msno"].astype("category").cat.codes,  # map hashed id to int
        "signup_ts": pd.to_datetime(df.get("registration_init_time", None), format="%Y%m%d", errors="coerce"),
        "channel": df.get("registered_via"),
        "country": None,
        "device": None
    }).drop_duplicates(subset=["user_id"])
    id_map = pd.DataFrame({"msno": df["msno"], "user_id": users["user_id"]})
    return users, id_map

def load_transactions(path, id_map):
    tx = pd.read_csv(path, parse_dates=["transaction_date","membership_expire_date"])
    # Map msno to user_id
    tx = tx.merge(id_map, on="msno", how="left")
    subs = tx.groupby(["user_id"], as_index=False).agg(
        start_ts=("transaction_date","min"),
        plan=("payment_plan_days", "max"),
        price=("actual_amount_paid","mean")
    )
    # churn if last membership period not renewed (approximation)
    last = tx.sort_values(["user_id","membership_expire_date"]).groupby("user_id").tail(1)
    subs["cancel_ts"] = last["membership_expire_date"]
    return subs

def load_logs(path_glob, id_map):
    files = sorted(glob.glob(path_glob))
    dfs = []
    for f in files:
        df = pd.read_csv(f)
        df = df.merge(id_map, on="msno", how="left")
        df["event_ts"] = pd.to_datetime(df["date"], format="%Y%m%d", errors="coerce")
        df = df.rename(columns={"source_system_tab":"source"})
        # Derive 'activate' if total listen time > threshold on a day
        df["event_type"] = "session_start"
        dfs.append(df[["user_id","event_ts","event_type","source"]])
    events = pd.concat(dfs, ignore_index=True)
    return events

def main(conn, members_csv, transactions_csv):
    engine = create_engine(conn, future=True)
    users, id_map = load_members(members_csv)
    subs = load_transactions(transactions_csv, id_map)
    users.to_sql("users", engine, if_exists="append", index=False)
    subs.to_sql("subscriptions", engine, if_exists="append", index=False)
    print(f"Loaded users={len(users)}, subscriptions={len(subs)}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--conn", required=True)
    ap.add_argument("--members_csv", default="data/members_v3.csv")
    ap.add_argument("--transactions_csv", default="data/transactions_v2.csv")
    args = ap.parse_args()
    main(args.conn, args.members_csv, args.transactions_csv)

