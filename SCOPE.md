# Does new construction lower nearby rents? — project scope

Scoped against real pulls on 2026-08-23. Every number below came from the actual data,
not from an estimate.

---

## Verdict from the feasibility pull

The project is viable, but **not as the design I first proposed**. Three things changed:

1. **Treatment is continuous and repeated, not staggered-binary.** Long Island City (11101)
   takes a supply shock in 9 separate years; 11201 in 9; 10018 in 5. Units do not "adopt
   treatment once and stay treated", so Callaway–Sant'Anna staggered DiD is the wrong
   estimator. Use **continuous/dose DiD** (Callaway, Goodman-Bacon & Sant'Anna 2024).
2. **The ZIP-level outcome is coarse, and a descriptive TWFE pass already returns a precise
   zero** (below). That is a result, not a failure — but the project has to be framed as
   *bounding* a ZIP-wide effect, not detecting a building-level one.
3. **ZORI coverage is missing exactly where the interesting non-luxury shocks are.** This is
   the most important finding of the recon and it belongs in the README, not a footnote.

## The identification problem, stated honestly

Developers build where rents are *already rising*. So the naive comparison mixes a positive
selection effect with whatever the supply effect is, and a measured zero could be either "no
effect" or "two effects cancelling". Anything that doesn't confront this is not worth writing.

Three defences, in increasing order of credibility:

- **Event-study pre-trends.** Estimate leads as well as lags. If treated ZIPs are already on a
  differential trend 8 quarters before completion, the design is dead and you say so.
- **Permit-date timing.** Completion date is endogenous to the market (developers slow down in
  downturns). Permit issuance is 2–5 years earlier. Define expected completion from
  `datepermit` plus typical lag, and use realised completion timing variation that is plausibly
  driven by construction delay rather than market conditions.
- **Dose within treated ZIPs only.** Drop never-treated ZIPs entirely and compare
  large-dose to small-dose treated ZIPs. Kills the "developers pick good ZIPs" story, since all
  units are ZIPs developers picked; keeps only the intensity margin.

## Data (all verified fetchable, no auth, 2026-08-23)

| Piece | Source | Verified |
|---|---|---|
| Housing completions | NYC HousingDB project-level, Socrata `br6q-ssj3` | 30,033 jobs with net unit gain, completion dates 2012–2025, lat/lon + BBL |
| Rent index | Zillow ZORI **ZIP-level** `Zip_zori_uc_sfrcondomfr_sm_month.csv` | 9.9 MB, 139 months (2015-01 to 2026-07), 163 NYC ZIPs |
| Housing stock denominator | NYC PLUTO, Socrata `64uk-42ks` | 858,602 lots; 3,741,864 residential units across 185 ZIPs |

**Do not use the Census ACS for the denominator.** `api.census.gov` now returns a "Missing Key"
page; PLUTO gives a better denominator anyway (lot-level, same vintage as the permit data).

**Join route:** HousingDB `bbl` to PLUTO `bbl` to `zipcode`. Matches **99.7% of jobs / 99.2% of
units** — better than a spatial join on lat/lon, and no boundary file needed. HousingDB has no
ZIP column of its own; don't go looking for one.

## Sample, after filters

Filters: `stock >= 3000` residential units (drops commercial ZIPs — 10103 has 59 residential
units and shows a nonsense 293% shock), ZORI coverage >= 60 months, 2015–2025.

| Shock threshold (% of ZIP stock in one year) | ZIP-years | ZIPs | ...with usable ZORI |
|---|---|---|---|
| >1% | 387 | 100 | 67 |
| >2% | 171 | 64 | **42** |
| >3% | 89 | 41 | 27 |
| >5% | 35 | 20 | 14 |

Working panel: **76 ZIPs x 47 quarters = 3,509 observations**, with 36 clean never-treated
control ZIPs. Median ZIP adds 0.9% of stock over any 2-year window; p90 is 4.2%; max 18%.

## What a first pass already shows

Two-way fixed effects, log ZORI on trailing-8-quarter supply as % of stock, ZIP + quarter FE,
SEs clustered by ZIP:

```
d(log rent) per +1% of stock added over 2y:  +0.0004   (se 0.0014, t = 0.29)
implied at p90 dose (4.2% of stock):         +0.2% rent
MDE at 80% power:                            0.0039 log pts per 1% of dose
```

A precise zero. At the p90 dose the design can detect roughly **±1.6%** in rent, so it rules
out large ZIP-wide effects but cannot speak to the -5 to -7% *within-500m* effects that the
building-level literature (Asquith, Mast & Rambachan) reports. Those are compatible: a 500m
effect diluted across a whole ZIP would be far below this detection floor. **Say that
explicitly** — it's the difference between "we found nothing" and "we bounded the thing".

This TWFE number is descriptive only. TWFE is biased with continuous, repeated treatment;
it exists here to prove the pipeline runs end to end, and should be reported as a
specification-check row, never as the headline.

## The coverage finding — put this in the README

ZORI is missing precisely where non-luxury supply shocks land:

| ZIP | Area | Max annual shock | Months of ZORI |
|---|---|---|---|
| 10474, 11239, 11436, 10457, 10470 | Hunts Point, Starrett City, S. Ozone Pk, Tremont, Wakefield | 2.3–5.2% | **0** |
| 11691, 10471, 10472 | Far Rockaway, Riverdale, Soundview | 2.3–5.1% | 1–5 |
| 10452, 10455, 10459, 10453 | Bronx | 2.8–4.0% | 4–5 |
| 11101, 11201, 10018, 10004, 11249 | LIC, Dtwn Bklyn, Hudson Yds, FiDi, Wburg | 7.1–29.4% | 115–139 |

Zillow publishes an index where the rental market is thick and listings are plentiful, which
means **coverage is a function of the outcome**. The estimable sample is therefore market-rate
towers in already-expensive neighbourhoods. Any result generalises to that, and not to housing
supply in general. This is a selection problem in the *outcome's existence*, which is rarer and
more interesting than the usual kind — it's worth a figure of its own (shock size vs. ZORI
coverage, one dot per ZIP).

