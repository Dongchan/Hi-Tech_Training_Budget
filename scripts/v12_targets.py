# -*- coding: utf-8 -*-
"""v1.2: 내역사업 합계 불일치 대상 산정 (v1.1 보정 모예산 기준)
- 대상 = 연도별 |내역 합계 − 모사업 예산| > 허용오차 인 사업의 합집합
- 출력: analysis/v12_jobs/sub_XX.json (배치당 12건)
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(r"D:\AI_Work\Claude\Hi-Tech_Training_Budget")
JOBS = BASE / "analysis" / "v12_jobs"
JOBS.mkdir(exist_ok=True)

db = json.load(open(BASE / "KAIB2026" / "data" / "budget_db.json", encoding="utf-8"))
FIX = {int(k): v for k, v in json.load(open(BASE / "analysis" / "budget_corrections_v11.json",
                                            encoding="utf-8"))["corrections"].items()}
idx = json.load(open(BASE / "analysis" / "batches" / "index.json", encoding="utf-8"))

TOL = 2.0


def num(x):
    return x if isinstance(x, (int, float)) else None


def parent_vals(p):
    b = p.get("budget") or {}
    pid = p["id"]
    if pid in FIX:
        f = FIX[pid]
        return {"2024": f.get("b2024"), "2025": f.get("b2025_original"), "2026": f.get("b2026_budget")}
    return {"2024": num(b.get("2024_settlement")), "2025": num(b.get("2025_original")),
            "2026": num(b.get("2026_budget"))}


targets = {}
year_counts = {"2024": 0, "2025": 0, "2026": 0}
for p in db["projects"]:
    subs = p.get("sub_projects") or []
    if not subs:
        continue
    pv = parent_vals(p)
    bad_years = []
    for yr in ["2024", "2025", "2026"]:
        vals = [num(s.get(f"budget_{yr}")) for s in subs]
        if all(v is None for v in vals):
            continue
        ssum = sum(v for v in vals if v is not None)
        parent = pv[yr]
        if parent is None:
            continue
        if abs(ssum - parent) > TOL:
            bad_years.append({"year": yr, "sub_sum": round(ssum, 1), "parent": parent,
                              "diff": round(ssum - parent, 1)})
            year_counts[yr] += 1
    if bad_years:
        targets[p["id"]] = {
            "id": p["id"], "name": p["name"],
            "mismatch": bad_years,
            "current_subs": [{"name": s.get("name"), "b2024": num(s.get("budget_2024")),
                              "b2025": num(s.get("budget_2025")), "b2026": num(s.get("budget_2026"))}
                             for s in subs],
            "parent_budget": pv,
            "extracted": idx[str(p["id"])]["extracted"],
        }

print(f"연도별 불일치(보정 모예산 기준): 2024={year_counts['2024']} / 2025={year_counts['2025']} / 2026={year_counts['2026']}")
print(f"대상 사업(합집합): {len(targets)}건")

items = sorted(targets.values(), key=lambda t: t["id"])
CH = 12
chunks = [items[i:i + CH] for i in range(0, len(items), CH)]
for i, c in enumerate(chunks, 1):
    (JOBS / f"sub_{i:02d}.json").write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"배치 {len(chunks)}개 생성 (배치당 {CH}건) → {JOBS}")
