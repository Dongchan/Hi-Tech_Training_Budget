# -*- coding: utf-8 -*-
"""Phase 4 사전: 인재양성 후보 사업 추출 (이중 필터)
- Tier A: ai_domains에 '교육/인재' 포함 (66건)
- Tier B: 사업명에 인재양성 키워드 (강한 신호)
- Tier C: 사업목적/내용/키워드에만 등장 (약한 신호, Phase 3 판정으로 확정)
출력: analysis/talent_candidates.json
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(r"D:\AI_Work\Claude\Hi-Tech_Training_Budget")
db = json.load(open(BASE / "KAIB2026" / "data" / "budget_db.json", encoding="utf-8"))
projects = db["projects"]

NAME_KW = ["인재", "인력양성", "인력 양성", "양성", "교육", "훈련", "대학", "대학원",
           "아카데미", "장학", "연수", "역량강화교육", "스쿨"]
BODY_KW = ["인재양성", "인력양성", "전문인력", "교육과정", "교육훈련", "석박사", "대학원",
           "장학", "아카데미", "커리큘럼", "재직자 교육", "현장인력"]

# 사업명 키워드 중 오탐 주의: '양성'은 '조성' 아님, '교육'은 부처명 제외
def name_hit(p):
    n = p.get("project_name") or ""
    return [k for k in NAME_KW if k in n]


def body_hit(p):
    text = " ".join([p.get("purpose") or "", p.get("description") or "",
                     " ".join(p.get("keywords") or [])])
    return [k for k in BODY_KW if k in text]


def b26(p):
    v = (p.get("budget") or {}).get("2026_budget")
    return v if isinstance(v, (int, float)) else 0


cands = {}
for p in projects:
    tiers = []
    dom = "교육/인재" in (p.get("ai_domains") or [])
    nh, bh = name_hit(p), body_hit(p)
    if dom:
        tiers.append("A")
    if nh:
        tiers.append("B")
    if bh:
        tiers.append("C")
    if tiers:
        cands[p["id"]] = {
            "id": p["id"], "name": p["name"], "department": p["department"],
            "project_name": p["project_name"], "tiers": tiers,
            "name_keywords": nh, "body_keywords": bh,
            "ai_domains": p.get("ai_domains"),
            "budget_2024": (p.get("budget") or {}).get("2024_settlement"),
            "budget_2025": (p.get("budget") or {}).get("2025_original"),
            "budget_2025_supp": (p.get("budget") or {}).get("2025_supplementary"),
            "budget_2026": b26(p),
        }

by_tier = {"A": [], "B": [], "C_only": []}
for c in cands.values():
    if "A" in c["tiers"]:
        by_tier["A"].append(c["id"])
    elif "B" in c["tiers"]:
        by_tier["B"].append(c["id"])
    else:
        by_tier["C_only"].append(c["id"])

out = {
    "counts": {k: len(v) for k, v in by_tier.items()},
    "total_candidates": len(cands),
    "sum_2026_A": sum(c["budget_2026"] for c in cands.values() if "A" in c["tiers"]),
    "sum_2026_A_or_B": sum(c["budget_2026"] for c in cands.values() if "A" in c["tiers"] or "B" in c["tiers"]),
    "by_tier": by_tier,
    "candidates": list(cands.values()),
}
with open(BASE / "analysis" / "talent_candidates.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("후보 총", len(cands), "건 | Tier A(도메인):", len(by_tier["A"]),
      "| B(사업명, A제외):", len(by_tier["B"]), "| C만(본문):", len(by_tier["C_only"]))
print("2026 예산 합계 — A:", f"{out['sum_2026_A']:,.0f}", "/ A∪B:", f"{out['sum_2026_A_or_B']:,.0f}", "백만원")
tb = sorted((c for c in cands.values() if "B" in c["tiers"] and "A" not in c["tiers"]),
            key=lambda c: -c["budget_2026"])
print("\nTier B (도메인 누락 의심) 상위 15건:")
for c in tb[:15]:
    print(f"  id {c['id']:3d} | {c['department']} | {c['project_name'][:38]} | {c['budget_2026']:,.0f} | kw={c['name_keywords']}")
