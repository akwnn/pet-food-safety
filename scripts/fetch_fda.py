"""Download FDA Enforcement Report recalls (product type = Veterinary / CVM) into data/raw/.

Uses the same public CSV export as the Enforcement Report website
(https://www.accessdata.fda.gov/scripts/ires/). No API key needed.

Usage:
  python3 scripts/fetch_fda.py            # refresh the last 3 classification years (weekly job)
  python3 scripts/fetch_fda.py --full     # re-download every year slice + pre-2012 keyword slices

Each export is capped at 1,000 rows by FDA, so any date range that hits the cap
is split in half and re-requested until every slice is under the cap.
Files are written only after a download succeeds, and rows are sorted by recall
number so an unchanged week produces no diff.
"""
import csv, io, json, os, sys, time, datetime as dt, urllib.parse, urllib.request, http.cookiejar

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
BASE = "https://www.accessdata.fda.gov/scripts/ires/index.cfm"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36 pet-food-safety-explorer/1.0")
HEADERS = {"User-Agent": UA, "Accept": "text/csv,text/html,application/xhtml+xml,*/*;q=0.8",
           "Accept-Language": "en-US,en;q=0.9", "Referer": BASE}


class _LogRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        print(f"  redirect {code} -> {newurl[:160]}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


# one session with cookies, like a browser: open the search page first, then export
_JAR = http.cookiejar.CookieJar()
_OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_JAR), _LogRedirects())
_PRIMED = False


def _prime():
    global _PRIMED
    if not _PRIMED:
        try:
            _OPENER.open(urllib.request.Request(BASE, headers=HEADERS), timeout=60).read()
        except Exception as e:
            print(f"  (could not open search page first: {e})")
        _PRIMED = True
CAP = 1000
OLDEST = dt.date(2012, 6, 8)  # earliest classification date the Enforcement Report supports
KEYWORDS = ["dog", "cat", "cat food", "pet", "treat", "feline", "kitten", "puppy", "canine", "chew"]
CLASSES = {"1": "Class I", "2": "Class II", "3": "Class III"}


def export_url(desc="", cls=None, dfrom="", dto=""):
    crit = [{"productdescriptiontxt": desc}, {"codeinformation": ""}, {"centercd": ["CVM"]},
            {"centerclassificationtypetxt": cls}, {"firmlegalnam": ""}, {"phasetxt": None},
            {"recalleventid": ""}, {"recallnum": ""}, {"productshortreasontxt": ""},
            {"centerclassificationdtfrom": dfrom}, {"centerclassificationdtto": dto}]
    q = urllib.parse.quote(json.dumps(crit, separators=(",", ":")))
    return f"{BASE}?action=export.getExportCSVResult&criteria={q}&view=AdvancedSearch&page=product"


def download(url, tries=4):
    for i in range(tries):
        try:
            _prime()
            req = urllib.request.Request(url, headers=HEADERS)
            text = _OPENER.open(req, timeout=180).read().decode("utf-8-sig", errors="replace")
            if not text.startswith("Product Type"):
                raise ValueError("unexpected response (not an Enforcement Report CSV)")
            reader = csv.DictReader(io.StringIO(text))
            return reader.fieldnames, list(reader)
        except Exception as e:  # network hiccup or FDA maintenance window
            if i == tries - 1:
                raise
            wait = 10 * (i + 1)
            print(f"  retry in {wait}s ({e})")
            time.sleep(wait)


def fmt(d):
    return d.strftime("%m/%d/%Y")


def fetch_range(a, b):
    """All CVM recalls classified between dates a..b, splitting ranges that hit the export cap."""
    fields, rows = download(export_url(dfrom=fmt(a), dto=fmt(b)))
    if len(rows) >= CAP and a < b:
        mid = a + (b - a) // 2
        f1, r1 = fetch_range(a, mid)
        _, r2 = fetch_range(mid + dt.timedelta(days=1), b)
        return f1 or fields, r1 + r2
    if len(rows) >= CAP:
        print(f"  WARNING: {fmt(a)} still at the {CAP}-row cap")
    return fields, rows


def save(name, fields, rows):
    seen, uniq = set(), []
    for r in rows:
        k = r.get("Recall Number", "").strip().upper()
        if k and k in seen:
            continue
        seen.add(k)
        uniq.append(r)
    uniq.sort(key=lambda r: (r.get("Recall Number", "").strip().upper(), r.get("Event ID", "")))
    path = os.path.join(RAW, name)
    tmp = path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(uniq)
    os.replace(tmp, path)
    print(f"  {name}: {len(uniq)} rows")
    return len(uniq)


def main():
    full = "--full" in sys.argv
    os.makedirs(RAW, exist_ok=True)
    today = dt.date.today()
    first_year = OLDEST.year if full else today.year - 2
    print(f"Refreshing classification years {first_year}-{today.year}" + (" + keyword slices" if full else ""))
    total = 0
    for y in range(first_year, today.year + 1):
        a = max(dt.date(y, 1, 1), OLDEST)
        b = min(dt.date(y, 12, 31), today)
        fields, rows = fetch_range(a, b)
        total += save(f"v{y}.csv", fields, rows)
        time.sleep(2)  # be polite to FDA's server
    if full:
        # Records classified before June 2012 have no classification date, so they can
        # only be reached by product-description keyword x recall class.
        for kw in KEYWORDS:
            for code in CLASSES:
                fields, rows = download(export_url(desc=kw, cls=[code]))
                if len(rows) >= CAP:
                    print(f"  WARNING: keyword '{kw}' class {code} hit the {CAP}-row cap")
                total += save(f"k_{kw.replace(' ', '_')}_{code}.csv", fields, rows)
                time.sleep(2)
    print(f"Done: {total} rows downloaded")


if __name__ == "__main__":
    main()
