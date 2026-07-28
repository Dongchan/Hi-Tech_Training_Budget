# -*- coding: utf-8 -*-
"""Phase 1: data/ JSON 실측 스키마 분석 (vs Data-format.md 문서 스키마 대조용)"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(r"D:\AI_Work\Claude\Hi-Tech_Training_Budget\KAIB2026\data")


def load(name):
    with open(BASE / name, encoding="utf-8") as f:
        return json.load(f)


def field_stats(items, label):
    print(f"\n=== {label}: {len(items)}건 ===")
    keys = Counter()
    for it in items:
        for k in it.keys():
            keys[k] += 1
    for k, c in keys.most_common():
        mark = "" if c == len(items) else f"  <-- 누락 {len(items)-c}건"
        print(f"  {k}: {c}{mark}")


raw = load("budget_raw.json")
db = load("budget_db.json")
toc = load("toc_mapping.json")

print("## budget_raw.json")
print("type:", type(raw).__name__)
if isinstance(raw, list):
    field_stats(raw, "budget_raw projects")
elif isinstance(raw, dict):
    print("top-level keys:", list(raw.keys()))
    projects_raw = raw.get("projects", [])
    field_stats(projects_raw, "budget_raw projects")

print("\n## budget_db.json")
print("top-level keys:", list(db.keys()))
meta = db.get("metadata", {})
print("metadata:", json.dumps(meta, ensure_ascii=False)[:2000])
projects = db.get("projects", [])
field_stats(projects, "budget_db projects")

print("\n## analysis 섹션 키:")
for k, v in db.get("analysis", {}).items():
    size = len(v) if isinstance(v, (list, dict)) else v
    print(f"  {k}: {type(v).__name__} ({size})")

print("\n## toc_mapping.json")
print("type:", type(toc).__name__, "/ 건수:", len(toc) if isinstance(toc, (list, dict)) else "?")
if isinstance(toc, list) and toc:
    print("sample:", json.dumps(toc[0], ensure_ascii=False))
elif isinstance(toc, dict):
    print("top-level keys:", list(toc.keys())[:10])

# AI 분류 실측
if projects:
    domains = Counter()
    techs = Counter()
    edu = []
    for p in projects:
        for d in p.get("ai_domains", []):
            domains[d] += 1
        for t in p.get("ai_tech", []):
            techs[t] += 1
        if "교육/인재" in p.get("ai_domains", []):
            edu.append((p.get("department"), p.get("project_name"), p.get("budget", {}).get("2026_budget")))
    print(f"\n## ai_domains ({len(domains)}종):")
    for d, c in domains.most_common():
        print(f"  {d}: {c}")
    print(f"\n## ai_tech ({len(techs)}종):")
    for t, c in techs.most_common():
        print(f"  {t}: {c}")
    print(f"\n## '교육/인재' 도메인 사업: {len(edu)}건")
    total = sum(b for _, _, b in edu if isinstance(b, (int, float)))
    print(f"  2026 확정예산 합계: {total:,.0f} 백만원")

# 부처 목록
src = raw if isinstance(raw, list) else raw.get("projects", [])
depts = Counter(p.get("department") for p in src)
print(f"\n## 부처: {len(depts)}개")
for d, c in depts.most_common():
    print(f"  {d}: {c}")
