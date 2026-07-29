# -*- coding: utf-8 -*-
"""Phase 5: 첨단분야 인재양성 예산현황 보고서 생성 (표 포함 전체)"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(r"D:\AI_Work\Claude\Hi-Tech_Training_Budget")
tf = json.load(open(BASE / "analysis" / "talent_final.json", encoding="utf-8"))
db = json.load(open(BASE / "KAIB2026" / "data" / "budget_db.json", encoding="utf-8"))
pname = {p["id"]: (p["department"], p["project_name"]) for p in db["projects"]}

s = tf["summary"]
core = [t for t in tf["projects"] if t["category"] == "core"]
part = [t for t in tf["projects"] if t["category"] == "partial"]


def fmt(v):
    return f"{v:,.0f}" if isinstance(v, (int, float)) else "-"


def row(t):
    note = []
    if t["corrected"]:
        note.append("예산보정")
    if not t["in_edu_domain"]:
        note.append("도메인누락")
    if t["is_rnd"]:
        note.append("R&D")
    return (f"| {t['id']} | {t['department']} | {t['project_name']} | "
            f"{fmt(t['b2024'])} | {fmt(t['b2025'])} | {fmt(t['b2026'])} | {', '.join(note)} |")


L = []
L.append("# AI 분야 인재양성 예산 현황 (2026년 AI 재정사업 기준, v1.1)")
L.append("")
L.append("- 작성일: 2026-07-28 (v1.1 개정: 예산 49건 확정값 보정 + 도메인 195건 재분류 반영, core/partial 재계산)")
L.append("- 범위: 2026년 AI 재정사업(533건) 내 인재양성 사업. 과제 관심 범위(첨단분야) 중 AI 분야 해당분임")
L.append("- 근거: `AI_예산사업_통합_설명자료.pdf`(5,296p) 파싱 데이터(KAIB2026)의 전수 검증·보정 결과")
L.append("- 목적: 메일 5번 항목(첨단분야 인재양성/인재수요 현황 파악)용 데이터 정리. 본 자료는 그중 AI 분야 담당 (기본계획 수립·인재지도 구축 활용)")
L.append("- 단위: 백만원. 2024=결산, 2025=본예산, 2026=확정예산")
L.append("")
L.append("## 1. 요약")
L.append("")
L.append("| 구분 | 사업 수 | 2026 확정예산 |")
L.append("|---|---:|---:|")
L.append(f"| **인재양성 주목적(core)**: 교육/인재 도메인(v1.1 개정 기준) 또는 사업명상 인재양성 | {s['core']['count']} | {fmt(s['core']['b2026'])} |")
L.append(f"| **인재양성 일부 포함(partial)**: 사업 내 인재양성 활동 포함 | {s['partial']['count']} | {fmt(s['partial']['b2026'])} |")
L.append(f"| **합계** | {s['total_talent_projects']} | {fmt(s['all']['b2026'])} |")
L.append("")
L.append(f"- 원 데이터의 '교육/인재' 도메인 기준(66건, {fmt(s['vs_edu_domain']['domain_b2026'])})과의 차이: "
         f"PDF 원문 대조 검증으로 **누락 {len(s['vs_edu_domain']['added'])}건 추가, 오분류 {len(s['vs_edu_domain']['removed'])}건 제외**")
L.append(f"- 예산 수치 보정 4건 반영 (파싱 오류 확인 건, 3절 참조)")
L.append("")
L.append("## 2. 부처별 현황 (2026 확정예산 기준)")
L.append("")
L.append("| 부처 | 사업 수 | 2026 예산 |")
L.append("|---|---:|---:|")
for k, v in tf["by_department"].items():
    L.append(f"| {k} | {v['count']} | {fmt(v['b2026'])} |")
L.append("")
L.append(f"## 3. 인재양성 주목적 사업 목록 (core, {len(core)}건)")
L.append("")
L.append("| id | 부처 | 사업명 | 2024 | 2025 | 2026 | 비고 |")
L.append("|---:|---|---|---:|---:|---:|---|")
for t in core:
    L.append(row(t))
L.append("")
L.append("예산보정 상세 (v1.1 확정값 적용 건):")
for t in tf["projects"]:
    if t.get("corrected"):
        L.append(f"- id {t['id']} ({t['department']} {t['project_name']}): {t.get('correction_note') or ''}")
L.append("")
L.append(f"## 4. 인재양성 일부 포함 사업 (partial, {len(part)}건)")
L.append("")
L.append("사업의 주목적은 다른 분야이나 PDF 원문상 인재양성·교육훈련 활동(내역)을 포함하는 사업.")
L.append("")
L.append("| id | 부처 | 사업명 | 2026 | 인재양성 요소 |")
L.append("|---:|---|---|---:|---|")
for t in part:
    note = (t.get("talent_note") or "").replace("|", "/")[:70]
    L.append(f"| {t['id']} | {t['department']} | {t['project_name']} | {fmt(t['b2026'])} | {note} |")
L.append("")
L.append("## 5. 중복·유사 의심 그룹 (인재양성 사업 2건 이상 포함)")
L.append("")
L.append("원 데이터의 유사도 분석(중복 의심 102그룹) 중 인재양성 사업이 2건 이상 걸린 그룹. 부처 간 유사 사업 분산 편성 여부 검토 대상.")
L.append("")
L.append("| 그룹 | 관련 인재양성 사업 |")
L.append("|---|---|")
for g in tf["duplicate_groups"]:
    names = "; ".join(f"{pname[i][0]} {pname[i][1]}(id{i})" for i in g["talent_ids"])
    L.append(f"| {len(g['all_ids'])}개 사업 그룹 | {names} |")
L.append("")
L.append("## 6. 데이터 출처 구분 (메일 5번 관점)")
L.append("")
L.append("| 구분 | 해당 자료 | 비고 |")
L.append("|---|---|---|")
L.append("| **가공데이터** | 본 현황표 및 KAIB2026 파싱 데이터(budget_db.json 등) | dBrain 원천 → 국회제출 PDF → 파싱. 전수 검증 완료, 한계는 검증보고서 참조 |")
L.append("| **행정데이터(원천)** | dBrain(예산), NTIS(R&D 과제·성과), e-나라도움(보조금), 고용보험DB(내일배움카드 등 훈련 실적) | 기계판독 형태 미공개가 근본 제약 |")
L.append("| **조사데이터** | 부처별 인력수급 전망조사(예: SW인력실태조사, 산업기술인력수급실태조사) | 본 데이터셋 범위 밖 — 인재지도 구축 시 별도 수집 필요 |")
L.append("")
L.append("## 7. 활용 유의사항")
L.append("")
L.append("1. 본 목록은 **'2026년 AI 재정사업'(533건) 범위 내** 인재양성 사업이다. AI 외 첨단분야(바이오·반도체 등) 인재양성 사업 중 AI 사업으로 분류되지 않은 것은 포함되지 않는다.")
L.append("2. partial 사업의 2026 예산은 **사업 전체 예산**이며 인재양성 내역만의 예산이 아니다. 내역 단위 분리는 내역사업 데이터 정밀화(v1.1) 과제.")
L.append("3. 검증에서 원 데이터의 체계적 파싱 오류(6열 시프트 등)가 확인되었으므로, 본 현황표 외 원 데이터를 직접 인용할 때는 `Reports\\분류체계_정합성_검증보고서_26.07.28.md`의 오류 목록을 먼저 확인할 것.")
L.append("")

out = BASE / "Reports" / "AI분야_인재양성_예산현황_26.07.28.md"
out.write_text("\n".join(L), encoding="utf-8")
print("보고서 생성:", out, f"({out.stat().st_size/1024:.0f}KB, core {len(core)} / partial {len(part)})")
