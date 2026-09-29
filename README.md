# Pet food recall explorer

[![Weekly FDA data refresh](https://github.com/akwnn/pet-food-safety/actions/workflows/refresh.yml/badge.svg)](https://github.com/akwnn/pet-food-safety/actions/workflows/refresh.yml)

Live dashboard: https://akwnn.github.io/pet-food-safety/

I built this to answer three questions pet owners can't easily answer: which pet food hazards keep coming back, which kinds of products they show up in, and how long it takes to go from the first sick pet to a recall.

The dashboard covers every dog food, cat food, pet treat and pet supplement recall in FDA's Enforcement Report since 2003. A GitHub Actions job downloads new FDA data every Monday and rebuilds the page.

## Current numbers
<!-- STATS:START -->
| | |
|---|---|
| Data through | Sep 24, 2026 (updates every Monday) |
| Pet food recall events | 329 (2003–2026) |
| Recalled products (SKUs) | 1,910 |
| Salmonella share of events | 50% |
| Class I (most serious) share | 71% |
| Median days, recall start → FDA classification | 74 |
| Recall events in the last 12 months | 24 |
| Most recent recall event | 2026-08-28: Morasch Meats (Salmonella) |
<!-- STATS:END -->

## What I found (September 2026)
- Salmonella caused 164 of 329 recall events (50%). Its share stayed between 49% and 66% in every five-year period since 2008.
- Chemical hazards came in clusters. All 18 melamine recalls were in 2007, aflatoxin recalls bunched up in 2011 and 2020, and 12 of 20 vitamin D recalls came between 2018 and 2021.
- A melamine recall covered about 25 products on average, compared with 4.6 for Salmonella, because one contaminated ingredient went into many brands.
- 16 of 19 Listeria recalls were raw or frozen food. All 11 aflatoxin recalls were dry kibble.
- Raw, frozen and freeze-dried food has been the most-recalled product type since 2018 (38% of events).
- 13 of 18 vitamin and mineral recalls were cat food. 10 were for low thiamine (vitamin B1), and 9 of those were cat food.
- In the 9 outbreaks where I found dates, recalls came 1 to 34 days after a positive lab test or an obvious poisoning. When the first signs were scattered complaints, it took from 181 days (Salmonella in people, linked to the food later) to about 5.5 years (jerky treats from China, cause never found).
- FDA's median time to classify a recall after a company starts it fell from about 140 days (2012–2019) to about 32 days (2020–2026).
- 30 companies recalled products for the same hazard again at least 90 days after an earlier recall. 19 of those repeats were Salmonella, mostly at small raw food and treat makers.

The page has a section for each question, a list of the newest recalls, and a searchable table of every recall event. Click a row to see the products and FDA's stated reason.

## Why this doesn't use openFDA adverse event reports
I started with openFDA's animal adverse event data (1.36 million reports), but it only covers animal drugs, and brand names are hidden as "MSK". Pet food complaints go to FDA's Safety Reporting Portal, which isn't published in bulk. openFDA's recall endpoint also skips the Veterinary product type, so only about 100 pet recalls show up there.

So I used the FDA Enforcement Report for recalls. For the first-sign-to-recall timelines, I took dates from FDA investigation pages, FDA warning letters and CDC outbreak reports, with a source link for each in `data/outbreak_timelines.json`. For some big recalls (Hill's 2019 vitamin D, the 2018 vitamin D dry foods, the 2017–18 thyroid hormone recalls), the companies said they acted on complaints, but I couldn't find a public record of when those complaints came in.

## How the data updates
`scripts/fetch_fda.py` downloads the Enforcement Report's public CSV export, which doesn't need an API key. FDA caps each export at 1,000 rows, so the script splits any date range that hits the cap. Every Monday, `.github/workflows/refresh.yml` runs the download and `scripts/pipeline.py`, and commits only if FDA's data changed. GitHub Pages republishes the dashboard after each commit. The "data through" date on the page is the newest date in FDA's records.

If FDA's site is down or turns away the request, the script retries with a fresh session, keeps the saved data, and tries again the next Monday. It only fails the run, which sends a GitHub email, if the saved data is more than 45 days old. It also won't replace a file when FDA's columns change or a download comes back with noticeably fewer rows, and the pipeline refuses to publish a dashboard built from fewer than 1,500 pet recall records. GitHub pauses scheduled jobs in public repos after 60 days without activity, so the job re-enables its own schedule each time it runs.

To refresh by hand (Python 3.9+, standard library only):
```bash
python3 scripts/fetch_fda.py          # last 3 years
python3 scripts/fetch_fda.py --full   # all history, about 5 minutes
python3 scripts/pipeline.py           # rebuild the data files, dashboard and the numbers above
```

## Files
```
index.html                      the dashboard (one file, opens in any browser)
data/raw/*.csv                  FDA Enforcement Report exports, product type Veterinary
data/recalled_products.csv      every recalled pet product, with hazard, product type and species labels
data/recall_events.csv          products grouped into recall events by FDA event ID
data/outbreak_timelines.json    first-sign-to-recall dates for 9 outbreaks, with sources
scripts/fetch_fda.py            downloads the FDA exports
scripts/pipeline.py             builds the data files, dashboard and README numbers
scripts/classify.py             keyword rules for hazard, product type and species
scripts/template.html           dashboard template (plain JavaScript and SVG)
.github/workflows/refresh.yml   the Monday refresh job
```

## Methods and limits
- I kept records that mention dogs, cats, pets, puppies, kittens, treats or chews, and dropped animal drugs, vet devices and livestock feed.
- Hazard labels come from keyword rules on FDA's "reason for recall" text. Product type and species come from the product description. Each recall event gets the most common label among its products. The rules miss some cases, so check the records before quoting an exact count.
- FDA classification lag is the Center Classification Date minus the Recall Initiation Date, using the earliest dates in each event.
- Records classified before June 2012 have no classification date, so the script finds them by searching product descriptions for pet keywords.
- Recall counts measure what got caught, not how often contamination happens. FDA's targeted sampling of raw pet food in the 2010s, for example, raised raw food recall counts. Market withdrawals and recalls outside the US aren't included.

Data from the U.S. FDA Enforcement Report, FDA CVM and CDC. Not affiliated with FDA or any pet food company.