## Repo layout

```
nyc-supply-rents/
├── README.md
├── requirements.txt
├── data/raw/            # cached API responses, gitignored; manifest.json records URL+date+sha
├── data/interim/        # zip_stock.csv, completions_zip.parquet, panel.parquet
├── scripts/
│   ├── 01_fetch_pluto.py         # paginated, 18 pages x 50k
│   ├── 02_fetch_housingdb.py
│   ├── 03_fetch_zori.py
│   └── 04_build_panel.py
├── src/nycsupply/
│   ├── geo.py           # bbl normalisation + zip join (watch the '.0' float suffixes)
│   ├── panel.py         # dose construction, stock filters
│   └── did.py           # continuous DiD + event study
├── tests/               # synthetic panels with a known planted effect — fine here
└── outputs/figures/
```

Two gotchas already hit, worth encoding in `geo.py`: Socrata returns BBLs and ZIPs as
float-ish strings (`"4114170006"` vs `"1000030001.0"`), and ZIP must be regex-guarded to
`^1[01]\d{3}$` or New Jersey and PO-box ZIPs leak in.

## Falsification / what makes this fail

- **Pre-trends fail.** If leads are significant, report that the design does not identify and
  stop. Do not patch it with more controls.
- **Effect is all composition.** New buildings enter the ZORI basket themselves, and they are
  expensive. A measured rent *rise* may be pure index composition, not market movement.
  Check by testing whether the effect scales with new units as a share of *listings* rather
  than stock; note that ZORI's smoothing and repeat-listing weighting is a partial defence.
- **Power.** With 42 treated ZIPs, only large effects are detectable. Report the MDE
  up front so a null is interpretable.

## Suggested headline

Not "new construction doesn't lower rents". Rather: *"At the ZIP scale, supply shocks up to
18% of stock move rents by less than 2% — and the neighbourhoods where supply might matter
most are the ones no rent index covers."* The second clause is the part nobody else has written.
