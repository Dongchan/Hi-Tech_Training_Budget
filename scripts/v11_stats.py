# -*- coding: utf-8 -*-
"""v1.1 갱신 통계 출력 (보고서·README용)"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
js = open(r"D:\AI_Work\Claude\Hi-Tech_Training_Budget\Dash_board\data\data.js", encoding="utf-8").read()
d = json.loads(js[js.index("{"):js.rindex(";")])
a = d["ai_relevance"]
t = d["totals"]["b2026"]
print("2026 총계:", f"{t:,.0f}", f"= {t/1e6:.2f}조")
for k in ["core", "partial", "none"]:
    print(f"  {k}: {a['count'][k]}건 {a['sum'][k]:,.0f} ({a['sum'][k]/t*100:.1f}%)")
print("교육/인재 by_domain:", [x for x in d["by_domain"] if x["domain"] == "교육/인재"])
print("top domains:", [(x["domain"], x["count"]) for x in d["by_domain"][:6]])
