# Dashboard redesign

## Why

The live dashboard (akwnn.github.io/pet-food-safety) is one of the case studies in Alana's product design portfolio. It works, but it reads like a generated report: a dark header with five identical number boxes, a pulsing green "live" dot, a rainbow of 14 hazard colors and a long scroll of charts. Recruiters coming from the portfolio should see a dashboard that looks designed, puts the main findings first, and matches the portfolio's look.

## Goals

- Look like a polished product dashboard in the style of Alana's two references (soft white cards with large rounded corners on a pale background, a rounded tab bar, one bold colored card, chunky rounded bars, a ring chart, a transaction-style list).
- Headline findings first: the Overview tab answers "what's going on with pet food recalls" in about 30 seconds.
- Cleaner charts and table: fewer colors, labels on the charts, numbers that line up.
- Use the portfolio palette: cobalt `#2364F0` as the one strong color, konbini orange `#F26A21` only for small accents (Salmonella tags, the newest recall, one callout), navy `#2B3A55` text, pale sky blues and hazes for everything secondary.
- Plain, specific copy, the same voice as the README.
- Works on a phone.

## Non-goals and things that must not change

- `scripts/fetch_fda.py`, `scripts/classify.py` and `.github/workflows/refresh.yml` don't change.
- `scripts/pipeline.py` still writes `index.html` by replacing `__DATA__` in `scripts/template.html`. The data shape it injects (`events`, `records`, `cases`, `meta`) stays the same.
- The README STATS block (between `<!-- STATS:START -->` and `<!-- STATS:END -->`) keeps its exact format; the portfolio parses it.
- Still one self-contained HTML file, plain JavaScript and SVG, no build step and no chart library.
- Every number on the page is computed from the data in the browser, so it stays right after each Monday refresh. Nothing is typed in by hand except the sourced outbreak notes and recommendations that are already hand-written today.

## Approved look

The mockup Alana approved ("looks good"): `direction-d` card style. Page background `#EAEFF6` inside a rounded shell, white cards with 24px corners, Manrope font (Helvetica Neue fallback), tabular numbers.

### Header
Paw logo tile in cobalt + "Pet food recalls". Rounded tab bar in the middle. On the right, a pill with "Data through {date}" and a search button that jumps to the All recalls tab with the search box focused.

### Overview tab
1. Title "US pet food recalls, {first year}–{last year}" with one line saying what's covered and that it updates every Monday. A Dogs & cats / Dogs / Cats switch on the right filters every card on this tab.
2. **Recall events card**: total events (big), products covered, events in the last 12 months, and a rounded bar chart of events per year (last 10 years by default, with a switch to all years). The tallest year is cobalt with a dark "peak" label; the current partial year is marked "so far".
3. **Biggest finding card** (solid cobalt): Salmonella share of events, one sentence on how steady that share has been, two small tiles for Class I share and median days to FDA classification.
4. **Hazards card**: ring chart of the top hazards plus "everything else", with Salmonella's share in the middle and a legend with counts. One callout pill for a burst hazard (melamine in 2007).
5. **Product types card**: share of events since 2018 by product type as progress bars, the top one in cobalt with a "#1" tag.
6. **Latest recalls card**: the five newest recall events as a list (company initials in a circle, company, product type and pet, hazard, date). The newest is tinted. Clicking one opens it in All recalls.

### Other tabs
Same card style. Each tab opens with a one- or two-sentence finding in plain words, then its charts.

- **Hazards**: events per year with hazard filter pills (Salmonella in cobalt, others in a short blue ramp, "everything else" grey); Salmonella's share by five-year period; the hazard table (events, products, first–last year, active years, repeat firms, most common product type, Class I share, small timeline).
- **Product types**: product type mix over time; hazard × product type grid (cobalt shades); which pets each hazard hits; recall class by product type.
- **Time to recall**: first sign → recall for the 9 documented outbreaks (with sources), median FDA classification time by year and by hazard, and before/after-2020 distribution.
- **Repeat recalls**: the repeat-episode timeline and firms with the most recall events.
- **All recalls**: the searchable, sortable table with filters (hazard, product type, pet, class, year); clicking a row shows the products and FDA's reason.
- **About the data**: what a quality and food safety team could do with this, plus methods and limits (the current text).

Tabs use the URL hash (`#hazards`, `#all-recalls`, …) so links and the back button work. Hover tooltips stay for detail, but the main point of each chart is readable without hovering.

## Calls I made (Alana can overrule)

- **Tabs, not one long scroll**, to match the references and keep Overview short.
- **Cut two charts**: the "chronic vs burst" bubble chart (log scale, hard to read; its point moves into the Hazards finding text) and the state tile map (weak finding). Everything else is kept and restyled.
- **14 hazard colors → one cobalt + a blue ramp + grey**; orange only for the small accents above. Recall class badges become solid navy (Class I), mid blue (II), pale (III) instead of red/yellow/blue.
- **Manrope** font to match the references; the portfolio itself uses Helvetica.
- **"About the data"** tab holds both the recommendations and the methods.

## Left to the builder

Exact spacing, breakpoints, chart sizes, which hazards get named in the ring chart (top 4 by count), tooltip styling, empty states for filters that match nothing, and short copy edits that keep the README's voice.

## Done means

- `python3 scripts/pipeline.py` rebuilds `index.html` from the new template with no errors and prints the same counts as before; the README STATS block is unchanged in format.
- The page works in a desktop browser and at phone width, with no console errors, and every tab renders.
- Pushed on branch `redesign-dashboard` with a PR (after Alana OKs the push). The refresh workflow is untouched and still green on main.
- A note on whether the portfolio's pet food preview should change.
