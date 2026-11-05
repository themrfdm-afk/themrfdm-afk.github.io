"""Collapse the DR12573 'Majors by College' workbook (one sheet per fall term) into majors.json.

usage: python3 build-data.py "<workbook.xlsx>" [majors.json]
Needs openpyxl.
"""
import json, re, sys, collections
import openpyxl

src = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else "majors.json"

# Sheets are in order Fall 2016 .. Fall 2025 (one is labelled "majors2024"); take the year from position.
wb = openpyxl.load_workbook(src, data_only=True)
YEARS = list(range(2016, 2016 + len(wb.sheetnames)))

COLLEGE_FIX = {"Business Administration": "Business"}

def college(c):
    c = c.strip()
    c = re.sub(r"^Grad Studies - ", "", c)
    return COLLEGE_FIX.get(c, c)

def level(d):
    if d in ("", "NDEG", "NA"): return "Non-degree / other"
    if d in ("CER", "GCER", "ACER", "TCER", "EDS", "END", "SXCT"): return "Certificate / specialist"
    if d in ("JD", "LLM", "JSD", "DVM"): return "Law & veterinary"
    if d in ("PHD", "EDD", "DMA", "DPLH", "AUD", "DOC"): return "Doctoral"
    if d.startswith("M"): return "Master's"
    if d.startswith("B"): return "Bachelor's"
    return "Non-degree / other"

rows = []
for ws, y in zip(wb, YEARS):
    for r in list(ws.iter_rows(values_only=True))[1:]:
        if not r[1]:  # blank trailing grand-total row
            continue
        rows.append((y, college(r[0] or ""), r[1].strip(), (r[2] or "").strip(), (r[3] or "").strip(), int(r[4])))

# Identify a "major" across years. Names get tweaked and codes get reused, so link rows that share a
# name OR a code (union-find), except for codes that lump unrelated programs together.
NO_LINK_CODES = {"PBAC", "TCER", "UNDA", "UNED", "UNDE", "UNDL"}
parent = {}
def find(x):
    parent.setdefault(x, x)
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x
def union(a, b): parent[find(a)] = find(b)

for y, col, name, code, deg, n in rows:
    find(("n", name))
    if code not in NO_LINK_CODES:
        union(("n", name), ("c", code))

groups = collections.defaultdict(list)
for row in rows:
    groups[find(("n", row[2]))].append(row)

colleges = sorted({r[1] for r in rows})
degs = sorted({r[4] for r in rows})
cidx = {c: i for i, c in enumerate(colleges)}
didx = {d: i for i, d in enumerate(degs)}

EXPAND = {"CHLD": "Child", "YTH": "Youth", "FAM": "Family", "STDIES": "Studies", "HOSPIT": "Hospitality",
          "REST": "Restaurant", "TOUR": "Tourism", "MNGT": "Management", "MGMT": "Management", "NUTR": "Nutrition",
          "HLTH": "Health", "SCI": "Science", "ENGR": "Engineering", "ENV": "Environmental", "COMM": "Communication",
          "EDUC": "Education", "AG": "Agricultural", "SYS": "Systems", "TECH": "Technology", "ADMIN": "Administration",
          "TEXT": "Textiles", "MERCH": "Merchandising", "DESGN": "Design", "TMFD": "Textiles, Merchandising & Fashion Design",
          "CYAF": "Child, Youth & Family Studies", "THEA": "Theatre", "HRTM": "Hospitality, Restaurant & Tourism Management",
          "PRE": "Pre", "UNDERGRAD": "Undergraduate", "MSTR": "Master's", "PGM": "Program", "PROGAM": "Program",
          "COMPUTER": "Computer", "HUM": "Human", "CONSUMER": "Consumer", "DEV": "Development", "MNG": "Management",
          "SPEC": "Special", "ELEM": "Elementary", "SEC": "Secondary", "ENDORSMNT": "Endorsement", "CERT": "Certification",
          "ENDORSEMENTS": "Endorsements", "EXPL": "Exploratory", "INTL": "International", "BIOL": "Biological"}
KEEP_UPPER = {"UNL", "ANR", "EHS", "CASNR", "II", "III", "IV", "ROTC", "TESOL", "GIS", "DNA", "PE", "MBA", "K", "IT", "ESL", "UNO", "CEHS", "SLP"}
SMALL = {"and", "of", "in", "for", "the", "to", "&", "or", "a", "an"}

def pretty(s):
    parts = re.split(r"([^A-Za-z0-9']+)", s)
    out = []
    for p in parts:
        u = p.upper()
        if not re.match(r"[A-Za-z0-9]", p): out.append(p); continue
        if u in KEEP_UPPER: out.append(u)
        elif u in EXPAND: out.append(EXPAND[u])
        elif p.isdigit() or any(c.isdigit() for c in p): out.append(p)
        else: out.append(p.capitalize())
    t = "".join(out)
    t = re.sub(r"\s*,\s*", ", ", t)
    t = re.sub(r"\s*&\s*", " & ", t)
    t = re.sub(r"\s*\(\s*", " (", t)
    t = re.sub(r"\s+", " ", t).strip()
    words = t.split(" ")
    t = " ".join(w.lower() if i and w.lower() in SMALL else w for i, w in enumerate(words))
    t = re.sub(r"\((\w)", lambda m: "(" + m.group(1).upper(), t)
    return t

majors = []
for g in groups.values():
    # display name: most students in the latest year the major existed
    latest = max(r[0] for r in g)
    tally = collections.Counter()
    for r in g:
        if r[0] == latest: tally[r[2]] += r[5]
    name = tally.most_common(1)[0][0]
    aliases = sorted({r[2] for r in g} - {name})
    codes = sorted({r[3] for r in g if r[3]})
    agg = collections.Counter()
    for y, col, nm, code, deg, n in g:
        agg[(y - YEARS[0], cidx[col], didx[deg])] += n
    majors.append({"n": pretty(name), "raw": name, "a": aliases, "k": codes, "rk": int(any("RAIKES" in r[2] for r in g)), "r": [[*k, v] for k, v in sorted(agg.items())]})

# Umbrella entry: every Raikes program rolled into one line (rk=2, so it shows in the normal list
# while the individual programs, rk=1, stay hidden unless asked for).
rk_rows = collections.Counter()
for m in majors:
    if m["rk"]:
        for y, c, d, v in m["r"]: rk_rows[(y, c, d)] += v
majors.append({"n": "Raikes School (all programs)", "raw": "", "a": [m["n"] for m in majors if m["rk"]], "k": [], "rk": 2,
               "r": [[*k, v] for k, v in sorted(rk_rows.items())]})
majors.sort(key=lambda m: m["n"])
for m in majors: del m["raw"]
data = {
    "years": YEARS,
    "colleges": colleges,
    "degrees": [[d or "(none)", level(d)] for d in degs],
    "majors": majors,
}
json.dump(data, open(out, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"{len(majors)} majors, {len(rows)} source rows -> {out}")
if "--names" in sys.argv:
    print("\n".join(m["n"] for m in majors))
