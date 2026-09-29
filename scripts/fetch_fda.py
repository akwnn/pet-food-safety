"""Download FDA Enforcement Report recalls (product type = Veterinary / CVM) into data/raw/.

Uses the same public CSV export as the Enforcement Report website
(https://www.accessdata.fda.gov/scripts/ires/). No API key needed.

Usage:
  python3 scripts/fetch_fda.py            # refresh the last 3 classification years (weekly job)
  python3 scripts/fetch_fda.py --full     # re-download every year slice + pre-2012 keyword slices

How it protects the data:
- FDA caps each export at 1,000 rows, so date ranges that hit the cap are split in half.
- Each request is retried with a fresh browser-style session and growing waits.
- A file is replaced only if the download has the expected columns and didn't shrink
  by more than 10%. Otherwise the old file is kept.
- If one slice fails, the others still update.
- The script exits with an error only when FDA can't be reached AND the saved data is
  more than STALE_DAYS old. A short outage just leaves a warning on the run.
Rows are sorted by recall number, so a week with no FDA changes produces no diff.
"""
import csv, glob, io, json, os, sys, time, datetime as dt, urllib.parse, urllib.request, http.cookiejar

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
BASE = "https://www.accessdata.fda.gov/scripts/ires/index.cfm"
CAP = 1000
STALE_DAYS = 45
OLDEST = dt.date(2012, 6, 8)  # earliest classification date the Enforcement Report supports
KEYWORDS = ["dog", "cat", "cat food", "pet", "treat", "feline", "kitten", "puppy", "canine", "chew"]
CLASSES = ["1", "2", "3"]
REQUIRED = {"Product Type", "Event ID", "Recall Number", "Recalling Firm", "State/Province", "Classification",
            "Status", "Product Description", "Reason for Recall", "Recall Initiation Date",
            "Center Classification Date"}
BROWSER_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
IN_ACTIONS = bool(os.environ.get("GITHUB_ACTIONS"))


def note(level, msg):
    """Print a message; on GitHub Actions also show it as an annotation on the run page."""
    print(f"::{level}::{msg}" if IN_ACTIONS else f"{level.upper()}: {msg}")


class Session:
    """A cookie-keeping session that opens FDA's search page before exporting, like a browser."""

    def __init__(self, style=0):
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.headers = {"User-Agent": BROWSER_UA + " pet-food-safety-explorer/1.1",
                        "Accept": "text/csv,text/html,application/xhtml+xml,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.9", "Referer": BASE}
        if style == 1:  # fallback: plain browser user agent, no extra headers
            self.headers = {"User-Agent": BROWSER_UA}
        try:
            self.opener.open(urllib.request.Request(BASE, headers=self.headers), timeout=60).read()
        except Exception as e:
            print(f"  (couldn't open the search page first: {e})")

    def get(self, url):
        resp = self.opener.open(urllib.request.Request(url, headers=self.headers), timeout=180)
        final = resp.geturl()
        text = resp.read().decode("utf-8-sig", errors="replace")
        if not text.startswith("Product Type"):
            raise IOError(f"FDA returned a non-CSV page ({final[:120]})")
        return text


_session = None


def download(url, tries=5):
    """Return (fieldnames, rows). Retries with a new session and longer waits each time."""
    global _session
    last = None
    for i in range(tries):
        try:
            if _session is None:
                _session = Session(style=1 if i >= 3 else 0)
            reader = csv.DictReader(io.StringIO(_session.get(url)))
            rows = list(reader)
            missing = REQUIRED - set(reader.fieldnames or [])
            if missing:
                raise ValueError(f"FDA export is missing columns: {sorted(missing)}")
            return reader.fieldnames, rows
        except ValueError:
            raise  # format change: retrying won't help
        except Exception as e:
            last = e
            _session = None  # start a fresh session next time
            if i < tries - 1:
                wait = [15, 30, 60, 120][min(i, 3)]
                print(f"  attempt {i + 1} failed ({e}); retrying in {wait}s")
                time.sleep(wait)
    raise IOError(f"gave up after {tries} attempts: {last}")


def export_url(desc="", cls=None, dfrom="", dto=""):
    crit = [{"productdescriptiontxt": desc}, {"codeinformation": ""}, {"centercd": ["CVM"]},
            {"centerclassificationtypetxt": cls}, {"firmlegalnam": ""}, {"phasetxt": None},
            {"recalleventid": ""}, {"recallnum": ""}, {"productshortreasontxt": ""},
            {"centerclassificationdtfrom": dfrom}, {"centerclassificationdtto": dto}]
    q = urllib.parse.quote(json.dumps(crit, separators=(",", ":")))
    return f"{BASE}?action=export.getExportCSVResult&criteria={q}&view=AdvancedSearch&page=product"


