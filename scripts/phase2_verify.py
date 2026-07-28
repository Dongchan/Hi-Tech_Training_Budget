# -*- coding: utf-8 -*-
"""Phase 2-B/C/D: 계층·코드 / 산술 / raw-db 교차 전수 검사 (533건)
출력: analysis/phase2_results.json + 콘솔 요약
"""
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(r"D:\AI_Work\Claude\Hi-Tech_Training_Budget")
DATA = BASE / "KAIB2026" / "data"

raw = json.load(open(DATA / "budget_raw.json", encoding="utf-8"))
db = json.load(open(DATA / "budget_db.json", encoding="utf-8"))
toc = json.load(open(DATA / "toc_mapping.json", encoding="utf-8"))
projects = db["projects"]

results = {"B_hierarchy": {}, "C_arithmetic": {}, "D_cross": {}}
issues = []


def add_issue(check, severity, pid, name, detail):
    issues.append({"check": check, "severity": severity, "id": pid, "name": name, "detail": detail})


# ---------- B. 계층/코드 ----------
b = results["B_hierarchy"]

# B-1 사업코드 형식
code_pat = re.compile(r"^\d{4}-\d{3}$")
null_codes = [p["id"] for p in raw if not p.get("code")]
bad_codes = [(p["id"], p["code"]) for p in raw if p.get("code") and not code_pat.match(str(p["code"]))]
b["code_null"] = null_codes
b["code_bad_format"] = bad_codes
for pid, c in bad_codes:
    add_issue("B-1 코드형식", "중", pid, "", f"code={c}")

# B-2 계층 일관성: 동일 코드 → 상이한 명칭
for level in ["program", "unit_project", "detail_project"]:
    code2names = defaultdict(set)
    for p in raw:
        node = p.get(level) or {}
        c, n = node.get("code"), node.get("name")
        if c:
            code2names[c].add(n)
    conflicts = {c: sorted(x or "" for x in ns) for c, ns in code2names.items() if len(ns) > 1}
    b[f"{level}_code_conflicts"] = conflicts
    for c, ns in conflicts.items():
        add_issue(f"B-2 {level} 코드-명칭 충돌", "상", None, c, f"{ns}")

# B-3 field/sector 조합
fs = Counter((p.get("field"), p.get("sector")) for p in raw)
b["field_sector_combos"] = len(fs)

# B-4 유일성/대응
ids = Counter(p["id"] for p in raw)
names = Counter(p["name"] for p in raw)
b["dup_ids"] = [k for k, v in ids.items() if v > 1]
b["dup_names"] = [k for k, v in names.items() if v > 1]
toc_ids = {t["id"] for t in toc}
raw_ids = {p["id"] for p in raw}
b["toc_raw_id_mismatch"] = sorted(toc_ids ^ raw_ids)
toc_name_diff = [t["id"] for t in toc if next((p for p in raw if p["id"] == t["id"]), {}).get("name") != t["full_name"]]
b["toc_name_mismatch"] = toc_name_diff

# B-5 rnd_stage 커버리지
rnd_no_stage = [p["id"] for p in projects if p.get("is_rnd") and not p.get("rnd_stage")]
b["is_rnd_true_but_no_stage"] = rnd_no_stage
b["is_rnd_count"] = sum(1 for p in projects if p.get("is_rnd"))

# B-6 사업명 잘림 (A4)
trunc = [(p["id"], p["project_name"]) for p in raw
         if "…" in (p.get("project_name") or "")
         or (p.get("project_name", "").count("(") != p.get("project_name", "").count(")"))]
b["truncated_names"] = trunc
for pid, n in trunc:
    add_issue("B-6 사업명 잘림", "중", pid, n, "")

# ---------- C. 산술 ----------
c = results["C_arithmetic"]
TOL = 1.5  # 백만원 단위 반올림 허용

def num(x):
    return x if isinstance(x, (int, float)) else None

# C-1 내역사업 합계 vs 모사업
sub_mismatch = {"2024": [], "2025": [], "2026": []}
for p in projects:
    subs = p.get("sub_projects") or []
    if not subs:
        continue
    bud = p.get("budget") or {}
    for yr, parent_key in [("2024", "2024_settlement"), ("2025", "2025_original"), ("2026", "2026_budget")]:
        vals = [num(s.get(f"budget_{yr}")) for s in subs]
        if all(v is None for v in vals):
            continue
        ssum = sum(v for v in vals if v is not None)
        parent = num(bud.get(parent_key))
        if parent is None:
            continue
        if abs(ssum - parent) > TOL:
            sub_mismatch[yr].append({"id": p["id"], "name": p["name"], "sub_sum": ssum, "parent": parent,
                                     "diff": round(ssum - parent, 1)})
