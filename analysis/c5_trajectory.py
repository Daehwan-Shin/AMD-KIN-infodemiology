# -*- coding: utf-8 -*-
"""Legacy mention-share calculation; not used for manuscript any-mention results.

The denominator here is the total number of topic mentions, not threads. Use
`reproduce_public_results.py` or `temporal_trends.py` for the manuscript-defined
thread-level any-mention rate.
"""
import json, sys, re
sys.stdout.reconfigure(encoding='utf-8')
from collections import Counter

print('WARNING: legacy mention-share denominator; not used in the manuscript.')

with open('_stage4_topic_FINAL_v3_1989.jsonl', encoding='utf-8') as f:
    corpus = [json.loads(l) for l in f if l.strip()]

def period_of(date):
    try: y = int((date or '').split('.')[0])
    except: return None
    if y < 2010: return '~2009'
    if y < 2015: return '2010–14'
    if y < 2020: return '2015–19'
    return '2020–'

CLASSES = ['C1','C2','C3','C4','C5','C6','C7','C8','C9']

def topics(r):
    p = r.get('final_primary','')
    s = r.get('final_secondary') or []
    if isinstance(s, str): s = [x.strip() for x in s.split(',') if x.strip()]
    return list(set([p] + list(s)) - {''})

# 기간별 total mentions
from collections import defaultdict
periods = ['~2009', '2010–14', '2015–19', '2020–']
period_threads = defaultdict(list)
for r in corpus:
    p = period_of(r.get('question_date',''))
    if p: period_threads[p].append(r)

print(f'\n=== Mention share by period (fig1e style: denominator = total mentions in period) ===')
print(f'{"period":<10} {"threads":>8} {"mentions":>9}  ' + ' '.join(f'{k:>6}' for k in CLASSES))
for period in periods:
    rows = period_threads[period]
    counts = Counter()
    total = 0
    for r in rows:
        ts = topics(r)
        for t in ts: counts[t] += 1
        total += len(ts)
    if total == 0: continue
    line = f'{period:<10} {len(rows):>8} {total:>9}  '
    for k in CLASSES:
        share = 100 * counts.get(k, 0) / total
        line += f'{share:>5.1f}%'
    print(line)

# C5 trajectory specifically
print(f'\n=== C5 trajectory (fig1e mention-share) ===')
for period in periods:
    rows = period_threads[period]
    counts = Counter()
    total = 0
    for r in rows:
        ts = topics(r)
        for t in ts: counts[t] += 1
        total += len(ts)
    c5_share = 100 * counts.get('C5', 0) / total if total else 0
    print(f'  {period}: {c5_share:.1f}% (C5 mentions {counts.get("C5",0)} / total {total})')
