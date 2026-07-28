# -*- coding: utf-8 -*-
"""v1.1: 교육/인재 도메인 ↔ 인재양성 96건 정합 점검 (리더 검토용)"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(r"D:\AI_Work\Claude\Hi-Tech_Training_Budget")
db = json.load(open(BASE / "KAIB2026" / "data" / "budget_db.json", encoding="utf-8"))
rev = {int(k): v for k, v in json.load(open(BASE / "analysis" / "ai_domains_revised.json", encoding="utf-8"))["revisions"].items()}
tf = json.load(open(BASE / "analysis" / "talent_final.json", encoding="utf-8"))
talent = {t["id"]: t for t in tf["projects"]}
proj = {p["id"]: p for p in db["projects"]}

dom = {pid: (rev[pid]["revised_domains"] if pid in rev else (p.get("ai_domains") or []))
       for pid, p in proj.items()}
after = {pid for pid, d in dom.items() if "교육/인재" in d}
tset = set(talent)

print("== 교육/인재 도메인인데 인재양성 목록에 없는 사업 ==")
for pid in sorted(after - tset):
    p = proj[pid]
    print(f"  id {pid} | {p['department']} | {p['project_name'][:42]} | 재분류={pid in rev}")
    if pid in rev:
        print("     근거:", rev[pid]["rationale"][:120])

print("\n== 인재양성 96건 중 교육/인재 도메인 없는 사업 ==")
for pid in sorted(tset - after):
    t = talent[pid]
    print(f"  id {pid} [{t['category']:7s}] {t['department']} | {t['project_name'][:38]} | 재분류대상={pid in rev}")
