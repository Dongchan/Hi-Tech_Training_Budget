# -*- coding: utf-8 -*-
"""v1.1: 워크플로 결과 통합·검증
- journal.jsonl에서 결과 수집 (스키마 형태로 예산/재분류 구분)
- 산술 자기검증 + 28종 도메인 체계 준수 검사
- 출력: analysis/budget_corrections_v11.json, analysis/ai_domains_revised.json
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(r"D:\AI_Work\Claude\Hi-Tech_Training_Budget")
JOURNAL = Path(r"C:\Users\krivet\.claude\projects\D--AI-Work-Claude-Hi-Tech-Training-Budget"
               r"\c80bcfcf-6051-44f4-b439-b0c8f880d49f\subagents\workflows\wf_42eab53e-f26\journal.jsonl")

DOMAINS = {"데이터", "디지털전환(AX)", "교육/인재", "의료/바이오", "LLM/언어모델", "보안/사이버",
           "R&D 지원", "건설/스마트시티", "AI반도체", "로봇", "통신/네트워크", "피지컬AI/디바이스",
           "교통/모빌리티", "제조/스마트팩토리", "법률/치안", "재난/안전", "농업/식품", "환경/기후",
           "에너지", "문화/콘텐츠", "행정/전자정부", "클라우드/컴퓨팅", "해양/수산", "국방/안보",
           "산림/생태", "우주/위성", "금융", "기타"}

budget, reclass = {}, {}
for line in open(JOURNAL, encoding="utf-8"):
    d = json.loads(line)
    if d.get("type") != "result":
        continue
    res = (d.get("result") or {}).get("results")
    if not res:
        continue
    if "b2026_budget" in res[0]:
        for r in res:
            budget[r["id"]] = r
    elif "revised_domains" in res[0]:
        for r in res:
            reclass[r["id"]] = r

print(f"예산 확정값 {len(budget)}건 / 재분류 {len(reclass)}건 수집")

# ---- 예산 산술 자기검증 ----
db = json.load(open(BASE / "KAIB2026" / "data" / "budget_db.json", encoding="utf-8"))
orig = {p["id"]: (p.get("budget") or {}) for p in db["projects"]}
TOL = 2.0
arith_bad, deltas = [], []
for pid, f in sorted(budget.items()):
    base25 = f.get("b2025_supplementary") if f.get("b2025_supplementary") is not None else f.get("b2025_original")
    ca = f.get("change_amount")
    if base25 is not None and ca is not None:
        if abs((f["b2026_budget"] - base25) - ca) > TOL:
            arith_bad.append((pid, f["b2026_budget"], base25, ca, f.get("note", "")[:60]))
    old = orig[pid].get("2026_budget")
    if old is not None and abs(f["b2026_budget"] - old) > TOL:
        deltas.append((pid, old, f["b2026_budget"], round(f["b2026_budget"] - old, 1)))

print(f"\n산술 자기검증 불일치: {len(arith_bad)}건")
for x in arith_bad:
    print("  ", x)
print(f"\n2026 확정예산 변경: {len(deltas)}건, 총 변화 {sum(d[3] for d in deltas):,.1f} 백만원")
for d in sorted(deltas, key=lambda x: -abs(x[3]))[:12]:
    print(f"   id {d[0]:3d}: {d[1]:>12,.0f} → {d[2]:>12,.0f} ({d[3]:+,.0f})")

# ---- 재분류 체계 검사 ----
bad_dom = [(pid, [x for x in r["revised_domains"] if x not in DOMAINS])
           for pid, r in reclass.items() if any(x not in DOMAINS for x in r["revised_domains"])]
empty = [pid for pid, r in reclass.items() if not r["revised_domains"]]
print(f"\n체계 위반 도메인: {len(bad_dom)}건 {bad_dom[:5]}")
print(f"도메인 0개 반환: {len(empty)}건 {empty[:10]}")

# 교육/인재 변화
before = {p["id"] for p in db["projects"] if "교육/인재" in (p.get("ai_domains") or [])}
after = set(before)
for pid, r in reclass.items():
    if "교육/인재" in r["revised_domains"]:
        after.add(pid)
    else:
        after.discard(pid)
tf = json.load(open(BASE / "analysis" / "talent_final.json", encoding="utf-8"))
talent_ids = {t["id"] for t in tf["projects"]}
print(f"\n'교육/인재' 도메인: {len(before)} → {len(after)}건")
print(f"  확정 인재양성 96건과의 정합: 재분류 후 교육/인재 중 인재양성 아님 {len(after - talent_ids)}건, "
      f"인재양성인데 도메인 없음 {len(talent_ids - after)}건")

# ---- 저장 ----
json.dump({"generated": "2026-07-28", "method": "Opus 5 medium × 5, PDF 원문 구조화 추출 + 산술 자기검증",
           "corrections": {str(k): v for k, v in sorted(budget.items())}},
          open(BASE / "analysis" / "budget_corrections_v11.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
json.dump({"generated": "2026-07-28", "method": "Opus 5 medium × 13, 기존 28종 체계 내 재분류",
           "revisions": {str(k): v for k, v in sorted(reclass.items())}},
          open(BASE / "analysis" / "ai_domains_revised.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n저장 완료: budget_corrections_v11.json / ai_domains_revised.json")
