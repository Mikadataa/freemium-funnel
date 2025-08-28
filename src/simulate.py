#!/usr/bin/env python
"""Generate synthetic freemium events and load to Postgres.

Usage:
  python src/simulate.py --n_users 30000 --start 2024-01-01 --months 12 --seed 7     --conn postgresql+psycopg2://postgres:postgres@localhost:5432/analytics
"""
import argparse, random
from datetime import datetime, timedelta
import numpy as np, pandas as pd
from faker import Faker
from sqlalchemy import create_engine

def simulate(n_users, start, months, seed):
    rng = np.random.default_rng(seed)
    fake = Faker()
    start_dt = pd.Timestamp(start)
    end_dt = start_dt + pd.DateOffset(months=months)

    # Users
    user_ids = np.arange(1, n_users+1)
    signup_dates = pd.to_datetime(rng.choice(pd.date_range(start_dt, end_dt, freq="D"), size=n_users))
    channels = rng.choice(["Ads","SEO","Referral","Social","Direct"], size=n_users, p=[0.25,0.2,0.2,0.2,0.15])
    countries = rng.choice(["KZ","CA","US","DE","TR","ES"], size=n_users)
    devices = rng.choice(["iOS","Android","Web"], size=n_users, p=[0.4,0.4,0.2])
    users = pd.DataFrame({
        "user_id": user_ids,
        "signup_ts": signup_dates,
        "channel": channels,
        "country": countries,
        "device": devices
    })

    # Activation probability depends on channel and device
    base_act = {"Ads":0.28,"SEO":0.35,"Referral":0.45,"Social":0.33,"Direct":0.30}
    device_adj = {"iOS":+0.03,"Android":0,"Web":-0.04}
    act_prob = [min(0.95, max(0.01, base_act[c] + device_adj[d])) for c,d in zip(channels, devices)]
    activated = rng.random(n_users) < np.array(act_prob)

    # Subscription probability conditional on activation (+ channel lift)
    base_sub = 0.16
    ch_lift = {"Ads":-0.02,"SEO":+0.01,"Referral":+0.04,"Social":0.0,"Direct":+0.01}
    sub_prob = [min(0.9, max(0.005, base_sub + (0.10 if a else -0.12) + ch_lift[c])) for a,c in zip(activated, channels)]
    subscribed = rng.random(n_users) < np.array(sub_prob)

    # Churn hazard per month (geometric with heterogeneity by device)
    hazard = {"iOS":0.05,"Android":0.07,"Web":0.09}

    events = []
    subs = []
    for uid, sdt, act, sub, dev in zip(user_ids, signup_dates, activated, subscribed, devices):
        # signup event
        events.append(dict(user_id=uid, event_ts=sdt, event_type="signup", device=dev, source="signup"))
        # sessions for 90 days post-signup
        days = pd.date_range(sdt, sdt + pd.Timedelta(days=90), freq="D")
        for day in days:
            if random.random() < (0.20 if act else 0.05):
                events.append(dict(user_id=uid, event_ts=day + pd.Timedelta(hours=int(random.random()*24)), event_type="session_start", device=dev, source="app"))
        if act:
            events.append(dict(user_id=uid, event_ts=sdt + pd.Timedelta(days=int(np.random.exponential(2))), event_type="activate", device=dev, source="onboarding"))
        if sub:
            start_ts = sdt + pd.Timedelta(days=int(np.random.exponential(7)))  # conversion lag
            subs.append(dict(user_id=uid, start_ts=start_ts, plan=random.choice(["FreeTrial","Monthly","Annual"]), price=random.choice([9.99, 12.99, 15.99]), cancel_ts=None))
            # churn
            hazard_p = hazard[dev]
            months_alive = 0
            while months_alive < 12 and random.random() > hazard_p:
                months_alive += 1
            if months_alive>0 and months_alive<12:
                cancel_ts = start_ts + pd.DateOffset(months=months_alive)
                subs[-1]["cancel_ts"] = cancel_ts
                events.append(dict(user_id=uid, event_ts=cancel_ts, event_type="cancel", device=dev, source="billing"))
            # subscribe event
            events.append(dict(user_id=uid, event_ts=start_ts, event_type="subscribe", device=dev, source="billing"))

    events_df = pd.DataFrame(events)
    subs_df = pd.DataFrame(subs)
    return users, events_df, subs_df

def main(n_users, start, months, seed, conn):
    users, events, subs = simulate(n_users, start, months, seed)
    engine = create_engine(conn, future=True)
    users.to_sql("users", engine, if_exists="append", index=False)
    events.to_sql("events", engine, if_exists="append", index=False)
    subs.to_sql("subscriptions", engine, if_exists="append", index=False)
    print(f"Loaded: users={len(users)}, events={len(events)}, subs={len(subs)}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n_users", type=int, default=30000)
    ap.add_argument("--start", type=str, default="2024-01-01")
    ap.add_argument("--months", type=int, default=12)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--conn", type=str, required=True)
    args = ap.parse_args()
    main(args.n_users, args.start, args.months, args.seed, args.conn)
