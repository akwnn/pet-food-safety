import json,re,collections,sys
HAZ=[
 ("Melamine / cyanuric acid", r"melamine|cyanuric|cuts and gravy|menu foods|rice protein concentrate|wheat gluten"),
 ("H5N1 avian influenza", r"h5n1|avian influenza|bird flu|hpai"),
 ("Salmonella", r"salmonell"),
 ("Listeria", r"listeria|l\. ?mono"),
 ("Aflatoxin / mycotoxin", r"aflatoxin|mycotoxin|vomitoxin|\bdon\b|fumonisin|ochratoxin|zearalenone"),
 ("Vitamin D excess", r"vitamin d(?!\s*deficien)|cholecalciferol"),
 ("Thyroid hormone", r"thyroid"),
 ("Pentobarbital", r"pentobarbital|euthanasia"),
 ("E. coli / other pathogen", r"e\.?\s*coli|\bstec\b|clostridium|c\. ?bot|botul|pathogen|bacteria|microb|microorganism|pseudomonas|aerobic plate|\bbse\b|spongiform"),
 ("Nutrient deficiency / excess", r"thiamine|vitamin a|vitamin b|deficien|excess (zinc|copper|vitamin|calcium|potassium)|elevated levels? of (zinc|copper|vitamin|calcium|iron|potassium|selenium)|choline|sodium|mineral|nutrient|potassium|magnesium|selenium|copper|zinc|\biron\b|non-protein nitrogen"),
 ("Mold / spoilage", r"rodent|insanitary|cgmp|gmp|mou?ld|spoil|rancid|off odor|off-odor|temperature|swollen|bloat|seal|leak|under ?process|commercial steril|low acid canned"),
 ("Foreign material", r"foreign|enamel|lining|splinter|plastic|metal|glass|rubber|wood|rock|stone|bone fragment|choking|string|wire"),
 ("Chemical / drug residue", r"propylene glycol|ethoxyquin|antibiotic|residue|drug|monensin|chemical|pesticide|heavy metal|lead|arsenic|mercury|ivermectin|xylitol|irradiat"),
 ("Labeling / undeclared / unapproved", r"undeclared|label|mislabel|misbrand|allergen|unapproved|not approved|registration|registered|claims?|packag|incorrect|wrong|chloramphenicol"),
]
HAZ=[(n,re.compile(p,re.I)) for n,p in HAZ]
CAT=[
 ("Raw / frozen / freeze-dried", r"\braw\b|frozen|freeze[- ]?dried|dehydrated"),
 ("Treats & chews", r"treat|chew|jerky|pig ears?|bully|rawhide|biscuit|snack|bone|hoof|hooves|trachea|sticks?\b|tendon|antler|cookie|pizzle|patt(y|ies)|sausage|cuts\b"),
 ("Supplements", r"supplement|softgel|vitamin|powder|probiotic|chewable|oil\b|capsule"),
 ("Wet / canned", r"\bcans?\b|canned|pouch|gravy|stew|pate|pâté|wet\b|tray|oz\. can|in sauce|morsels"),
 ("Dry kibble", r"\bdry\b|kibble|\blbs?\.?\b|bag|formula|dog food|cat food|puppy food|kitten food|lb\b"),
]
CAT=[(n,re.compile(p,re.I)) for n,p in CAT]
def species(d):
    dg=re.search(r"\b(dogs?|canine|pupp(y|ies)|k9)\b",d,re.I); ct=re.search(r"\b(cats?|feline|kittens?)\b",d,re.I)
    if dg and ct: return "Dog & cat"
    if dg: return "Dog"
    if ct: return "Cat"
    if re.search(r"fish|bird|reptile|rabbit|ferret|hamster|small animal",d,re.I): return "Other"
    return "Unspecified"
def hazard(r,d):
    for n,p in HAZ:
        if p.search(r): return n
    for n,p in HAZ[:9]:
        if p.search(d): return n
    return "Other / unspecified"
def category(d):
    for n,p in CAT:
        if p.search(d): return n
    return "Other / unspecified"

NONFOOD=re.compile(r"eye drop|sterile|sterility|potency|sub-potent|compound|hptlc|lubricant|chew weight|alcohol prep|out[- ]of[- ]specification|stability",re.I)
