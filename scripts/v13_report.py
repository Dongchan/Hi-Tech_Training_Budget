# -*- coding: utf-8 -*-
"""v1.3: 중복성 검토 보고서 생성"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(r"D:\AI_Work\Claude\Hi-Tech_Training_Budget")
doc = json.load(open(BASE / "analysis" / "duplication_review_v13.json", encoding="utf-8"))
db = json.load(open(BASE / "KAIB2026" / "data" / "budget_db.json", encoding="utf-8"))
pname = {p["id"]: (p["department"], p["project_name"]) for p in db["projects"]}
KO, SEV = doc["legend_ko"], doc["severity_ko"]
groups = doc["groups"]

L = []
L.append("# 중복·유사 사업 검토 보고서 (v1.3)")
L.append("")
L.append("- 작성일: 2026-07-29 | 근거 계획: `Plans\\Plan_26.07.29_v1.3.md`")
L.append("- 대상: 인재양성 사업이 걸린 유사도 그룹 13개, 구성 사업 86개")
L.append("- 방법: 그룹당 검토 에이전트(Opus 5 medium) 1명이 구성 사업의 PDF 원문(사업목적·내용·내역)을 비교 판정, 리더 종합")
L.append("- 판정 체계: 중복 소지 / 일부 중복 소지 / 보완·분담 / 무관 + 심각도(상·중·하)")
L.append("")
L.append("## 1. 요약")
L.append("")
dist = {}
for r in groups.values():
    dist[r["verdict"]] = dist.get(r["verdict"], 0) + 1
L.append("| 판정 | 그룹 수 |")
L.append("|---|---:|")
for v in ["duplicate", "mixed", "complementary", "unrelated"]:
    L.append(f"| {KO[v]} | {dist.get(v, 0)} |")
L.append("")
L.append("- 그룹 전체가 중복인 사례는 없음. 다만 8개 그룹에서 **특정 사업 쌍의 내역 단위 중복 소지** 확인")
highs = [gid for gid, r in groups.items() if r["severity"] == "high"]
L.append(f"- 심각도 '상' {len(highs)}개 그룹(그룹 {', '.join(highs)})은 통합·조정 검토가 필요한 수준으로 판정")
L.append("- 유사도 분석만으로 묶인 그룹 중 상당수는 공통 서식 문구·명칭 유사에 따른 것으로 실질 무관")
L.append("")
L.append("## 2. 그룹별 판정")
L.append("")
for gid in sorted(groups, key=int):
    r = groups[gid]
    L.append(f"### 그룹 {gid} · {KO[r['verdict']]} (심각도 {SEV[r['severity']]})")
    L.append("")
    L.append(f"- 판정 요지: {r['summary']}")
    if r.get("overlap_points"):
        L.append("- 겹침 지점 또는 구분 근거:")
        for o in r["overlap_points"]:
            L.append(f"  - {o}")
    if r.get("suggestion"):
        L.append(f"- 제언: {r['suggestion']}")
    L.append("- 구성 사업 역할:")
    for m in r.get("member_roles", []):
        d, n = pname.get(m["id"], ("?", f"id {m['id']}"))
        L.append(f"  - {d} · {n}: {m['role']}")
    L.append("")
L.append("## 3. 유의사항")
L.append("")
L.append("1. 본 판정은 예산 설명자료 원문 기준의 내용 비교이며, 실제 사업 통합·조정은 집행 현황·성과를 포함한 정책 검토 사안임")
L.append("2. 대상은 인재양성 관련 13개 그룹에 한정. 전체 유사도 그룹(102개)의 나머지는 미검토")
L.append("3. 판정 원자료: `analysis\\duplication_review_v13.json`")
L.append("")

out = BASE / "Reports" / "중복성_검토_v1.3_26.07.29.md"
out.write_text("\n".join(L), encoding="utf-8")
print("보고서 생성:", out, f"({out.stat().st_size/1024:.0f}KB)")
