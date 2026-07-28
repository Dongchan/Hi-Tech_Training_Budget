# -*- coding: utf-8 -*-
"""v1.1: 에이전트 배치 작업 파일 생성
- 예산 보정 49건 → 10건씩 5개 청크 (analysis/v11_jobs/budget_XX.json)
- 재분류 195건 → 15건씩 13개 청크 (analysis/v11_jobs/reclass_XX.json)
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(r"D:\AI_Work\Claude\Hi-Tech_Training_Budget")
JOBS = BASE / "analysis" / "v11_jobs"
JOBS.mkdir(exist_ok=True)

vr = json.load(open(BASE / "analysis" / "verification_results.json", encoding="utf-8"))
idx = json.load(open(BASE / "analysis" / "batches" / "index.json", encoding="utf-8"))
db = json.load(open(BASE / "KAIB2026" / "data" / "budget_db.json", encoding="utf-8"))
pname = {p["id"]: p["project_name"] for p in db["projects"]}

budget_jobs, reclass_jobs = [], []
for r in vr["results"]:
    pid = r["id"]
    e = idx[str(pid)]
    if r["budget_verdict"] == "mismatch":
        budget_jobs.append({
            "id": pid, "name": f'{e["name"]}',
            "prior_detail": r.get("budget_detail", ""),
            "pjson": str(BASE / "analysis" / "pjson" / f"{pid}.json"),
            "extracted": e["extracted"],
        })
    if r["classification_verdict"] in ("partial", "wrong"):
        reclass_jobs.append({
            "id": pid, "name": pname[pid],
            "prior_detail": r.get("classification_detail", ""),
            "current_domains": next(p.get("ai_domains") for p in db["projects"] if p["id"] == pid),
            "pjson": str(BASE / "analysis" / "pjson" / f"{pid}.json"),
            "extracted": e["extracted"],
        })


def chunks(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]


bch = chunks(budget_jobs, 10)
rch = chunks(reclass_jobs, 15)
for i, c in enumerate(bch, 1):
    (JOBS / f"budget_{i:02d}.json").write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
for i, c in enumerate(rch, 1):
    (JOBS / f"reclass_{i:02d}.json").write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"budget: {len(budget_jobs)}건 → {len(bch)}청크 / reclass: {len(reclass_jobs)}건 → {len(rch)}청크")
