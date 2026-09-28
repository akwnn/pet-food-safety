# Pet Food Safety Signal Explorer

[![Weekly FDA data refresh](https://github.com/akwnn/pet-food-safety/actions/workflows/refresh.yml/badge.svg)](https://github.com/akwnn/pet-food-safety/actions/workflows/refresh.yml)

**Live dashboard: https://akwnn.github.io/pet-food-safety/**

**Which hazards keep coming back in pet food, which product formats they cluster in, and how long it takes to get from the first warning sign to a recall.**

An interactive dashboard built on **every FDA Center for Veterinary Medicine recall of dog, cat and pet food, treats and supplements** in the FDA Enforcement Report, plus sourced first-signal-to-recall timelines for major outbreaks. The data **refreshes itself every week** through GitHub Actions.

## Live numbers
<!-- STATS:START -->
| Data through | **Sep 24, 2026** (auto-refreshed weekly) |
|---|---|
| Pet food recall events | 329 (2003–2026) |
| Recalled products (SKUs) | 1,910 |
| Salmonella share of events | 50% |
| Class I (most serious) share | 71% |
| Median days, recall start → FDA classification | 74 |
| Recall events in the last 12 months | 24 |
| Most recent recall event | 2026-08-28: Morasch Meats (Salmonella) |
<!-- STATS:END -->

## Key findings (Sept 2026 analysis)
- **Salmonella, the constant hazard:** 50% of all pet food recall events (164 of 329), and 49–66% in every five-year window since 2008.
- **Chemical hazards, rare but in bursts:** melamine (all 18 events in 2007), aflatoxin (2011 and 2020), vitamin D excess (12 of 20 events in 2018–2021).
- **Recall size, the ingredient signature:** a melamine event averaged ~25 products vs ~4.6 for Salmonella, which is what it looks like when one contaminated ingredient flows into many brands.
- **Listeria and aflatoxin, each tied to one format:** 16 of 19 Listeria events are raw/frozen, and 11 of 11 aflatoxin events are dry kibble.
- **Raw food, the new front line:** raw/frozen/freeze-dried has been the largest recall format since 2018 (38% of events).
- **Nutrient errors, mostly a cat problem:** 13 of 18 nutrient deficiency/excess events are cat foods, and 10 involve low thiamine (vitamin B1).
- **Time to recall, set by the signal type:** a lab positive or acute linked illness led to recalls in 1–34 days. Diffuse signals took 6 months (human Salmonella cases linked in hindsight) to about 5.5 years (China jerky treats, agent never identified).
- **Public record, much faster since 2020:** FDA's median time from recall start to classification fell from ~140 days (2012–2019) to ~32 days (2020–2026).
- **Repeat recalls, mostly Salmonella:** 30 firm/hazard pairs recurred in separate episodes more than 90 days apart, and 19 of those were Salmonella, mostly at small raw and treat makers.

## What's in the dashboard
- **Recall trend, header sparkline:** events per year with the melamine, jerky-residue and vitamin D spikes labeled.
- **Q1 recurring hazards, four views:** stacked yearly bars, a chronic-vs-burst bubble chart, Salmonella share by era, and a scorecard with per-hazard timelines.
- **Q2 clusters, four views:** hazard × format heatmap, format mix over time, species by hazard, and recall severity by format.
- **Q3 time to recall, four views:** sourced outbreak timelines (log scale), FDA classification lag by year and by hazard, and a before/after-2020 lag distribution.
- **Q4 repeat recalls, three views:** repeat-episode timeline by firm, a US tile map of recalling firms, and top firms by hazard.
- **Explorer, every recall:** search and filter all 329 events, then click a row for the products and FDA's stated reason.

## Why not openFDA adverse events?
openFDA's `animalandveterinary/event` endpoint (1.36M reports) covers **animal drugs only**, and brand names are masked as "MSK". It contains no pet food complaints. Pet food complaints go to FDA's Safety Reporting Portal, which isn't published as bulk data. openFDA's `food/enforcement` endpoint also leaves out the Veterinary product type (only ~100 pet items appear there, misfiled under Food). So this project:
- uses the **FDA Enforcement Report (iRES)**, product type *Veterinary*, for recalls, and
- builds the first-signal-to-recall lens from **FDA investigation pages, FDA warning letters and CDC outbreak reports** (`data/outbreak_timelines.json`, each with a source URL).

Measuring that gap is part of the finding: for several major recalls (Hill's 2019 vitamin D, the 2018 vitamin D dry foods, the 2017–18 thyroid hormone recalls), firms say they acted on "complaints" but no public record gives the complaint dates.

## How it stays current
- **Download, no API key:** `scripts/fetch_fda.py` requests the Enforcement Report's public CSV export for product type *Veterinary*. Any date range that hits FDA's 1,000-row export cap is split in half automatically.
- **Schedule, every Monday:** `.github/workflows/refresh.yml` runs the download and `scripts/pipeline.py` on GitHub Actions, then commits only if the recall data actually changed.
- **Publishing, GitHub Pages:** each commit republishes the dashboard, so the live link always shows the latest data.
- **Freshness, shown on the page:** the "data through" date is calculated from the newest date in FDA's records, not typed by hand.
- **Manual refresh, one command:** `python3 scripts/fetch_fda.py && python3 scripts/pipeline.py` (add `--full` to re-download all history).

## Repo layout
```
index.html                      self-contained dashboard (open in any browser)
data/raw/*.csv                  FDA Enforcement Report exports (Veterinary), by year + pet keyword × recall class
data/recalled_products.csv      1,910 pet products with hazard / format / species labels
data/recall_events.csv          329 recall events (grouped by FDA event ID) with FDA classification lag
data/outbreak_timelines.json    sourced first-signal -> recall timelines
scripts/fetch_fda.py            downloads FDA Enforcement Report exports (weekly, no API key)
scripts/pipeline.py             raw CSVs -> filtered, classified data -> index.html + README stats
.github/workflows/refresh.yml   weekly GitHub Actions refresh
scripts/classify.py             hazard / format / species keyword rules
scripts/template.html           dashboard template (vanilla JS + SVG, no dependencies)
```

## Reproduce
```bash
python3 scripts/fetch_fda.py --full   # download every FDA veterinary recall slice (about 5 minutes)
python3 scripts/pipeline.py           # rebuild the data files, dashboard and README stats
```
Python 3.9+, standard library only. Records classified before June 2012 have no classification date, so they're pulled by product-description keyword × recall class.

## Methods and limits
- **Pet filter, keyword-based:** keeps records mentioning pet terms. Drops veterinary drugs and devices (NDC, tablets, injectables, test kits, sterility or potency issues) and livestock feed.
- **Hazard, format and species, rule-based labels:** hazard uses ordered keyword rules on FDA's "reason for recall" text. Format and species use keyword rules on the product description. Event labels are the most common label across the event's products. The rules are transparent but imperfect, so spot-check before quoting exact counts.
- **FDA classification lag, defined:** Center Classification Date − Recall Initiation Date (earliest per event).
- **Recall counts, detection not incidence:** they reflect detection and enforcement effort, not true contamination rates. For example, FDA's targeted raw pet food sampling in the 2010s raised raw-food recall counts. Market withdrawals and non-US recalls aren't included.

*Data: U.S. FDA Enforcement Report, FDA CVM, CDC. Public and unvalidated. Not affiliated with FDA or any pet food company.*
