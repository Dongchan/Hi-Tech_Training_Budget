# -*- coding: utf-8 -*-
"""Phase 2-A/E: 페이지 매핑 전수 검증 + 사업별 PDF 텍스트 추출 (UTF-8)
- A: toc_mapping의 페이지 범위(오프셋 0 확인됨)에 사업명·부처명 실재 확인
- E: 사업별 텍스트를 extracted/{id:03d}_{사업명}.txt 로 저장 (앞뒤 1페이지 여유 포함)
출력: analysis/page_mapping_results.json
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(r"D:\AI_Work\Claude\Hi-Tech_Training_Budget")
PDF = BASE / "Original_data" / "AI_예산사업_통합_설명자료.pdf"
OUT_DIR = BASE / "extracted"
OUT_DIR.mkdir(exist_ok=True)

SIMILAR = {"\u318d": "\u00b7", "\u2024": ".", "\u2027": "\u00b7", "\uff0d": "-", "\u2013": "-", "\u2014": "-",
           "\u25b3": "-", "\u25b5": "-", "\uff08": "(", "\uff09": ")"}


def norm(s):
    if not s:
        return ""
    s = unicodedata.normalize("NFC", s)
    for a, b in SIMILAR.items():
        s = s.replace(a, b)
    return re.sub(r"\s+", "", s)


def probe_key(name):
    """사업명에서 검색용 키 추출: 잘림(…) 앞부분, 공백 제거, 최대 8자"""
    n = norm(name)
    n = n.split("…")[0]
    return n[:8] if len(n) >= 4 else n


doc = fitz.open(PDF)
toc = json.load(open(BASE / "KAIB2026" / "data" / "toc_mapping.json", encoding="utf-8"))

results = []
not_found_name, not_found_dept = [], []

# 페이지 커버리지 검사용
covered = set()

for t in toc:
    pid, ps, pe = t["id"], t["page_start"], t["page_end"]
    dept, pname = t["department"], t["project_name"]
    covered.update(range(ps, pe + 1))

    core_text = "".join(doc[i].get_text() for i in range(ps - 1, min(pe, doc.page_count)))
    core_norm = norm(core_text)

    name_ok = probe_key(pname) in core_norm
    dept_ok = norm(dept) in core_norm

    if not name_ok:
        not_found_name.append({"id": pid, "name": t["full_name"], "pages": [ps, pe]})
    if not dept_ok:
        not_found_dept.append({"id": pid, "name": t["full_name"], "pages": [ps, pe]})

    # E: 추출 저장 (앞뒤 1페이지 여유)
    lo, hi = max(1, ps - 1), min(doc.page_count, pe + 1)
    full_text = "\n".join(f"[PAGE {i+1}]\n{doc[i].get_text()}" for i in range(lo - 1, hi))
    safe = re.sub(r'[\\/:*?"<>|]|[\x00-\x1f]', "_", pname)[:60]
    fp = OUT_DIR / f"{pid:03d}_{safe}.txt"
    with open(fp, "w", encoding="utf-8") as f:
        f.write(f"# id={pid} | {t['full_name']} | toc pages {ps}-{pe} (margin ±1)\n\n{full_text}")

    results.append({"id": pid, "name_found": name_ok, "dept_found": dept_ok, "pages": [ps, pe]})

# 페이지 갭/중복 검사 (본문 영역)
all_pages = set(range(min(covered), max(covered) + 1))
gaps = sorted(all_pages - covered)
overlaps = []
prev = None
for t in sorted(toc, key=lambda x: x["page_start"]):
    if prev and t["page_start"] < prev["page_end"]:
        overlaps.append({"a": prev["id"], "b": t["id"], "pages": [t["page_start"], prev["page_end"]]})
    prev = t

summary = {
    "total": len(toc),
    "name_found": len(toc) - len(not_found_name),
    "name_not_found": not_found_name,
    "dept_not_found": not_found_dept,
    "coverage": {"first": min(covered), "last": max(covered), "pdf_pages": doc.page_count,
                 "gap_pages": gaps, "overlap_ranges": overlaps},
}
with open(BASE / "analysis" / "page_mapping_results.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(f"전체 {len(toc)}건 | 사업명 확인 {summary['name_found']}건 | 미확인 {len(not_found_name)}건")
for x in not_found_name[:10]:
    print("  미확인:", x)
print(f"부처명 미확인: {len(not_found_dept)}건")
print(f"커버리지: p{min(covered)}~p{max(covered)} (PDF {doc.page_count}p) | 갭 {len(gaps)}p | 중첩 {len(overlaps)}건")
print("추출 파일:", len(list(OUT_DIR.glob('*.txt'))), "개 →", OUT_DIR)