def fmt(d):
    return d.strftime("%m/%d/%Y")


def fetch_range(a, b):
    """All CVM recalls classified between dates a..b, splitting ranges that hit the export cap."""
    fields, rows = download(export_url(dfrom=fmt(a), dto=fmt(b)))
    if len(rows) >= CAP and a < b:
        mid = a + (b - a) // 2
        f1, r1 = fetch_range(a, mid)
        _, r2 = fetch_range(mid + dt.timedelta(days=1), b)
        return f1, r1 + r2
    if len(rows) >= CAP:
        note("warning", f"{fmt(a)} is still at FDA's {CAP}-row export cap; some rows may be missing")
    return fields, rows


def existing_rows(path):
    if not os.path.exists(path):
        return 0
    with open(path, encoding="utf-8-sig") as fh:
        return sum(1 for _ in csv.DictReader(fh))


def save(name, fields, rows):
    """Write rows sorted by recall number. Keep the old file if the new one shrank by >10%."""
    seen, uniq = set(), []
    for r in rows:
        k = (r.get("Recall Number") or "").strip().upper()
        if k and k in seen:
            continue
        seen.add(k)
        uniq.append(r)
    path = os.path.join(RAW, name)
    before = existing_rows(path)
    if before >= 20 and len(uniq) < 0.9 * before:
        note("warning", f"{name}: FDA returned {len(uniq)} rows vs {before} saved; kept the saved file")
        return False
    uniq.sort(key=lambda r: ((r.get("Recall Number") or "").strip().upper(), r.get("Event ID", "")))
    tmp = path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(uniq)
    os.replace(tmp, path)
    print(f"  {name}: {len(uniq)} rows")
    return True


def newest_saved_date():
    newest = None
    for f in glob.glob(os.path.join(RAW, "*.csv")):
        with open(f, encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                for col in ("Center Classification Date", "Report Date", "Recall Initiation Date"):
                    try:
                        d = dt.datetime.strptime((r.get(col) or "").strip(), "%m/%d/%Y").date()
                    except ValueError:
                        continue
                    if d <= dt.date.today() and (newest is None or d > newest):
                        newest = d
    return newest


def main():
    full = "--full" in sys.argv
    os.makedirs(RAW, exist_ok=True)
    today = dt.date.today()
    first_year = OLDEST.year if full else today.year - 2
    print(f"Refreshing classification years {first_year}-{today.year}" + (" + keyword slices" if full else ""))

    jobs = []
    for y in range(first_year, today.year + 1):
        a, b = max(dt.date(y, 1, 1), OLDEST), min(dt.date(y, 12, 31), today)
        jobs.append((f"v{y}.csv", lambda a=a, b=b: fetch_range(a, b)))
    if full:
        # Records classified before June 2012 have no classification date, so they can
        # only be reached by product-description keyword x recall class.
        for kw in KEYWORDS:
            for code in CLASSES:
                jobs.append((f"k_{kw.replace(' ', '_')}_{code}.csv",
                             lambda kw=kw, code=code: download(export_url(desc=kw, cls=[code]))))

    ok, failed = 0, []
    for name, job in jobs:
        try:
            fields, rows = job()
            if save(name, fields, rows):
                ok += 1
        except ValueError as e:  # FDA changed the export format: stop and alert
            note("error", f"{name}: {e}")
            sys.exit(1)
        except Exception as e:
            failed.append(name)
            note("warning", f"{name}: couldn't download ({e}); kept the saved file")
        time.sleep(2)  # be polite to FDA's server

    newest = newest_saved_date()
    age = (today - newest).days if newest else None
    summary = (f"Updated {ok} of {len(jobs)} FDA export slices. Newest date in the saved data: "
               f"{newest} ({age} days old).")
    print(summary)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as fh:
            fh.write(summary + ("\n\nFailed slices: " + ", ".join(failed) if failed else "") + "\n")

    if failed and ok == 0:
        if age is None or age > STALE_DAYS:
            note("error", f"FDA couldn't be reached and the saved data is {age} days old "
                          f"(limit {STALE_DAYS}). The dashboard is out of date.")
            sys.exit(1)
        note("warning", f"FDA couldn't be reached this run. Keeping saved data ({age} days old); "
                        f"will try again next week.")


if __name__ == "__main__":
    main()
