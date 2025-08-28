# src/load_events_csv.py
import argparse
import pandas as pd
from sqlalchemy import create_engine

def main(csv_path: str, idmap_csv: str, conn: str):
    # Read events CSV: support old (first_activity_date) and new (event_ts) formats
    peek = pd.read_csv(csv_path, nrows=0)
    if "event_ts" in peek.columns:
        ev = pd.read_csv(csv_path, parse_dates=["event_ts"])
    elif "first_activity_date" in peek.columns:
        ev = pd.read_csv(csv_path, parse_dates=["first_activity_date"])
        ev = ev.rename(columns={"first_activity_date": "event_ts"})
        ev["event_type"] = ev.get("event_type", "activate")
        ev["device"] = ev.get("device", None)
        ev["source"] = ev.get("source", "logs_agg")
    else:
        raise SystemExit("CSV must contain either 'event_ts' or 'first_activity_date'")

    # Ensure required columns exist
    for col, default in [("event_type", "session_start"), ("device", None), ("source", "logs_agg")]:
        if col not in ev.columns:
            ev[col] = default

    print(f"Events rows read: {len(ev):,}")

    # Read id map (msno -> user_id) and join
    idmap = pd.read_csv(idmap_csv)  # columns: msno,user_id
    df = idmap.merge(ev, on="msno", how="inner")

    # Keep only required columns and drop obvious dupes
    df = df[["user_id", "event_ts", "event_type", "device", "source"]].drop_duplicates()

    print(f"Rows to load after join/dedup: {len(df):,}")

    engine = create_engine(conn, future=True)
    df.to_sql(
        "events",
        engine,
        if_exists="append",
        index=False,
        chunksize=10000,
        method="multi",
    )
    print("Loaded events ✅")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="Aggregated events CSV")
    ap.add_argument("--idmap_csv", required=True, help="CSV with msno,user_id mapping")
    ap.add_argument("--conn", required=True, help="SQLAlchemy connection string")
    args = ap.parse_args()
    main(args.csv, args.idmap_csv, args.conn)
