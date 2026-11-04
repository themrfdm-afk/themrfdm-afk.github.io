"""Collapse predictions.csv (one row per predictor per year) into groundhogs.json (one record per predictor)."""
import csv, json, sys

src = sys.argv[1] if len(sys.argv) > 1 else "predictions.csv"
out = sys.argv[2] if len(sys.argv) > 2 else "groundhogs.json"

rows = sorted(csv.DictReader(open(src, encoding="utf-8")), key=lambda r: int(r["year"]))
by_id = {}
for r in rows:
    g = by_id.setdefault(r["id"], {"preds": []})
    # later rows overwrite, so profile fields reflect the most recent year
    g.update(
        id=int(r["id"]), slug=r["slug"], name=r["name"], short=r["shortname"],
        city=r["city"], region=r["region"], country=r["country"], type=r["type"],
        active=r["active"] == "1", successor=r["successor"], desc=r["description"],
        image=r["image"],
    )
    s = {"1": 1, "0": 0}.get(r["shadow"])  # NA -> None
    g["preds"].append([int(r["year"]), s, r["details"]] if r["details"] else [int(r["year"]), s])

data = sorted(by_id.values(), key=lambda g: g["name"])
json.dump(data, open(out, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"{len(data)} predictors -> {out}")
