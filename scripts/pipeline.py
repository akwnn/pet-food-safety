"""Rebuild the Pet Food Safety Signal Explorer from raw FDA Enforcement Report exports.

Usage:  python3 scripts/pipeline.py
Input:  data/raw/*.csv  (FDA iRES Enforcement Report CSV exports, product type = Veterinary)
Output: data/recall_events.csv, data/recalled_products.csv, index.html
"""
import csv, glob, json, re, collections, datetime as dt, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from classify import hazard, category, species, NONFOOD

# 1. merge + de-duplicate on recall number
rows = {}
for f in sorted(glob.glob(os.path.join(ROOT, "data/raw/*.csv"))):
    for x in csv.DictReader(open(f, encoding="utf-8-sig")):
        rows[x["Recall Number"].strip().upper()] = x
vet_total = len(rows)

# 2. keep pet food / treats / supplements; drop vet drugs, devices, livestock feed
PET = re.compile(r"\b(dogs?|cats?|pets?|canine|feline|pupp(y|ies)|kittens?|kibble|pig ears?|bully sticks?|rawhide|jerky treats?|dog treats?|cat treats?|chews?)\b", re.I)
LIVE = re.compile(r"\b(cattle|swine|hog|pig starter|poultry|broiler|chick|turkey|horse|equine|goat|sheep|calf|calves|dairy|ruminant|layer|fish feed|shrimp|rabbit|bird seed|wild bird|deer)\b", re.I)
DRUG = re.compile(r"\b(NDC|tablets?|injection|injectable|capsules?|mg/mL|suspension|ointment|shampoo|test strip|test kit|syringe|otic|ophthalmic|flea|tick|topical|spot[- ]on|chewable tablets?|ANADA|NADA|dewormer|vaccine)\b", re.I)
def d(s):
    try: return dt.datetime.strptime((s or "").strip(), "%m/%d/%Y").date()
    except ValueError: return None
def norm(f):
    f = re.sub(r"\bdba\b.*$", "", f, flags=re.I)
    f = re.sub(r"['\u2019`]", "", f); f = re.sub(r"[\.,!\"]", " ", f)
    f = re.sub(r"\b(inc|llc|co|corp|corporation|company|ltd|lp|l l c|the|usa|us|incorporated)\b", " ", f, flags=re.I)
    return re.sub(r"\s+", " ", f).strip().title().replace("Nestle Purina Petcare", "Nestle Purina PetCare")

recs = []
for x in rows.values():
    desc, reason = x["Product Description"], x["Reason for Recall"]
    if not PET.search(desc + " " + reason): continue
    if DRUG.search(desc): continue
    if LIVE.search(desc) and not re.search(r"\b(dog|cat|pet)\s*(food|treat)", desc, re.I): continue
    if NONFOOD.search(reason) and not re.search(r"salmonell|listeria|aflatoxin|melamine", reason, re.I): continue
    recs.append(dict(
        rn=x["Recall Number"].strip().upper(), ev=x["Event ID"].strip(), firm=x["Recalling Firm"].strip(),
        firm_n=norm(x["Recalling Firm"].strip()), state=x["State/Province"].strip(), country=x["Country"].strip(),
        cls=x["Classification"].strip(), status=x["Status"].strip(), vm=x["Voluntary/Mandated"].strip(),
        desc=re.sub(r"\s+", " ", desc).strip(), reason=re.sub(r"\s+", " ", reason).strip(), qty=x["Product Quantity"].strip(),
        init=str(d(x["Recall Initiation Date"]) or ""), classified=str(d(x["Center Classification Date"]) or ""),
        report=str(d(x["Report Date"]) or ""), term=str(d(x["Termination Date"]) or ""),
        hazard=hazard(reason, desc), category=category(desc), species=species(desc + " " + reason)))

# 3. roll up to recall events (FDA event ID)
by = collections.defaultdict(list)
for r in recs: by[r["ev"] or r["rn"]].append(r)
events = []
for k, rs in by.items():
    mode = lambda f: collections.Counter(r[f] for r in rs).most_common(1)[0][0]
    inits = [r["init"] for r in rs if r["init"]]; cl = [r["classified"] for r in rs if r["classified"]]
    i0 = min(inits) if inits else ""; c0 = min(cl) if cl else ""
    sp = set(r["species"] for r in rs) - {"Unspecified"}
    spc = "Dog & cat" if ({"Dog", "Cat"} <= sp or "Dog & cat" in sp) else (next(iter(sp)) if len(sp) == 1 else ("Unspecified" if not sp else "Mixed"))
    tl = [r["term"] for r in rs if r["term"]]
    events.append(dict(id=k, firm=mode("firm"), firm_n=mode("firm_n"), init=i0, year=int(i0[:4]) if i0 else None,
        classified=c0, fda_lag=(dt.date.fromisoformat(c0) - dt.date.fromisoformat(i0)).days if i0 and c0 else None,
        close_days=(dt.date.fromisoformat(max(tl)) - dt.date.fromisoformat(i0)).days if i0 and tl and len(tl) == len(rs) else None,
        hazard=mode("hazard"), category=mode("category"), species=spc, cls=min(r["cls"] for r in rs), n=len(rs),
        reason=rs[0]["reason"][:400], state=mode("state")))
events.sort(key=lambda e: e["init"] or "")

# 4. write CSVs
def wcsv(path, data, fields):
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore"); w.writeheader(); w.writerows(data)
wcsv(os.path.join(ROOT, "data/recall_events.csv"), events, ["id","init","classified","fda_lag","close_days","year","firm","firm_n","hazard","category","species","cls","n","state","reason"])
wcsv(os.path.join(ROOT, "data/recalled_products.csv"), recs, ["rn","ev","firm","firm_n","state","country","cls","status","vm","init","classified","report","term","hazard","category","species","desc","reason","qty"])

# 5. build the self-contained dashboard
cases = json.load(open(os.path.join(ROOT, "data/outbreak_timelines.json")))
slim = [{k: (r[k][:260] if k == "desc" else r[k]) for k in ["rn","ev","firm","desc","cls","init"]} for r in recs]
meta = dict(exported="Sept 28, 2026", vet_total=vet_total, ade_total="1.36M reports", openfda_pet="~100")
data = json.dumps(dict(events=events, records=slim, cases=cases, meta=meta), separators=(",", ":"))
open(os.path.join(ROOT, "index.html"), "w").write(open(os.path.join(ROOT, "scripts/template.html")).read().replace("__DATA__", data))
print(f"{vet_total} veterinary recall records -> {len(recs)} pet products -> {len(events)} recall events. Wrote index.html")
