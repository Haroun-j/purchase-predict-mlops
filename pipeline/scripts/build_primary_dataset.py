"""Build the session/product table used by the pipeline from raw e-commerce events.

The raw file has one row per event with the columns
event_time, event_type, product_id, category_id, category_code, brand, price,
user_id, user_session. The output has one row per (session, product) pair that
reached the cart or purchase stage, with the target `purchased` and the 13
features used by the model. It is what the `loading` pipeline expects to find
in data/03_primary/primary.csv (or in the GCS folder configured in conf/local).

Usage:
    python scripts/build_primary_dataset.py data/01_raw/events.csv
    python scripts/build_primary_dataset.py data/01_raw/events.csv --output data/03_primary/primary.csv
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

OUTPUT_COLUMNS = [
    "product_id",
    "brand",
    "price",
    "user_id",
    "user_session",
    "purchased",
    "num_views_session",
    "num_views_product",
    "category",
    "sub_category",
    "hour",
    "minute",
    "weekday",
    "duration",
    "num_prev_sessions",
    "num_prev_product_views",
]


def build_primary(events: pd.DataFrame) -> pd.DataFrame:
    """Turn raw events into one row per (session, product) with the model features."""
    df = events.loc[~events["user_session"].isna()].copy()

    # Target: the product was bought at some point during the session.
    df["purchased"] = np.where(df["event_type"] == "purchase", 1, 0)
    df["purchased"] = df.groupby(["user_session", "product_id"])["purchased"].transform("max")

    # Browsing intensity, for the whole session and for this product.
    is_view = np.where(df["event_type"] == "view", 1, 0)
    df["num_views_session"] = is_view
    df["num_views_session"] = df.groupby("user_session")["num_views_session"].transform("sum")
    df["num_views_product"] = is_view
    df["num_views_product"] = df.groupby(["user_session", "product_id"])["num_views_product"].transform("sum")

    # category_code looks like "electronics.smartphone".
    parts = df["category_code"].str.split(".", expand=True)
    df["category"] = parts[0]
    df["sub_category"] = parts[1] if 1 in parts.columns else np.nan

    df["event_time"] = pd.to_datetime(df["event_time"], utc=True)
    df["hour"] = df["event_time"].dt.hour
    df["minute"] = df["event_time"].dt.minute
    df["weekday"] = df["event_time"].dt.dayofweek

    # Session duration in seconds, from the first to the last event.
    bounds = df.groupby("user_session")["event_time"].agg(["min", "max"]).reset_index()
    bounds["duration"] = (bounds["max"] - bounds["min"]).dt.seconds

    dataset = (
        df.sort_values("event_time")
        .drop_duplicates(["event_type", "product_id", "user_id", "user_session"])
    )
    dataset = dataset.loc[dataset["event_type"].isin(["cart", "purchase"])].merge(
        bounds[["user_session", "duration"]], how="left", on="user_session"
    )

    # How many earlier sessions this user had before the current one.
    prev_sessions = (
        dataset[["user_id", "user_session", "event_time"]]
        .sort_values("event_time")
        .groupby(["user_id", "user_session"])
        .first()
        .reset_index()
    )
    prev_sessions["num_prev_sessions"] = prev_sessions.sort_values("event_time").groupby("user_id").cumcount()
    dataset = dataset.merge(prev_sessions[["user_session", "num_prev_sessions"]], how="left", on="user_session")

    # How many earlier sessions in which this user already looked at this product.
    prev_views = (
        dataset[["user_id", "user_session", "event_time", "product_id"]]
        .sort_values("event_time")
        .groupby(["user_id", "user_session", "product_id"])
        .first()
        .reset_index()
    )
    prev_views["num_prev_product_views"] = (
        prev_views.sort_values("event_time").groupby(["user_id", "product_id"]).cumcount()
    )
    dataset = dataset.merge(
        prev_views[["user_session", "product_id", "num_prev_product_views"]],
        how="left",
        on=["user_session", "product_id"],
    )

    dataset = (
        dataset.sort_values("event_time")
        .drop_duplicates(["user_session", "product_id", "purchased"])
        .drop(["event_time", "event_type", "category_code", "category_id"], axis=1)
    )
    return dataset[OUTPUT_COLUMNS].reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("events_csv", type=Path, help="raw events CSV (view / cart / purchase rows)")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/03_primary/primary.csv"),
        help="where to write the primary table (default: data/03_primary/primary.csv)",
    )
    args = parser.parse_args()

    events = pd.read_csv(args.events_csv)
    primary = build_primary(events)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    primary.to_csv(args.output, index=False)

    positives = primary["purchased"].mean()
    print(f"{len(events)} events -> {len(primary)} session/product rows ({positives:.1%} purchased)")
    print(f"written to {args.output}")


if __name__ == "__main__":
    main()
