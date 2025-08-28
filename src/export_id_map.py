# src/export_id_map.py
import argparse
import pandas as pd

def main(members_csv: str, out_csv: str):
    print(f"Reading {members_csv} …")
    m = pd.read_csv(members_csv, usecols=["msno"])
    # Same mapping as ETL: dense integer codes from Pandas categories
    user_id = m["msno"].astype("category").cat.codes
    id_map = pd.DataFrame({"msno": m["msno"], "user_id": user_id})
    # Drop dupes (multiple rows per msno in members are possible)
    id_map = id_map.drop_duplicates("msno").reset_index(drop=True)
    id_map.to_csv(out_csv, index=False)
    print(f"Wrote mapping → {out_csv}  (rows={len(id_map):,})")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--members_csv", default="data/members_v3.csv")
    ap.add_argument("--out_csv", default="data/processed/id_map.csv")
    args = ap.parse_args()
    main(args.members_csv, args.out_csv)
