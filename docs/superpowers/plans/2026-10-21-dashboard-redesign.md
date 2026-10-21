# Dashboard Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `scripts/template.html` with the approved card-style, tabbed dashboard, with every number computed from the injected data.

**Architecture:** One self-contained template. `pipeline.py` keeps replacing `__DATA__` with `{events, records, cases, meta}`. The template has a shared header, six tab panels switched by URL hash, and plain-JS SVG chart helpers.

**Tech Stack:** HTML, CSS, plain JavaScript, inline SVG; Manrope from Google Fonts; Python 3.9+ standard library for the pipeline.

**Spec:** `docs/superpowers/specs/2026-10-21-dashboard-redesign-design.md`

## Global Constraints

- Don't change `scripts/fetch_fda.py`, `scripts/classify.py`, `.github/workflows/refresh.yml`, or the README STATS block format.
- `pipeline.py` output contract: `index.html` with `__DATA__` replaced; the injected JSON shape is unchanged.
- Palette: cobalt `#2364F0`, orange `#F26A21` (accents only: Salmonella tags, newest recall, one callout), navy `#2B3A55`, hazes `#C9DBF0` / `#D6E6F5` / `#F3F8FD`, page `#EAEFF6`.
- No hard-coded data numbers in the template; the outbreak notes and recommendations stay hand-written.
- One HTML file, no chart library, no build step.

## Review Focus

- Species switch set to Cats: every Overview card must recompute (ring, bars, product types, latest list); no NaN on low counts.
- A filter combination in All recalls that matches nothing: show "No recalls match these filters", not an empty table.
- Opening `index.html#all-recalls` directly, or using the back button, lands on the right tab.
- Phone width (375px): no horizontal page scroll; wide charts and the table scroll inside their card.
- Charts drawn while their tab is hidden have zero width: draw on tab show and on resize.

---

### Task 1: New template, Overview tab

**Files:**
- Modify: `scripts/template.html` (full rewrite)

**Interfaces:**
- Produces: `show(tab)` that switches panels from `location.hash`; helpers `el()`, `tip()`, `untip()`, `median()`, `fmt()`, `esc()` kept with their current signatures; `openRecall(id)` that switches to All recalls and expands that row.

- [ ] Write the shell, header, tab bar, and Overview cards per the spec, computed from `E` filtered by the species switch (`Dog`, `Cat`, or all; "Dog & cat" events count in both).
- [ ] Run `python3 scripts/pipeline.py`. Expected: `Data through Oct 8, 2026.` and `… -> 1912 pet products -> 330 recall events`.
- [ ] Open the page; check that the Overview numbers match the README STATS block (330, 1,912, 50%, 71%, 73, 23) and that the console has no errors.

### Task 2: Hazards, Product types, Time to recall, Repeat recalls tabs

- [ ] Port these charts from the old template, restyled: years by hazard (with pills), Salmonella share by period, hazard table, product type mix, hazard × product grid, pets by hazard, class by product type, outbreak timeline + notes, lag by year, lag by hazard, lag before/after 2020, repeat timeline, top firms. Drop the bubble chart and the tile map.
- [ ] Each tab opens with its finding sentence, computed as in the old `writeFindings`.
- [ ] Check each tab in the browser at desktop and 375px widths with no console errors.

### Task 3: All recalls and About the data

- [ ] Port the explorer table (search, five filters, sorting, expandable rows) with an empty state; the header search button focuses its search box. Port recommendations, methods and footer.
- [ ] Check that searching "Morasch" finds the Aug 28, 2026 event and that clicking it shows its products.

### Task 4: Ship

- [ ] Run the pipeline and confirm `git diff README.md` shows nothing; commit the template, `index.html`, spec and plan on `redesign-dashboard`.
- [ ] Ask Alana before pushing; open the PR; confirm the refresh workflow on main is still green.
