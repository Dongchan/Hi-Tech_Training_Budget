# -*- coding: utf-8 -*-
"""Dash_board 데이터 자산 생성
- data/*.csv (UTF-8 BOM, 엑셀 호환): raw 전수 + 내역사업 + 인재양성 + 검증이슈 + 집계 2종
- data/data.js: 대시보드용 (file:// 환경에서 fetch 불가 → script 로드)
- 예산 보정: 검증 확정 8건은 corrected(b26c) 값 병기, 차트는 보정값 사용
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(r"D:\AI_Work\Claude\Hi-Tech_Training_Budget")
OUT = BASE / "Dash_board"
DATA = OUT / "data"
DATA.mkdir(parents=True, exist_ok=True)

db = json.load(open(BASE / "KAIB2026" / "data" / "budget_db.json", encoding="utf-8"))
vr = json.load(open(BASE / "analysis" / "verification_results.json", encoding="utf-8"))
tf = json.load(open(BASE / "analysis" / "talent_final.json", encoding="utf-8"))
projects = db["projects"]
verdict = {r["id"]: r for r in vr["results"]}
talent = {t["id"]: t for t in tf["projects"]}

# PDF 실측 확정 보정값 (2026 확정예산, 백만원)
CORR26 = {9: 3068, 112: 10399, 242: 9177, 243: 183056, 339: 6823, 452: 1705, 466: 1918, 467: 7487}
CORR_NOTE = "6열 시프트/다행 총괄표 파싱 오류 — PDF 실측값으로 보정"


def num(x):
    return x if isinstance(x, (int, float)) else None


def j(lst):
    return ";".join(lst or [])


# ---------------- CSV 1: 전체 사업 raw ----------------
rows = []
for p in projects:
    b = p.get("budget") or {}
    v = verdict.get(p["id"], {})
    t = talent.get(p["id"])
    b26 = num(b.get("2026_budget"))
    b26c = CORR26.get(p["id"], b26)
    rows.append({
        "id": p["id"], "name": p["name"], "project_name": p["project_name"],
        "department": p["department"], "division": p.get("division"),
        "code": p.get("code"), "field": p.get("field"), "sector": p.get("sector"),
        "program_code": (p.get("program") or {}).get("code"), "program_name": (p.get("program") or {}).get("name"),
        "unit_code": (p.get("unit_project") or {}).get("code"), "unit_name": (p.get("unit_project") or {}).get("name"),
        "detail_code": (p.get("detail_project") or {}).get("code"), "detail_name": (p.get("detail_project") or {}).get("name"),
        "account_type": p.get("account_type"), "status": p.get("status"), "support_type": p.get("support_type"),
        "implementing_agency": p.get("implementing_agency"),
        "is_rnd": p.get("is_rnd"), "is_informatization": p.get("is_informatization"),
        "rnd_stage": p.get("rnd_stage"), "ai_domains": j(p.get("ai_domains")),
        "ai_tech": j(p.get("ai_tech")), "keywords": j(p.get("keywords")),
        "b2024_settlement": num(b.get("2024_settlement")), "b2025_original": num(b.get("2025_original")),
        "b2025_supplementary": num(b.get("2025_supplementary")), "b2026_request": num(b.get("2026_request")),
        "b2026_budget": b26, "b2026_corrected": b26c,
        "correction_note": CORR_NOTE if p["id"] in CORR26 else "",
        "change_amount": num(b.get("change_amount")), "change_rate": num(b.get("change_rate")),
        "project_period": (p.get("project_period") or {}).get("raw"),
        "total_cost": (p.get("total_cost") or {}).get("raw"),
        "page_start": p.get("page_start"), "page_end": p.get("page_end"),
        "verify_budget": v.get("budget_verdict"), "verify_budget_detail": v.get("budget_detail", ""),
        "verify_classification": v.get("classification_verdict"), "verify_classification_detail": v.get("classification_detail", ""),
        "verify_name_match": v.get("name_match"), "ai_relevance": v.get("ai_relevance"),
        "talent_related": v.get("talent_related"), "talent_category": t["category"] if t else "",
    })


def write_csv(path, rows, fields=None):
    fields = fields or list(rows[0].keys())
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"{path.name}: {len(rows)}행")


write_csv(DATA / "projects_raw.csv", rows)

# ---------------- CSV 2: 내역사업 ----------------
subs = []
for p in projects:
    for s in (p.get("sub_projects") or []):
        subs.append({"parent_id": p["id"], "department": p["department"],
                     "parent_name": p["project_name"], "sub_name": s.get("name"),
                     "b2024": num(s.get("budget_2024")), "b2025": num(s.get("budget_2025")),
                     "b2026": num(s.get("budget_2026"))})
write_csv(DATA / "sub_projects_raw.csv", subs)

# ---------------- CSV 3: 인재양성 96건 ----------------
trows = [{"id": t["id"], "department": t["department"], "project_name": t["project_name"],
          "category": t["category"], "in_edu_domain": t["in_edu_domain"],
          "ai_domains": j(t.get("ai_domains")), "is_rnd": t.get("is_rnd"),
          "b2024": t["b2024"], "b2025": t["b2025"], "b2026": t["b2026"],
          "corrected": t["corrected"], "correction_note": t.get("correction_note") or "",
          "talent_note": t.get("talent_note", "")} for t in tf["projects"]]
write_csv(DATA / "talent_projects.csv", trows)

# ---------------- CSV 4: 검증 이슈 ----------------
irows = []
for r in vr["results"]:
    if r["budget_verdict"] == "match" and r["classification_verdict"] == "appropriate" and r.get("name_match", True):
        continue
    p = next(x for x in projects if x["id"] == r["id"])
    irows.append({"id": r["id"], "department": p["department"], "project_name": p["project_name"],
                  "budget_verdict": r["budget_verdict"], "budget_detail": r.get("budget_detail", ""),
                  "classification_verdict": r["classification_verdict"],
                  "classification_detail": r.get("classification_detail", ""),
                  "name_match": r.get("name_match"), "name_detail": r.get("name_detail", ""),
                  "ai_relevance": r["ai_relevance"], "source": r.get("source")})
write_csv(DATA / "verification_issues.csv", irows)

# ---------------- 집계 ----------------
def b26c_of(p):
    return CORR26.get(p["id"], num((p.get("budget") or {}).get("2026_budget")) or 0)


by_dept = defaultdict(lambda: {"count": 0, "b2026": 0.0, "talent_core": 0.0, "talent_partial": 0.0})
for p in projects:
    d = by_dept[p["department"]]
    d["count"] += 1
    d["b2026"] += b26c_of(p)
    t = talent.get(p["id"])
    if t:
        d["talent_" + t["category"]] += t["b2026"] or 0
drows = [{"department": k, **{kk: round(vv, 1) for kk, vv in v.items()}}
         for k, v in sorted(by_dept.items(), key=lambda x: -x[1]["b2026"])]
write_csv(DATA / "by_department.csv", drows)

by_dom = defaultdict(lambda: {"count": 0, "b2026": 0.0})
for p in projects:
    for d in (p.get("ai_domains") or []):
        by_dom[d]["count"] += 1
        by_dom[d]["b2026"] += b26c_of(p)
domrows = [{"domain": k, "count": v["count"], "b2026": round(v["b2026"], 1)}
           for k, v in sorted(by_dom.items(), key=lambda x: -x[1]["b2026"])]
write_csv(DATA / "by_domain.csv", domrows)

# ---------------- data.js ----------------
slim = []
for p in projects:
    b = p.get("budget") or {}
    v = verdict.get(p["id"], {})
    t = talent.get(p["id"])
    slim.append({
        "id": p["id"], "dept": p["department"], "name": p["project_name"],
        "b24": num(b.get("2024_settlement")), "b25": num(b.get("2025_original")),
        "b26": num(b.get("2026_budget")), "b26c": CORR26.get(p["id"], num(b.get("2026_budget"))),
        "corr": p["id"] in CORR26,
        "dom": p.get("ai_domains") or [], "rnd": bool(p.get("is_rnd")), "info": bool(p.get("is_informatization")),
        "ai": v.get("ai_relevance"), "bv": v.get("budget_verdict"), "cv": v.get("classification_verdict"),
        "tal": (t["category"] if t else None),
    })

tot24 = round(sum(x["b24"] or 0 for x in slim), 1)
tot25 = round(sum(x["b25"] or 0 for x in slim), 1)
tot26 = round(sum(x["b26c"] or 0 for x in slim), 1)
tot26_raw = round(sum(x["b26"] or 0 for x in slim), 1)

ai_sum = {k: round(sum(x["b26c"] or 0 for x in slim if x["ai"] == k), 1) for k in ["core", "partial", "none"]}
ai_cnt = {k: sum(1 for x in slim if x["ai"] == k) for k in ["core", "partial", "none"]}

tal_year = {c: {y: round(sum((talent[x["id"]]["b" + y] or 0) for x in slim if x["tal"] == c), 1)
                for y in ["2024", "2025", "2026"]} for c in ["core", "partial"]}

deltas = sorted(((x, (x["b26c"] or 0) - (x["b25"] or 0)) for x in slim if x["b25"] is not None),
                key=lambda y: y[1])
top_dec = [{"id": x["id"], "dept": x["dept"], "name": x["name"], "delta": round(d, 1)} for x, d in deltas[:8]]
top_inc = [{"id": x["id"], "dept": x["dept"], "name": x["name"], "delta": round(d, 1)} for x, d in deltas[-8:]][::-1]

type_sum = {
    "R&D": round(sum(x["b26c"] or 0 for x in slim if x["rnd"]), 1),
    "정보화": round(sum(x["b26c"] or 0 for x in slim if x["info"] and not x["rnd"]), 1),
    "일반": round(sum(x["b26c"] or 0 for x in slim if not x["rnd"] and not x["info"]), 1),
}
type_cnt = {
    "R&D": sum(1 for x in slim if x["rnd"]),
    "정보화": sum(1 for x in slim if x["info"] and not x["rnd"]),
    "일반": sum(1 for x in slim if not x["rnd"] and not x["info"]),
}

dup_groups = [{"n": len(g["all_ids"]),
               "names": [f'{talent[i]["department"]} · {talent[i]["project_name"]}' for i in g["talent_ids"]]}
              for g in tf["duplicate_groups"]]

payload = {
    "meta": {"generated": "2026-07-28", "source": "AI_예산사업_통합_설명자료.pdf (5,296p) / KAIB2026 파싱 데이터 전수 검증",
             "unit": "백만원", "corrections": len(CORR26), "tot26_raw": tot26_raw},
    "totals": {"projects": 533, "departments": 41, "b2024": tot24, "b2025": tot25, "b2026": tot26},
    "ai_relevance": {"sum": ai_sum, "count": ai_cnt},
    "verify": {"budget": vr["stats"]["budget_verdict"],
               "classification": vr["stats"]["classification_verdict"],
               "error_types": {"6열 시프트": 25, "증감필드 누락·오기": 20, "다행 총괄표 부분파싱": 3, "신규 순증 처리": 1},
               "agreement": vr["stats"]["recheck_agreement"],
               "name_mismatch": vr["stats"]["name_match_false"]},
    "talent": {"summary": tf["summary"], "yearly": tal_year,
               "by_dept": [{"dept": r["department"], "core": r["talent_core"], "partial": r["talent_partial"]}
                            for r in drows if r["talent_core"] + r["talent_partial"] > 0],
               "top": sorted(([{"id": t["id"], "dept": t["department"], "name": t["project_name"],
                                "cat": t["category"], "b26": t["b2026"] or 0} for t in tf["projects"]]),
                             key=lambda x: -x["b26"])[:15],
               "dups": dup_groups},
    "by_dept": drows,
    "by_domain": domrows,
    "type": {"sum": type_sum, "count": type_cnt},
    "top_inc": top_inc, "top_dec": top_dec,
    "projects": slim,
}

js = "// 자동 생성: scripts/phase6_dashboard_data.py (2026-07-28)\nconst DATA = " + \
     json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n"
(DATA / "data.js").write_text(js, encoding="utf-8")
print(f"data.js: {(DATA/'data.js').stat().st_size/1024:.0f}KB")
print("합계(보정): 2024", f"{tot24:,.0f}", "/ 2025", f"{tot25:,.0f}", "/ 2026", f"{tot26:,.0f}",
      f"(미보정 {tot26_raw:,.0f})")
