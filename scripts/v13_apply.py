# -*- coding: utf-8 -*-
"""v1.3: 중복성 판정 결과 통합
출력: analysis/duplication_review_v13.json + 콘솔 요약
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(r"D:\AI_Work\Claude\Hi-Tech_Training_Budget")
JOURNAL = Path(r"C:\Users\krivet\.claude\projects\D--AI-Work-Claude-Hi-Tech-Training-Budget"
               r"\c80bcfcf-6051-44f4-b439-b0c8f880d49f\subagents\workflows\wf_22ac05db-429\journal.jsonl")

KO = {"duplicate": "중복 소지", "complementary": "보완·분담", "unrelated": "무관", "mixed": "일부 중복 소지"}
SEV = {"high": "상", "medium": "중", "low": "하"}

reviews = {}
for line in open(JOURNAL, encoding="utf-8"):
    d = json.loads(line)
    if d.get("type") != "result":
        continue
    r = d.get("result")
    if isinstance(r, dict) and "group_id" in r:
        reviews[r["group_id"]] = r

print(f"수집: {len(reviews)}/13 그룹")
missing = sorted(set(range(1, 14)) - set(reviews))
if missing:
    print("!! 미수집 그룹:", missing)

out = {"generated": "2026-07-29", "method": "그룹당 Opus 5 medium 1명, 구성 사업 PDF 원문 비교 판정",
       "legend_ko": KO, "severity_ko": SEV,
       "groups": {str(k): reviews[k] for k in sorted(reviews)}}
json.dump(out, open(BASE / "analysis" / "duplication_review_v13.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("\n== 그룹별 판정 ==")
for gid in sorted(reviews):
    r = reviews[gid]
    print(f"그룹 {gid:2d} [{KO[r['verdict']]:7s}/{SEV[r['severity']]}] {r['summary'][:88]}")
print("\n판정 분포:", {KO[v]: sum(1 for r in reviews.values() if r["verdict"] == v)
                     for v in ["duplicate", "mixed", "complementary", "unrelated"]})
print("저장: analysis/duplication_review_v13.json")
