# -*- coding: utf-8 -*-
"""Phase 4 최종: 검증 결과를 반영한 인재양성 예산 현황 생성
- 인재양성 최종 = Phase 3 talent_related 판정 96건
- 구분: core(주력: 교육/인재 도메인 유지 또는 사업명 키워드) / partial(요소 포함)
- 예산 보정: 시프트/다행 오류 확인 건은 PDF 실측값으로 교체
- id 527 리더 판정 반영(uncertain → mismatch, 확정예산 7,371은 유효)
출력: analysis/talent_final.json
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(r"D:\AI_Work\Claude\Hi-Tech_Training_Budget")
vr = json.load(open(BASE / "analysis" / "verification_results.json", encoding="utf-8"))
db = json.load(open(BASE / "KAIB2026" / "data" / "budget_db.json", encoding="utf-8"))
projects = {p["id"]: p for p in db["projects"]}
final = {r["id"]: r for r in vr["results"]}

# ---- 리더 판정: id 527 (PDF p.5214 실측) ----
f527 = final[527]
f527["budget_verdict"] = "mismatch"
f527["budget_detail"] = ("리더 판정(PDF p.5214 실측): 2026확정 7,371은 정확(기능별 합계 일치). "
                         "change_amount=7371→정답 1,979, change_rate=1979→정답 36.7% (텍스트 추출 순서 오류)")
f527["source"] = "leader_adjudicated"
vr["stats"]["budget_verdict"] = {"match": 484, "mismatch": 49, "uncertain": 0}
vr["stats"]["leader_note"] = "id 527 uncertain을 리더가 PDF 실측으로 mismatch 확정 (2026확정값 자체는 유효)"
json.dump(vr, open(BASE / "analysis" / "verification_results.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---- 예산 보정 (인재양성 교집합 5건 중 수치 영향 4건, PDF 실측) ----
CORR = {
    112: {"2024": 15040, "2025": 11797, "2026": 10399,
          "why": "2행 총괄표 중 사업출연금 행만 파싱됨 → 전체 합산값으로 보정"},
    242: {"2026": 9177, "why": "6열 시프트: JSON 2026_budget=증감액 → PDF 조정안(B)로 보정"},
    452: {"2026": 1705, "why": "6열 시프트: JSON 2026_budget=-202(증감) → PDF 2026예산(B)로 보정"},
    466: {"2026": 1918, "why": "6열 시프트: JSON 2026_budget=-70(증감) → PDF 확정(B)로 보정"},
}

STRONG_KW = ["인재", "양성", "인력", "교육", "훈련", "대학", "아카데미", "장학", "연수"]
edu_ids = {p["id"] for p in db["projects"] if "교육/인재" in (p.get("ai_domains") or [])}

talent = []
for pid, f in final.items():
    if not f["talent_related"]:
        continue
    p = projects[pid]
    bud = p.get("budget") or {}
    b24, b25, b26 = bud.get("2024_settlement"), bud.get("2025_original"), bud.get("2026_budget")
    corrected = pid in CORR
    if corrected:
        c = CORR[pid]
        b24 = c.get("2024", b24)
        b25 = c.get("2025", b25)
        b26 = c.get("2026", b26)
    name_hit = [k for k in STRONG_KW if k in (p.get("project_name") or "")]
    core = (pid in edu_ids) or bool(name_hit)
    talent.append({
        "id": pid, "department": p["department"], "project_name": p["project_name"],
        "category": "core" if core else "partial",
        "in_edu_domain": pid in edu_ids, "name_keywords": name_hit,
        "ai_domains": p.get("ai_domains"), "is_rnd": p.get("is_rnd"),
        "b2024": b24, "b2025": b25, "b2026": b26,
        "corrected": corrected, "correction_note": CORR.get(pid, {}).get("why"),
        "talent_note": f.get("talent_note", ""),
        "verification": {"budget": f["budget_verdict"], "classification": f["classification_verdict"]},
    })

talent.sort(key=lambda t: (t["category"], -(t["b2026"] or 0)))

def tot(items, key):
    return round(sum(t[key] or 0 for t in items), 1)

core = [t for t in talent if t["category"] == "core"]
part = [t for t in talent if t["category"] == "partial"]
by_dept = defaultdict(lambda: {"count": 0, "b2026": 0.0})
for t in talent:
    by_dept[t["department"]]["count"] += 1
    by_dept[t["department"]]["b2026"] += t["b2026"] or 0

# 중복 의심 그룹 중 인재양성 관련
tset = {t["id"] for t in talent}
dup_groups = []
for g in db["analysis"].get("duplicates", []):
    ids = {m.get("id") for m in g.get("projects", []) if isinstance(m, dict)}
    if not ids:
        continue
    hit = ids & tset
    if len(hit) >= 2:
        dup_groups.append({"keyword": g.get("keyword") or g.get("name") or "?",
                           "talent_ids": sorted(hit), "all_ids": sorted(i for i in ids if i)})

out = {
    "summary": {
        "total_talent_projects": len(talent),
        "core": {"count": len(core), "b2024": tot(core, "b2024"), "b2025": tot(core, "b2025"), "b2026": tot(core, "b2026")},
        "partial": {"count": len(part), "b2026": tot(part, "b2026")},
        "all": {"b2026": tot(talent, "b2026")},
        "vs_edu_domain": {"domain_count": len(edu_ids), "domain_b2026": 6823880.0,
                          "added": sorted(tset - edu_ids), "removed": sorted(edu_ids - tset)},
        "corrections_applied": {str(k): v for k, v in CORR.items()},
    },
    "by_department": {k: {"count": v["count"], "b2026": round(v["b2026"], 1)}
                      for k, v in sorted(by_dept.items(), key=lambda x: -x[1]["b2026"])},
    "duplicate_groups": dup_groups,
    "projects": talent,
}
json.dump(out, open(BASE / "analysis" / "talent_final.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

s = out["summary"]
print("인재양성 최종:", s["total_talent_projects"], "건")
print("  core(주력):", s["core"]["count"], "건 | 2026:", f"{s['core']['b2026']:,.0f}", "백만원")
print("  partial(요소):", s["partial"]["count"], "건 | 2026:", f"{s['partial']['b2026']:,.0f}", "백만원")
print("  전체 2026:", f"{s['all']['b2026']:,.0f}", "백만원 (도메인 기준 6,823,880 대비)")
print("\n부처별 상위 10:")
for k, v in list(out["by_department"].items())[:10]:
    print(f"  {k}: {v['count']}건, {v['b2026']:,.0f}")
print("\n중복 의심 그룹(인재양성 2건 이상 포함):", len(dup_groups))
for g in dup_groups[:8]:
    print("  -", g["keyword"], g["talent_ids"])
print("\ncore 상위 10:")
for t in core[:10]:
    print(f"  id {t['id']:3d} | {t['department']} | {t['project_name'][:34]} | {t['b2026'] or 0:,.0f}")
