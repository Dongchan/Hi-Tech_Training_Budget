# -*- coding: utf-8 -*-
"""v1.2: 내역 재추출 결과 통합·판별
사업·연도별 분류:
  FIXED          재추출 내역 합 ≈ 보정 모예산 (추출오류였음 → 보정)
  CONCEPT_2024   2024년: 집행액 합 ≈ 모예산(결산) — 개념 차이(정상), 내역표는 예산액 기준
  SOURCE         재추출 합 ≈ PDF 합계행이나 모예산과 불일치 — PDF 원본 자체 불일치
  NO_DETAIL      내역 미기재
  RESIDUAL       위 어디에도 해당 없음 (잔여)
출력: analysis/sub_projects_corrections_v12.json
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(r"D:\AI_Work\Claude\Hi-Tech_Training_Budget")
JOURNAL = Path(r"C:\Users\krivet\.claude\projects\D--AI-Work-Claude-Hi-Tech-Training-Budget"
               r"\c80bcfcf-6051-44f4-b439-b0c8f880d49f\subagents\workflows\wf_a84a4ae7-1dd\journal.jsonl")

results = {}
for line in open(JOURNAL, encoding="utf-8"):
    d = json.loads(line)
    if d.get("type") != "result":
        continue
    for r in (d.get("result") or {}).get("results", []):
        results[r["id"]] = r
print(f"수집: {len(results)}건")

db = json.load(open(BASE / "KAIB2026" / "data" / "budget_db.json", encoding="utf-8"))
FIX = {int(k): v for k, v in json.load(open(BASE / "analysis" / "budget_corrections_v11.json",
                                            encoding="utf-8"))["corrections"].items()}
proj = {p["id"]: p for p in db["projects"]}
TOL = 2.0


def parent_vals(pid):
    p = proj[pid]
    b = p.get("budget") or {}
    if pid in FIX:
        f = FIX[pid]
        return {"2024": f.get("b2024"), "2025": f.get("b2025_original"), "2026": f.get("b2026_budget")}
    def num(x):
        return x if isinstance(x, (int, float)) else None
    return {"2024": num(b.get("2024_settlement")), "2025": num(b.get("2025_original")),
            "2026": num(b.get("2026_budget"))}


def close(a, b):
    return a is not None and b is not None and abs(a - b) <= TOL


status_counter = Counter()
out = {}
residual_detail = []
for pid, r in sorted(results.items()):
    pv = parent_vals(pid)
    subs = r["subs"]
    status = {}
    for yr, tkey in [("2024", "total_2024"), ("2025", "total_2025"), ("2026", "total_2026")]:
        vals = [s.get("b" + yr) for s in subs if isinstance(s.get("b" + yr), (int, float))]
        ssum = round(sum(vals), 1) if vals else None
        parent = pv[yr]
        trow = r.get(tkey)
        if not subs:
            st = "NO_DETAIL"
        elif parent is None or ssum is None:
            st = "NO_DATA"
        elif close(ssum, parent):
            st = "FIXED"
        elif yr == "2024" and close(r.get("exec_2024_total"), parent):
            st = "CONCEPT_2024"
        elif trow is not None and close(ssum, trow):
            st = "SOURCE"
        else:
            st = "RESIDUAL"
            residual_detail.append((pid, yr, ssum, parent, trow, (r.get("note") or "")[:60]))
        status[yr] = {"sub_sum": ssum, "parent": parent, "total_row": trow, "status": st}
        status_counter[yr, st] += 1
    out[pid] = {"subs": subs, "totals": {k: r.get("total_" + k) for k in ["2024", "2025", "2026"]},
                "exec_2024_total": r.get("exec_2024_total"), "note": r.get("note", ""),
                "status_by_year": status}

print("\n== 사업·연도별 판별 ==")
for yr in ["2024", "2025", "2026"]:
    row = {st: status_counter[yr, st] for st in ["FIXED", "CONCEPT_2024", "SOURCE", "NO_DETAIL", "NO_DATA", "RESIDUAL"]}
    print(f"  {yr}:", {k: v for k, v in row.items() if v})

n_subs_old = sum(len(proj[pid].get("sub_projects") or []) for pid in results)
n_subs_new = sum(len(r["subs"]) for r in results.values())
print(f"\n내역 행 수 (대상 165건 내): {n_subs_old} → {n_subs_new} ({n_subs_new - n_subs_old:+d})")

print("\nRESIDUAL 상세 (상위 15):")
for x in residual_detail[:15]:
    print("  ", x)

json.dump({"generated": "2026-07-28", "method": "Opus 5 medium × 14, 기능별 예산 내역 표 재추출",
           "legend": {"FIXED": "재추출로 모예산과 일치(보정)", "CONCEPT_2024": "결산=집행액 개념 차이(정상)",
                       "SOURCE": "PDF 원본 자체 불일치", "NO_DETAIL": "내역 미기재", "RESIDUAL": "잔여 불일치"},
           "projects": {str(k): v for k, v in out.items()}},
          open(BASE / "analysis" / "sub_projects_corrections_v12.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n저장: analysis/sub_projects_corrections_v12.json")