c["sub_sum_mismatch"] = {k: v for k, v in sub_mismatch.items()}
c["sub_sum_mismatch_counts"] = {k: len(v) for k, v in sub_mismatch.items()}

# C-2 증감액/증감률 역산
amt_bad, rate_bad = [], []
for p in projects:
    bud = p.get("budget") or {}
    b26, b25o, b25s = num(bud.get("2026_budget")), num(bud.get("2025_original")), num(bud.get("2025_supplementary"))
    ca, cr = num(bud.get("change_amount")), num(bud.get("change_rate"))
    if b26 is None or ca is None:
        continue
    bases = [x for x in (b25o, b25s) if x is not None]
    if not bases:
        continue
    if not any(abs((b26 - base) - ca) <= TOL for base in bases):
        amt_bad.append({"id": p["id"], "name": p["name"], "b26": b26, "b25o": b25o, "b25s": b25s, "change_amount": ca})
    if cr is not None:
        ok = False
        for base in bases:
            if base:
                if abs((b26 - base) / base * 100 - cr) <= 0.15:
                    ok = True
        if not ok and not (all(not x for x in bases) and cr == 0):
            rate_bad.append({"id": p["id"], "name": p["name"], "b26": b26, "b25o": b25o, "b25s": b25s, "change_rate": cr})
c["change_amount_mismatch"] = amt_bad
c["change_rate_mismatch"] = rate_bad

# C-3 metadata 총계 재계산
tot26 = sum(num((p.get("budget") or {}).get("2026_budget")) or 0 for p in projects)
tot25 = sum(num((p.get("budget") or {}).get("2025_original")) or 0 for p in projects)
meta = db["metadata"]
c["metadata_totals"] = {
    "2026_recalc": round(tot26, 1), "2026_meta": meta.get("total_budget_2026"),
    "2026_match": abs(tot26 - (meta.get("total_budget_2026") or 0)) <= TOL,
    "2025_recalc": round(tot25, 1), "2025_meta": meta.get("total_budget_2025"),
    "2025_match": abs(tot25 - (meta.get("total_budget_2025") or 0)) <= TOL,
}

# C-4 budget_mismatch 플래그 건 (B6)
c["budget_mismatch_flagged"] = [{"id": p["id"], "name": p["name"], "detail": p.get("budget_mismatch")}
                                for p in projects if p.get("budget_mismatch")]

# ---------- D. raw ↔ db 교차 ----------
d = results["D_cross"]
raw_by_id = {p["id"]: p for p in raw}
skip = {"raw_text"}
db_only = {"ai_domains", "ai_tech", "rnd_stage", "_sub_column_fixed", "_sub_projects_cleaned", "budget_mismatch"}
diff_fields = Counter()
diff_samples = defaultdict(list)
for p in projects:
    r = raw_by_id.get(p["id"])
    if not r:
        continue
    for k, v in p.items():
        if k in db_only or k in skip:
            continue
        rv = r.get(k)
        if json.dumps(v, ensure_ascii=False, sort_keys=True) != json.dumps(rv, ensure_ascii=False, sort_keys=True):
            diff_fields[k] += 1
            if len(diff_samples[k]) < 3:
                diff_samples[k].append(p["id"])
d["field_diff_counts"] = dict(diff_fields)
d["field_diff_samples"] = dict(diff_samples)

# ---------- 저장/요약 ----------
results["issues"] = issues
out = BASE / "analysis" / "phase2_results.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("=== Phase 2-B 계층/코드 ===")
print("code null:", len(null_codes), "/ 형식위반:", len(bad_codes))
for level in ["program", "unit_project", "detail_project"]:
    print(f"{level} 코드-명칭 충돌: {len(b[f'{level}_code_conflicts'])}건")
print("id 중복:", b["dup_ids"], "/ name 중복:", b["dup_names"])
print("toc-raw id 불일치:", b["toc_raw_id_mismatch"], "/ toc name 불일치:", len(toc_name_diff))
print("is_rnd=true & rnd_stage 없음:", len(rnd_no_stage), f"(is_rnd 총 {b['is_rnd_count']}건)")
print("사업명 잘림 의심:", len(trunc), trunc[:5])
print("\n=== Phase 2-C 산술 ===")
print("내역합계 불일치:", c["sub_sum_mismatch_counts"])
print("증감액 불일치:", len(amt_bad), "/ 증감률 불일치:", len(rate_bad))
print("metadata 총계:", c["metadata_totals"])
print("budget_mismatch 플래그:", [x["id"] for x in c["budget_mismatch_flagged"]])
print("\n=== Phase 2-D raw↔db ===")
print("필드별 차이 건수:", dict(diff_fields))
print("\n결과 저장:", out)
