# -*- coding: utf-8 -*-
"""Phase 3: 사업별 JSON 요약 파일 생성 (2차 재검용)"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8")
from phase3_packets import summarize, projects  # noqa: E402

OUT = Path(r"D:\AI_Work\Claude\Hi-Tech_Training_Budget\analysis\pjson")
OUT.mkdir(exist_ok=True)
for p in projects:
    fp = OUT / f"{p['id']}.json"
    fp.write_text(json.dumps(summarize(p), ensure_ascii=False, indent=1), encoding="utf-8")
print("pjson", len(list(OUT.glob("*.json"))), "files")
