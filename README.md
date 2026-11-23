# FRE-GY 6921 Term Group Project: Group 3

Cross-hedging U.S. Gulf Coast jet fuel with NY Harbor ULSD (HO) futures.

Members: Tanishk Yadav (ty2766), Tianze Xia (tx717), Rohit Kakumani (vk2851)

Instructor: Bruno G. Kamdem, Ph.D. | NYU Tandon, Department of Finance and Risk Engineering

## Overview
<!-- one paragraph, written by the group -->

## Setup
Python 3.12 or newer.

```bash
git clone https://github.com/tanishhky/fre6921-jet-fuel-cross-hedge.git
cd fre6921-jet-fuel-cross-hedge
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Data access
<!-- series IDs, links, how to download, retrieval dates -->

## How to run
<!-- other members add their commands here -->

Hedge engine and baseline (Tanishk):
```bash
python -m src.hedge.interim_data     # builds data/processed/daily_prices.csv (interim, until the data pipeline lands)
python -m src.hedge.run_baseline     # results/baseline_*.csv and figures/baseline_rolling_h.png
pytest -q                            # includes the no-lookahead tests
```

## Repository layout
- `src/` Python code
- `data/` downloaded data (not committed, see `.gitignore`)
- `notebooks/` analysis and live demo
- `tests/` tests (run with `pytest`)
- `excel/` Excel cross-check workbook
- `docs/` proposals and report PDFs
- `figures/` generated figures
- `TODO.md` task list and owners

## Results
<!-- tables and figures mapped to the code that produced them -->
