"""Interim data build for the 11/23 baseline only. Owner: Tanishk Yadav.

Tianze's data pipeline (cleaning, NYMEX roll calendar, roll-adjusted variants, post-2013 sample) replaces this
file's output. It writes the agreed interface file data/processed/daily_prices.csv:

    date (index), jet ($/gal, EIA Gulf Coast kerosene-type jet fuel spot FOB),
    ho ($/gal, NYMEX HO front month: EIA through 2024-04-05, Yahoo Finance HO=F after), ho_source

No roll adjustment is applied here: the front-month series still jumps when the contract rolls.

Run:  python -m src.hedge.interim_data
"""
from __future__ import annotations

import io
import pathlib
import urllib.request

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
EIA = "https://www.eia.gov/dnav/pet/hist_xls/{}d.xls"
JET, HO = "EER_EPJK_PF4_RGC_DPG", "EER_EPD2F_PE1_Y35NY_DPG"
SPLICE = pd.Timestamp("2024-04-05")


def eia_series(sid: str) -> pd.Series:
    req = urllib.request.Request(EIA.format(sid), headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req, timeout=60).read()
    df = pd.read_excel(io.BytesIO(raw), sheet_name="Data 1", skiprows=2)
    df.columns = ["date", "value"]
    return df.dropna().set_index("date")["value"].astype(float)


def yahoo_front() -> pd.Series:
    import yfinance as yf
    h = yf.Ticker("HO=F").history(start="2023-12-01", auto_adjust=False)["Close"]
    h.index = h.index.tz_localize(None).normalize()
    return h.astype(float)


def build(out: pathlib.Path = ROOT / "data" / "processed" / "daily_prices.csv") -> pd.DataFrame:
    jet, ho_eia, ho_yf = eia_series(JET), eia_series(HO), yahoo_front()
    overlap = pd.concat([ho_eia, ho_yf], axis=1, join="inner").loc[:SPLICE]
    overlap.columns = ["eia", "yahoo"]
    gap = float((overlap["eia"] - overlap["yahoo"]).abs().max())
    assert gap < 0.01, f"EIA and Yahoo HO disagree by {gap:.4f} $/gal on the overlap"
    ho = pd.concat([ho_eia.loc[:SPLICE], ho_yf.loc[ho_yf.index > SPLICE]])
    src = pd.Series("EIA", index=ho.index).where(ho.index <= SPLICE, "Yahoo HO=F")
    df = pd.concat([jet.rename("jet"), ho.rename("ho"), src.rename("ho_source")], axis=1, join="inner").dropna()
    df = df[df.index.dayofweek < 5]
    df.index.name = "date"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out)
    print(f"wrote {out} : {len(df)} days {df.index.min().date()} to {df.index.max().date()}, "
          f"overlap {len(overlap)} days, max EIA vs Yahoo gap {gap:.4f} $/gal")
    return df


if __name__ == "__main__":
    build()
