import argparse
import pandas as pd

def main(input_csv, out_csv, sample_users=0.1):
    print(f"Reading logs from {input_csv}...")
    # Read in chunks so we don’t blow memory
    chunks = pd.read_csv(input_csv, chunksize=1_000_000)

    all_rows = []
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i}...")
        # convert date
        chunk["date"] = pd.to_datetime(chunk["date"], format="%Y%m%d", errors="coerce")

        # derive active month
        chunk["month"] = chunk["date"].dt.to_period("M")

        # keep only msno, month
        g = chunk.groupby(["msno", "month"]).size().reset_index(name="sessions")

        # make event_ts = first day of month
        g["event_ts"] = g["month"].dt.to_timestamp()
        g["event_type"] = "session_start"
        g["device"] = None
        g["source"] = "logs_agg"

        all_rows.append(g[["msno", "event_ts", "event_type", "device", "source"]])

    df = pd.concat(all_rows).drop_duplicates()

    # sample users if requested
    if 0 < sample_users < 1:
        unique_users = df["msno"].unique()
        sample = pd.Series(unique_users).sample(frac=sample_users, random_state=42)
        df = df[df["msno"].isin(sample)]
        print(f"Sampled {len(sample)} users → {len(df)} events")

    df.to_csv(out_csv, index=False)
    print(f"Saved aggregated events → {out_csv}, rows={len(df):,}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input_csv", required=True)
    ap.add_argument("--out_csv", required=True)
    ap.add_argument("--sample_users", type=float, default=0.1)
    args = ap.parse_args()
    main(args.input_csv, args.out_csv, args.sample_users)
