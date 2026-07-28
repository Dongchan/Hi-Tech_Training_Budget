# -*- coding: utf-8 -*-
"""v1.2 확정: RESIDUAL 4건 리더 판정 반영 + 통계 산출"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(r"D:\AI_Work\Claude\Hi-Tech_Training_Budget")
f = BASE / "analysis" / "sub_projects_corrections_v12.json"
doc = json.load(open(f, encoding="utf-8"))

# 리더 판정: RESIDUAL 4건(93, 142, 364, 468)은 표 내부 불일치(합계행 ≠ 내역행 합) = 원본 오류
# 근거 확인: id 142 — PDF 합계행 3,328 vs 내역행 합 3,228 (원문 실측)
for pid in ["93", "142", "364", "468"]:
    st = doc["projects"][pid]["status_by_year"]["2026"]
    if st["status"] == "RESIDUAL":
        st["status"] = "SOURCE_TABLE"
        st["leader_note"] = "원본 표 내부 불일치: 합계행 ≠ 내역행 합 (id 142 원문 실측으로 유형 확정)"
doc["legend"]["SOURCE_TABLE"] = "PDF 원본 표 내부 불일치(합계행 ≠ 내역행 합) — 원본 오류"
doc["leader_adjudication"] = "RESIDUAL 4건(93·142·364·468, 2026년)을 SOURCE_TABLE로 확정 (id 142 원문 실측 근거)"
json.dump(doc, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

c = Counter()
for pid, p in doc["projects"].items():
    for yr, st in p["status_by_year"].items():
        c[yr, st["status"]] += 1
for yr in ["2024", "2025", "2026"]:
    print(yr, {k[1]: v for k, v in c.items() if k[0] == yr})
src25 = [pid for pid, p in doc["projects"].items() if p["status_by_year"]["2025"]["status"] == "SOURCE"]
print("2025 원본 자체 불일치(모예산≠내역표) 사업:", src25)
