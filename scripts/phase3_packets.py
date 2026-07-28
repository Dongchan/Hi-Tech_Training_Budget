# -*- coding: utf-8 -*-
"""Phase 3: 에이전트 검증 패킷 생성
- 배치당 ~40건 × 14개: analysis/batches/batch_NN.md
- 각 사업: JSON 요약(예산·분류) + PDF 원문 첫 3페이지(최대 5,000자)
- index.json: id → 사업명/추출파일/배치 매핑
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(r"D:\AI_Work\Claude\Hi-Tech_Training_Budget")
BATCH_DIR = BASE / "analysis" / "batches"
BATCH_DIR.mkdir(exist_ok=True)

db = json.load(open(BASE / "KAIB2026" / "data" / "budget_db.json", encoding="utf-8"))
toc = {t["id"]: t for t in json.load(open(BASE / "KAIB2026" / "data" / "toc_mapping.json", encoding="utf-8"))}
projects = sorted(db["projects"], key=lambda p: p["id"])

extracted = {}
for fp in (BASE / "extracted").glob("*.txt"):
    pid = int(fp.name.split("_")[0])
    extracted[pid] = fp

PAGE_RE = re.compile(r"\[PAGE (\d+)\]\n")


def first_pages(pid, n=3, cap=5000):
    """추출 파일에서 toc 시작 페이지부터 n페이지 텍스트"""
    t = toc[pid]
    ps = t["page_start"]
    text = extracted[pid].read_text(encoding="utf-8")
    parts = PAGE_RE.split(text)
    # parts: [header, num, body, num, body, ...]
    pages = {}
    for i in range(1, len(parts) - 1, 2):
        pages[int(parts[i])] = parts[i + 1]
    out = "".join(pages.get(p, "") for p in range(ps, min(ps + n, t["page_end"] + 1)))
    if len(out) > cap:
        out = out[:cap] + "\n…(이하 생략)"
    return out


def summarize(p):
    return {
        "id": p["id"], "name": p["name"], "code": p.get("code"),
        "department": p["department"], "project_name": p["project_name"],
        "budget(백만원)": p.get("budget"),
        "project_period": (p.get("project_period") or {}).get("raw"),
        "total_cost": (p.get("total_cost") or {}).get("raw"),
        "sub_projects": [{"name": s.get("name"), "b2024": s.get("budget_2024"),
                          "b2025": s.get("budget_2025"), "b2026": s.get("budget_2026")}
                         for s in (p.get("sub_projects") or [])],
        "is_rnd": p.get("is_rnd"), "rnd_stage": p.get("rnd_stage"),
        "ai_domains": p.get("ai_domains"), "ai_tech": p.get("ai_tech"),
        "keywords": p.get("keywords"),
    }


BATCH = 40
index = {}
batches = [projects[i:i + BATCH] for i in range(0, len(projects), BATCH)]
for bi, batch in enumerate(batches, 1):
    lines = []
    for p in batch:
        pid = p["id"]
        t = toc[pid]
        lines.append(f"=== PROJECT id={pid} | {p['name']} | PDF p{t['page_start']}-{t['page_end']} ===")
        lines.append("[JSON 데이터]")
        lines.append(json.dumps(summarize(p), ensure_ascii=False, indent=1))
        lines.append(f"[PDF 원문 (p{t['page_start']}~ 최대 3페이지)]")
        lines.append(first_pages(pid))
        lines.append("")
        index[pid] = {"name": p["name"], "batch": bi,
                      "packet": str(BATCH_DIR / f"batch_{bi:02d}.md"),
                      "extracted": str(extracted[pid])}
    fp = BATCH_DIR / f"batch_{bi:02d}.md"
    fp.write_text("\n".join(lines), encoding="utf-8")
    print(f"batch_{bi:02d}.md: {len(batch)}건, {fp.stat().st_size/1024:.0f}KB")

with open(BATCH_DIR / "index.json", "w", encoding="utf-8") as f:
    json.dump(index, f, ensure_ascii=False, indent=1)
print("총", len(batches), "배치 /", len(index), "사업")
