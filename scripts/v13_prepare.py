# -*- coding: utf-8 -*-
"""v1.3: 중복성 검토 대상 그룹 작업 파일 생성
- talent_final의 중복·유사 그룹 13개, 그룹별 구성 사업(비인재양성 포함 전체) 정보
- 출력: analysis/v13_jobs/group_XX.json
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(r"D:\AI_Work\Claude\Hi-Tech_Training_Budget")
JOBS = BASE / "analysis" / "v13_jobs"
JOBS.mkdir(exist_ok=True)

tf = json.load(open(BASE / "analysis" / "talent_final.json", encoding="utf-8"))
db = json.load(open(BASE / "KAIB2026" / "data" / "budget_db.json", encoding="utf-8"))
idx = json.load(open(BASE / "analysis" / "batches" / "index.json", encoding="utf-8"))
FIX = {int(k): v for k, v in json.load(open(BASE / "analysis" / "budget_corrections_v11.json",
                                            encoding="utf-8"))["corrections"].items()}
proj = {p["id"]: p for p in db["projects"]}
talent_ids = {t["id"] for t in tf["projects"]}


def b26_of(pid):
    if pid in FIX:
        return FIX[pid]["b2026_budget"]
    v = (proj[pid].get("budget") or {}).get("2026_budget")
    return v if isinstance(v, (int, float)) else 0


groups = tf["duplicate_groups"]
for i, g in enumerate(groups, 1):
    members = []
    for pid in g["all_ids"]:
        if pid not in proj:
            continue
        p = proj[pid]
        members.append({
            "id": pid, "department": p["department"], "project_name": p["project_name"],
            "b2026": b26_of(pid), "is_talent": pid in talent_ids,
            "purpose": (p.get("purpose") or "")[:400],
            "pjson": str(BASE / "analysis" / "pjson" / f"{pid}.json"),
            "extracted": idx[str(pid)]["extracted"],
        })
    out = {"group_id": i, "member_count": len(members), "members": members}
    (JOBS / f"group_{i:02d}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"그룹 {i:2d}: {len(members)}개 사업 | " +
          ", ".join(f"{m['department']}·{m['project_name'][:14]}" for m in members[:4]) +
          (" ..." if len(members) > 4 else ""))
print(f"\n총 {len(groups)}개 그룹, {sum(len(json.load(open(JOBS / f'group_{i:02d}.json', encoding='utf-8'))['members']) for i in range(1, len(groups)+1))}개 사업")
