# TODO and task allocation (Group 3)

Owners follow the Task Distribution Matrix in the Initial Proposal. Tick a box only when the work is committed to this repo.

## Milestones
| Date | Milestone | Owner(s) |
|---|---|---|
| Mon Nov 23 | Revised proposal: feedback table, working baseline with real numbers, repo with commits from every member | All |
| Mon Nov 30 | Full models implemented and validated, all tables and figures produced | All |
| Thu Dec 3 | Report draft circulated, code frozen except bug fixes | All |
| Mon Dec 7 | Final report submitted, repo tagged `v1.0-final` | All |
| Dec 7 or Dec 14 | Presentation and live demo | All |
| Mon Dec 14 | Confidential peer evaluations (individual) | Each member |

## Tanishk Yadav: hedge model lead
- [ ] Hedge-ratio engine in `src/`: OLS minimum-variance ratio, hedge effectiveness
- [ ] Rolling out-of-sample framework with an explicit decision date on every data read (no lookahead)
- [ ] Test in `tests/`: add future data, check past hedge ratios are unchanged
- [ ] Hedge-effectiveness tables by horizon and window, with bootstrap confidence intervals
- [ ] Baseline for 11/23: no hedge vs 1:1 vs minimum-variance on real data
- [ ] Revised proposal: Problem Statement, Methodology, feedback table

## Tianze Xia: data and diagnostics lead
- [ ] Download scripts in `src/` for EIA jet fuel, EIA HO and Yahoo HO=F, plus data-access steps in the README
- [ ] Cleaning: weekday filter, common dates, splice at 2024-04-05, check the 66-day overlap
- [ ] Roll handling: NYMEX expiry calendar, changes within a contract, variants with roll days dropped and back-adjusted
- [ ] Basis and roll diagnostics tables (mean, standard deviation, autocorrelation, roll frequency and size)
- [ ] Post-2013 sensitivity (HO was heating oil until May 2013)
- [ ] Revised proposal: Data Sources and Tools sections

## Rohit Kakumani: scenario and demo lead
- [ ] Stress scenarios for 2008, 2020, 2022 and 2026: hedged vs unhedged fuel cost
- [ ] CME margin levels for HO (source and retrieval date) and the variation margin calculation
- [ ] Excel cross-check of one estimation window in `excel/`
- [ ] Live demo notebook in `notebooks/`: change window, horizon or hedge ratio and recompute effectiveness and margin
- [ ] Revised proposal: Market Context and Expected Outcomes

## Everyone
- [ ] First commit under your own GitHub account by Mon Nov 16
- [ ] Tanishk: add Tianze and Rohit as collaborators (needs their GitHub usernames)
- [ ] Weekly group meeting, notes in `docs/`
- [ ] README: overview, data access, how to run, map from each table and figure to its code
- [ ] AI Tool Usage Disclosure for the final report appendix
- [ ] Tag `v1.0-final` by Dec 7
