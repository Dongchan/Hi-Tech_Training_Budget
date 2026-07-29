# -*- coding: utf-8 -*-
"""Dash_board 데이터 자산 생성 (v1.1)
- data/*.csv (UTF-8 BOM) + data/data.js
- v1.1 보정 반영: analysis/budget_corrections_v11.json (49건 7필드 확정값),
  analysis/ai_domains_revised.json (195건 재분류) — 파일이 있으면 자동 적용
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

# ---- v1.1 보정 파일 ----
fix_path = BASE / "analysis" / "budget_corrections_v11.json"
rev_path = BASE / "analysis" / "ai_domains_revised.json"
FIX = {int(k): v for k, v in json.load(open(fix_path, encoding="utf-8"))["corrections"].items()} if fix_path.exists() else {}
REV = {int(k): v for k, v in json.load(open(rev_path, encoding="utf-8"))["revisions"].items()} if rev_path.exists() else {}
print(f"보정 적용: 예산 {len(FIX)}건 / 도메인 재분류 {len(REV)}건")


def num(x):
    return x if isinstance(x, (int, float)) else None


def clean_note(s):
    """대시보드 표시용 텍스트 정제: EM 대시 제거 (원자료 CSV는 원문 유지)"""
    import re
    return re.sub(r"\s*—\s*", ", ", s or "")


def j(lst):
    return ";".join(lst or [])


def corr_field(pid, key, fallback):
    """보정값이 있으면 사용, null이면 fallback 유지 여부: 예산 필드는 보정 파일이 정답이므로 null도 존중"""
    if pid in FIX and key in FIX[pid]:
        return FIX[pid][key]
    return fallback


def vals(p):
    b = p.get("budget") or {}
    pid = p["id"]
    raw26 = num(b.get("2026_budget"))
    if pid in FIX:
        f = FIX[pid]
        return {"b24": f.get("b2024"), "b25": f.get("b2025_original"),
                "b26": raw26, "b26c": f["b2026_budget"], "corr": abs((f["b2026_budget"] or 0) - (raw26 or 0)) > 2,
                "note": f.get("note", "")}
    return {"b24": num(b.get("2024_settlement")), "b25": num(b.get("2025_original")),
            "b26": raw26, "b26c": raw26, "corr": False, "note": ""}


def dom_of(p):
    return REV[p["id"]]["revised_domains"] if p["id"] in REV else (p.get("ai_domains") or [])


# ---------------- CSV 1: 전체 사업 raw ----------------
rows = []
for p in projects:
    b = p.get("budget") or {}
    v = verdict.get(p["id"], {})
    t = talent.get(p["id"])
    w = vals(p)
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
        "ai_domains_revised_v11": j(REV[p["id"]]["revised_domains"]) if p["id"] in REV else "",
        "ai_tech": j(p.get("ai_tech")), "keywords": j(p.get("keywords")),
        "b2024_settlement": num(b.get("2024_settlement")), "b2024_corrected": w["b24"],
        "b2025_original": num(b.get("2025_original")), "b2025_corrected": w["b25"],
        "b2025_supplementary": num(b.get("2025_supplementary")),
        "b2026_request": num(b.get("2026_request")),
        "b2026_budget": w["b26"], "b2026_corrected": w["b26c"],
        "correction_note": w["note"],
        "change_amount": corr_field(p["id"], "change_amount", num(b.get("change_amount"))),
        "change_rate": corr_field(p["id"], "change_rate", num(b.get("change_rate"))),
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

# ---------------- CSV 2: 내역사업 (v1.2 보정 반영) ----------------
subfix_path = BASE / "analysis" / "sub_projects_corrections_v12.json"
SUBFIX = ({int(k): v for k, v in json.load(open(subfix_path, encoding="utf-8"))["projects"].items()}
          if subfix_path.exists() else {})
subs = []
for p in projects:
    pid = p["id"]
    if pid in SUBFIX and SUBFIX[pid]["subs"]:
        for s in SUBFIX[pid]["subs"]:
            subs.append({"parent_id": pid, "department": p["department"],
                         "parent_name": p["project_name"], "sub_name": s.get("name"),
                         "b2024": s.get("b2024"), "b2025": s.get("b2025"), "b2026": s.get("b2026"),
                         "source": "v1.2_corrected"})
    else:
        for s in (p.get("sub_projects") or []):
            subs.append({"parent_id": pid, "department": p["department"],
                         "parent_name": p["project_name"], "sub_name": s.get("name"),
                         "b2024": num(s.get("budget_2024")), "b2025": num(s.get("budget_2025")),
                         "b2026": num(s.get("budget_2026")), "source": "original"})
write_csv(DATA / "sub_projects_raw.csv", subs)
print("  내역 v1.2 보정 모사업:", sum(1 for pid in SUBFIX if SUBFIX[pid]["subs"]), "건")

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
                  "corrected_v11": "Y" if r["id"] in FIX else "",
                  "classification_verdict": r["classification_verdict"],
                  "classification_detail": r.get("classification_detail", ""),
                  "reclassified_v11": "Y" if r["id"] in REV else "",
                  "name_match": r.get("name_match"), "name_detail": r.get("name_detail", ""),
                  "ai_relevance": r["ai_relevance"], "source": r.get("source")})
write_csv(DATA / "verification_issues.csv", irows)

# ---------------- 집계 ----------------
by_dept = defaultdict(lambda: {"count": 0, "b2024": 0.0, "b2025": 0.0, "b2026": 0.0,
                                "talent_core": 0.0, "talent_partial": 0.0})
for p in projects:
    d = by_dept[p["department"]]
    w = vals(p)
    d["count"] += 1
    d["b2024"] += w["b24"] or 0
    d["b2025"] += w["b25"] or 0
    d["b2026"] += w["b26c"] or 0
    t = talent.get(p["id"])
    if t:
        d["talent_" + t["category"]] += t["b2026"] or 0
drows = [{"department": k, **{kk: round(vv, 1) for kk, vv in v.items()}}
         for k, v in sorted(by_dept.items(), key=lambda x: -x[1]["b2026"])]
write_csv(DATA / "by_department.csv", drows)

by_dom = defaultdict(lambda: {"count": 0, "b2024": 0.0, "b2025": 0.0, "b2026": 0.0})
for p in projects:
    w = vals(p)
    for d in dom_of(p):
        by_dom[d]["count"] += 1
        by_dom[d]["b2024"] += w["b24"] or 0
        by_dom[d]["b2025"] += w["b25"] or 0
        by_dom[d]["b2026"] += w["b26c"] or 0
domrows = [{"domain": k, "count": v["count"], "b2024": round(v["b2024"], 1),
            "b2025": round(v["b2025"], 1), "b2026": round(v["b2026"], 1)}
           for k, v in sorted(by_dom.items(), key=lambda x: -x[1]["b2026"])]
write_csv(DATA / "by_domain.csv", domrows)

# ---------------- data.js ----------------
slim = []
for p in projects:
    v = verdict.get(p["id"], {})
    t = talent.get(p["id"])
    w = vals(p)
    slim.append({
        "id": p["id"], "dept": p["department"], "name": p["project_name"],
        "b24": w["b24"], "b25": w["b25"], "b26": w["b26"], "b26c": w["b26c"], "corr": w["corr"],
        "dom": dom_of(p), "rev": p["id"] in REV,
        "rnd": bool(p.get("is_rnd")), "info": bool(p.get("is_informatization")),
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


def type_of(x):
    return "R&D" if x["rnd"] else ("정보화" if x["info"] else "일반")


type_trend = {t: {y: round(sum(x["b" + k] or 0 for x in slim if type_of(x) == t), 1)
                  for y, k in [("2024", "24"), ("2025", "25"), ("2026", "26c")]}
              for t in ["R&D", "정보화", "일반"]}

# 추이 통계: 신규·급증·감액 (2025 본예산 대비 2026 확정)
new_p = [x for x in slim if not (x["b25"] or 0) and (x["b26c"] or 0) > 0]
up2x = [x for x in slim if (x["b25"] or 0) > 0 and (x["b26c"] or 0) >= 2 * x["b25"]]
up_p = [x for x in slim if (x["b25"] or 0) > 0 and (x["b26c"] or 0) > x["b25"]]
down_p = [x for x in slim if (x["b25"] or 0) > 0 and (x["b26c"] or 0) < x["b25"]]
trend_stats = {
    "new": {"count": len(new_p), "sum": round(sum(x["b26c"] or 0 for x in new_p), 1)},
    "up2x": {"count": len(up2x), "sum": round(sum((x["b26c"] or 0) - x["b25"] for x in up2x), 1)},
    "up": {"count": len(up_p)},
    "down": {"count": len(down_p), "sum": round(sum(x["b25"] - (x["b26c"] or 0) for x in down_p), 1)},
}
type_cnt = {
    "R&D": sum(1 for x in slim if x["rnd"]),
    "정보화": sum(1 for x in slim if x["info"] and not x["rnd"]),
    "일반": sum(1 for x in slim if not x["rnd"] and not x["info"]),
}

dup_groups = [{"n": len(g["all_ids"]),
               "names": [f'{talent[i]["department"]} · {talent[i]["project_name"]}' for i in g["talent_ids"]]}
              for g in tf["duplicate_groups"]]

n_b26_changed = sum(1 for x in slim if x["corr"])
payload = {
    "meta": {"generated": "2026-07-28 (v1.1)", "source": "AI_예산사업_통합_설명자료.pdf (5,296p) / KAIB2026 파싱 데이터 전수 검증·보정",
             "unit": "백만원", "corrections": n_b26_changed, "reclassified": len(REV), "tot26_raw": tot26_raw},
    "totals": {"projects": 533, "departments": 41, "b2024": tot24, "b2025": tot25, "b2026": tot26},
    "ai_relevance": {"sum": ai_sum, "count": ai_cnt},
    "verify": {"budget": vr["stats"]["budget_verdict"],
               "classification": vr["stats"]["classification_verdict"],
               "error_types": {"6열 시프트": 25, "증감필드 누락·오기": 20, "다행 총괄표 부분파싱": 3, "신규 순증 처리": 1},
               "agreement": vr["stats"]["recheck_agreement"],
               "name_mismatch": vr["stats"]["name_match_false"]},
    "talent": {"summary": tf["summary"], "yearly": tal_year,
               "notes": {str(t["id"]): clean_note(t.get("talent_note")) for t in tf["projects"]},
               "partial_list": sorted(([{"id": t["id"], "dept": t["department"], "name": t["project_name"],
                                          "b26": t["b2026"] or 0, "note": clean_note(t.get("talent_note"))}
                                         for t in tf["projects"] if t["category"] == "partial"]),
                                       key=lambda x: -x["b26"]),
               "by_dept": [{"dept": r["department"], "core": r["talent_core"], "partial": r["talent_partial"]}
                            for r in drows if r["talent_core"] + r["talent_partial"] > 0],
               "top": sorted(([{"id": t["id"], "dept": t["department"], "name": t["project_name"],
                                "cat": t["category"], "b26": t["b2026"] or 0} for t in tf["projects"]]),
                             key=lambda x: -x["b26"])[:15],
               "dups": dup_groups},
    "by_dept": drows,
    "by_domain": domrows,
    "type": {"sum": type_sum, "count": type_cnt, "trend": type_trend},
    "trend_stats": trend_stats,
    "top_inc": top_inc, "top_dec": top_dec,
    "projects": slim,
}

js = "// 자동 생성: scripts/phase6_dashboard_data.py v1.1 (2026-07-28)\nconst DATA = " + \
     json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n"
(DATA / "data.js").write_text(js, encoding="utf-8")
print(f"data.js: {(DATA/'data.js').stat().st_size/1024:.0f}KB")
print(f"2026 확정예산 변경 {n_b26_changed}건 반영")
print("합계(보정): 2024", f"{tot24:,.0f}", "/ 2025", f"{tot25:,.0f}", "/ 2026", f"{tot26:,.0f}",
      f"(미보정 {tot26_raw:,.0f}, 차이 {tot26-tot26_raw:+,.0f})")

# 인재양성 예산 정합 체크 (talent_final의 보정값 vs v1.1 확정값)
warn = []
for pid, t in talent.items():
    if pid in FIX and abs((FIX[pid]["b2026_budget"] or 0) - (t["b2026"] or 0)) > 2:
        warn.append((pid, t["b2026"], FIX[pid]["b2026_budget"]))
print("인재양성 예산 정합 경고:", warn if warn else "없음 (talent_final과 v1.1 확정값 일치)")
