# -*- coding: utf-8 -*-
"""v1.1 확정: 리더 판정 반영 + talent_final 재계산
1) id 519: '교육/인재' 추가 기각 (부수적 요소 — id 133과 동일 기준)
2) talent 96건 core/partial을 개정 도메인 기준으로 재계산
   core = 교육/인재 ∈ 개정도메인 OR 사업명 강한 키워드
3) 인재양성 예산을 v1.1 확정값으로 갱신
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(r"D:\AI_Work\Claude\Hi-Tech_Training_Budget")
STRONG_KW = ["인재", "양성", "인력", "교육", "훈련", "대학", "아카데미", "장학", "연수"]

# ---- 1) 리더 판정: id 519 ----
rev_doc = json.load(open(BASE / "analysis" / "ai_domains_revised.json", encoding="utf-8"))
r519 = rev_doc["revisions"]["519"]
if "교육/인재" in r519["revised_domains"]:
    r519["revised_domains"].remove("교육/인재")
    r519["leader_override"] = ("교육/인재 추가 기각: 창업 교육 프로그램은 부수 요소로, "
                               "id 133에 적용된 '부수적이면 제거' 기준과 동일하게 처리 (리더 판정)")
rev_doc["leader_adjudication"] = "id 519 교육/인재 기각. id 133 교육/인재 제거는 승인(인재양성 목록에서는 partial로 재구분)."
json.dump(rev_doc, open(BASE / "analysis" / "ai_domains_revised.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
REV = {int(k): v for k, v in rev_doc["revisions"].items()}

# ---- 2) talent_final 재계산 ----
db = json.load(open(BASE / "KAIB2026" / "data" / "budget_db.json", encoding="utf-8"))
proj = {p["id"]: p for p in db["projects"]}
FIX = {int(k): v for k, v in json.load(open(BASE / "analysis" / "budget_corrections_v11.json",
                                            encoding="utf-8"))["corrections"].items()}
tf = json.load(open(BASE / "analysis" / "talent_final.json", encoding="utf-8"))


def dom_of(pid):
    return REV[pid]["revised_domains"] if pid in REV else (proj[pid].get("ai_domains") or [])


changes = []
for t in tf["projects"]:
    pid = t["id"]
    in_dom = "교육/인재" in dom_of(pid)
    name_hit = [k for k in STRONG_KW if k in (t["project_name"] or "")]
    new_cat = "core" if (in_dom or name_hit) else "partial"
    if new_cat != t["category"]:
        changes.append((pid, t["project_name"][:30], t["category"], "->", new_cat))
    t["category"] = new_cat
    t["in_edu_domain"] = in_dom
    t["name_keywords"] = name_hit
    # v1.1 확정 예산 반영
    if pid in FIX:
        f = FIX[pid]
        if f.get("b2024") is not None or t["b2024"] is None:
            t["b2024"] = f.get("b2024")
        if f.get("b2025_original") is not None or t["b2025"] is None:
            t["b2025"] = f.get("b2025_original")
        t["b2026"] = f["b2026_budget"]
        t["corrected"] = True
        t["correction_note"] = "v1.1 확정값: " + f.get("note", "")[:100]

print("구분 변경:", len(changes))
for c in changes:
    print("  ", c)

# summary 재계산
core = [t for t in tf["projects"] if t["category"] == "core"]
part = [t for t in tf["projects"] if t["category"] == "partial"]


def tot(items, key):
    return round(sum(t[key] or 0 for t in items), 1)


tf["summary"]["core"] = {"count": len(core), "b2024": tot(core, "b2024"),
                          "b2025": tot(core, "b2025"), "b2026": tot(core, "b2026")}
tf["summary"]["partial"] = {"count": len(part), "b2026": tot(part, "b2026")}
tf["summary"]["all"] = {"b2026": tot(tf["projects"], "b2026")}
tf["summary"]["version"] = "v1.1 (2026-07-28): 예산 확정값 반영, core/partial을 개정 도메인 기준 재계산"

by_dept = defaultdict(lambda: {"count": 0, "b2026": 0.0})
for t in tf["projects"]:
    by_dept[t["department"]]["count"] += 1
    by_dept[t["department"]]["b2026"] += t["b2026"] or 0
tf["by_department"] = {k: {"count": v["count"], "b2026": round(v["b2026"], 1)}
                       for k, v in sorted(by_dept.items(), key=lambda x: -x[1]["b2026"])}

tf["projects"].sort(key=lambda t: (t["category"], -(t["b2026"] or 0)))
json.dump(tf, open(BASE / "analysis" / "talent_final.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

s = tf["summary"]
print(f"\n인재양성 96건 (v1.1): core {s['core']['count']}건 {s['core']['b2026']:,.0f} / "
      f"partial {s['partial']['count']}건 {s['partial']['b2026']:,.0f} / 합계 {s['all']['b2026']:,.0f} 백만원")
