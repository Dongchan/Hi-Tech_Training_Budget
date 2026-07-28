# -*- coding: utf-8 -*-
"""Phase 3 종합: 1차(batch_*) + 2차(recheck_*) 판정 병합 → analysis/verification_results.json
- 재검된 id는 2차 판정을 최종으로 채택 (1차는 prior로 보존)
- 표본(why=sample) 1·2차 일치율로 1차 판정 무결성 측정
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(r"D:\AI_Work\Claude\Hi-Tech_Training_Budget")
VD = BASE / "analysis" / "verdicts"

# 소스: workflow journal (스키마 검증을 통과한 구조화 반환값 — 항상 유효한 JSON)
JOURNAL = Path(r"C:\Users\krivet\.claude\projects\D--AI-Work-Claude-Hi-Tech-Training-Budget"
               r"\c80bcfcf-6051-44f4-b439-b0c8f880d49f\subagents\workflows\wf_abdd5065-c67\journal.jsonl")
known_batches = [set(range(1 + 40 * k, min(534, 41 + 40 * k))) for k in range(14)]

first, second = {}, {}
n_verify = n_recheck = 0
for line in open(JOURNAL, encoding="utf-8"):
    d = json.loads(line)
    if d.get("type") != "result":
        continue
    res = (d.get("result") or {}).get("results")
    if not res:
        continue
    ids = {r["id"] for r in res}
    if ids in known_batches:
        n_verify += 1
        for r in res:
            first[r["id"]] = r
    else:
        n_recheck += 1
        for r in res:
            second[r["id"]] = r
print(f"journal: verify {n_verify}개 배치 / recheck {n_recheck}개 청크")

print(f"1차 {len(first)}건 / 2차 {len(second)}건")
missing = set(range(1, 534)) - set(first)
if missing:
    print("!! 1차 누락 id:", sorted(missing))

edu_ids = set(json.load(open(BASE / "analysis" / "talent_candidates.json", encoding="utf-8"))["by_tier"]["A"])

final = {}
for pid, r in first.items():
    f = dict(r)
    f["source"] = "first_pass"
    if pid in second:
        s = second[pid]
        f = dict(s)
        f["source"] = "rechecked"
        f["prior"] = {k: r.get(k) for k in ["budget_verdict", "classification_verdict", "ai_relevance", "talent_related"]}
    final[pid] = f

# 통계
stats = {}
for key in ["budget_verdict", "classification_verdict", "ai_relevance"]:
    stats[key] = dict(Counter(f[key] for f in final.values()))
stats["talent_related_true"] = sum(1 for f in final.values() if f["talent_related"])
stats["name_match_false"] = sum(1 for f in final.values() if not f.get("name_match", True))

# 표본 무결성: 재검 항목 중 1차와 2차 판정 비교 (전체 재검 건 기준)
agree = Counter()
for pid, s in second.items():
    p = final[pid].get("prior", {})
    for k in ["budget_verdict", "classification_verdict", "ai_relevance", "talent_related"]:
        agree[k, p.get(k) == s.get(k)] += 1
stats["recheck_agreement"] = {k: {"agree": agree[k, True], "disagree": agree[k, False]}
                              for k in ["budget_verdict", "classification_verdict", "ai_relevance", "talent_related"]}

# 인재양성 판정 변화
talent_final = {pid for pid, f in final.items() if f["talent_related"]}
stats["talent"] = {
    "final_count": len(talent_final),
    "added_vs_domain": sorted(talent_final - edu_ids),
    "removed_vs_domain": sorted(edu_ids - talent_final),
}

out = {"stats": stats, "results": [final[k] for k in sorted(final)]}
with open(BASE / "analysis" / "verification_results.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("\n== 최종 판정 통계 ==")
for k, v in stats.items():
    if k not in ("recheck_agreement", "talent"):
        print(f"  {k}: {v}")
print("  재검 일치율:", {k: v for k, v in stats["recheck_agreement"].items()})
print("  인재양성 최종:", stats["talent"]["final_count"], "건")
print("   + 도메인에 없던 추가:", stats["talent"]["added_vs_domain"])
print("   - 도메인인데 제외:", stats["talent"]["removed_vs_domain"])

print("\n== 최종 예산 불일치(mismatch) ==")
for pid, f in sorted(final.items()):
    if f["budget_verdict"] == "mismatch":
        print(f"  id {pid:3d} [{f['source'][:5]}] {f.get('budget_detail','')[:110]}")

print("\n== 분류 wrong ==")
for pid, f in sorted(final.items()):
    if f["classification_verdict"] == "wrong":
        print(f"  id {pid:3d} {f.get('classification_detail','')[:110]}")
