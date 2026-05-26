# -*- coding: utf-8 -*-
"""topic validation 100 재집계 (97 기존 + 3 replacement)."""
import json, sys, re
sys.stdout.reconfigure(encoding='utf-8')
import openpyxl
from collections import Counter
from sklearn.metrics import cohen_kappa_score

# === drop 된 케이스 (v5b 에서 strict_AMD 아닌 것) ===
DROPPED = {'P2-2516', 'P2-2195', 'P2-3098'}

# === load 원래 100 ===
def load_review(p):
    wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
    ws = wb['review']
    headers = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
    rows = {}
    for r in ws.iter_rows(min_row=2, values_only=True):
        no, rid = r[0], r[1]
        primary = r[4]  # 'human_primary' or 'primary'
        rows[rid] = (no, (primary or '').strip())
    wb.close(); return rows
sdh_old = load_review('AMD_topic_human_validation_100_SDH.xlsx')
nkt_old = load_review('AMD_topic_human_validation_100_NKT_1.xlsx')
print(f'SDH old: {len(sdh_old)}, NKT old: {len(nkt_old)}')

# === load 3 replacements ===
sdh_rep = load_review('수정용자료/AMD_topic_replacement_3_SDH_done.xlsx')
nkt_rep = load_review('수정용자료/AMD_topic_replacement_3_NKT_NKTdone.xlsx')
print(f'SDH replacement: {sdh_rep}')
print(f'NKT replacement: {nkt_rep}')

# === build new 100 ===
new_sdh = {rid: (no, lbl) for rid, (no, lbl) in sdh_old.items() if rid not in DROPPED}
new_nkt = {rid: (no, lbl) for rid, (no, lbl) in nkt_old.items() if rid not in DROPPED}
for rid, (no, lbl) in sdh_rep.items():
    new_sdh[rid] = (no, lbl)
for rid, (no, lbl) in nkt_rep.items():
    new_nkt[rid] = (no, lbl)
print(f'\nNew 100: SDH {len(new_sdh)}, NKT {len(new_nkt)}')

# === load LLM topic labels for these IDs ===
with open('_stage4_topic_FINAL_v2.jsonl', encoding='utf-8') as f:
    topic_data = {(r.get('phase2_id') or r.get('phase1_id')): r
                  for r in [json.loads(l) for l in f if l.strip()]}

# === compare ===
CLASSES = ['C1','C2','C3','C4','C5','C6','C7','C8','C9']

# Build comparison
pairs_sdh_llm = []
pairs_nkt_llm = []
pairs_sdh_nkt = []
for rid in new_sdh:
    sdh_lbl = new_sdh[rid][1]
    nkt_lbl = new_nkt.get(rid, ('','' ))[1]
    llm = topic_data.get(rid, {})
    llm_primary = (llm.get('final_primary') or llm.get('primary_topic') or '').strip()
    if sdh_lbl in CLASSES and llm_primary in CLASSES:
        pairs_sdh_llm.append((sdh_lbl, llm_primary))
    if nkt_lbl in CLASSES and llm_primary in CLASSES:
        pairs_nkt_llm.append((nkt_lbl, llm_primary))
    if sdh_lbl in CLASSES and nkt_lbl in CLASSES:
        pairs_sdh_nkt.append((sdh_lbl, nkt_lbl))

print(f'\n=== Topic validation κ ===')
def kappa(pairs, name):
    if not pairs:
        print(f'  {name}: no valid pairs'); return
    y1, y2 = zip(*pairs)
    yt = [CLASSES.index(x) for x in y1]
    yp = [CLASSES.index(x) for x in y2]
    raw = sum(1 for a,b in zip(yt,yp) if a==b)/len(yt)
    k = cohen_kappa_score(yt, yp)
    print(f'  {name}  n={len(pairs)}  κ={k:.3f}  raw={raw*100:.1f}%')

kappa(pairs_sdh_llm, 'SDH vs LLM (primary)')
kappa(pairs_nkt_llm, 'NKT vs LLM (primary)')
kappa(pairs_sdh_nkt, 'Inter-expert (SDH vs NKT, primary)')

# Gold subset
print(f'\n=== Gold-subset (SDH ∩ NKT primary 일치) ===')
gold_pairs = []
for rid in new_sdh:
    sdh_lbl = new_sdh[rid][1]
    nkt_lbl = new_nkt.get(rid, ('',''))[1]
    if sdh_lbl == nkt_lbl and sdh_lbl in CLASSES:
        llm = topic_data.get(rid, {})
        llm_p = (llm.get('final_primary') or '').strip()
        gold_pairs.append((sdh_lbl, llm_p))
gold_match = sum(1 for s, l in gold_pairs if s == l)
print(f'  gold n={len(gold_pairs)}, LLM match={gold_match}/{len(gold_pairs)} = {100*gold_match/len(gold_pairs):.1f}%')

# 비교: 이전 결과
print(f'\n=== 이전 paper 결과 (참고) ===')
print(f'  SDH κ=0.906 (raw 92.0%) — 100 sample')
print(f'  NKT κ=0.825 (raw 85.0%) — 100 sample')
print(f'  inter-expert κ=0.778 (raw 81.0%) — 100 sample')
print(f'  gold-subset (SDH∩NKT) overlap with LLM = 84/85 (98.8%)')
