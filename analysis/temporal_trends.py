# -*- coding: utf-8 -*-
"""corpus 1,989 의 primary-only temporal trend 재계산."""
import json, sys, re
sys.stdout.reconfigure(encoding='utf-8')
from collections import Counter, defaultdict

with open('_stage4_topic_FINAL_v3_1989.jsonl', encoding='utf-8') as f:
    corpus = [json.loads(l) for l in f if l.strip()]

CLASSES = ['C1','C2','C3','C4','C5','C6','C7','C8','C9']

def period_of(date):
    try: y = int((date or '').split('.')[0])
    except: return None
    if y < 2010: return '~2009'
    if y < 2015: return '2010–14'
    if y < 2020: return '2015–19'
    return '2020–'

by_period = defaultdict(list)
for r in corpus:
    p = period_of(r.get('question_date',''))
    if p: by_period[p].append(r)

print(f'\n=== Primary topic per-period rates ===')
print(f'{"period":<10} {"n":>5}  ' + ' '.join(f'{k:>6}' for k in CLASSES))
periods = ['~2009', '2010–14', '2015–19', '2020–']
for period in periods:
    sub = by_period[period]
    pri_count = Counter(r.get('final_primary','') for r in sub)
    rates = {k: 100 * pri_count.get(k, 0) / len(sub) for k in CLASSES}
    line = f'{period:<10} {len(sub):>5}  ' + ' '.join(f'{rates[k]:>5.1f}%' for k in CLASSES)
    print(line)

print(f'\n=== Any-mention per-period rates ===')
print(f'{"period":<10} {"n":>5}  ' + ' '.join(f'{k:>6}' for k in CLASSES))
for period in periods:
    sub = by_period[period]
    c = Counter()
    for r in sub:
        p = r.get('final_primary','')
        s = r.get('final_secondary') or []
        if isinstance(s, str): s = [x.strip() for x in s.split(',') if x.strip()]
        topics = set([p] + list(s)) - {''}
        for t in topics: c[t] += 1
    rates = {k: 100 * c.get(k, 0) / len(sub) for k in CLASSES}
    line = f'{period:<10} {len(sub):>5}  ' + ' '.join(f'{rates[k]:>5.1f}%' for k in CLASSES)
    print(line)

# 첫·마지막 비교 (manuscript 의 X→Y 형식)
print(f'\n=== Primary: first vs last period ===')
first = by_period['~2009']
last = by_period['2020–']
fc = Counter(r.get('final_primary','') for r in first)
lc = Counter(r.get('final_primary','') for r in last)
for k in CLASSES:
    fr = 100*fc.get(k,0)/len(first)
    lr = 100*lc.get(k,0)/len(last)
    print(f'  {k}: {fr:.1f}% → {lr:.1f}%  (Δ {lr-fr:+.1f})')

# Any-mention: first vs last
print(f'\n=== Any-mention: first vs last ===')
def amx(rows):
    c = Counter()
    for r in rows:
        p = r.get('final_primary','')
        s = r.get('final_secondary') or []
        if isinstance(s, str): s = [x.strip() for x in s.split(',') if x.strip()]
        topics = set([p] + list(s)) - {''}
        for t in topics: c[t] += 1
    return c
fc = amx(first); lc = amx(last)
for k in CLASSES:
    fr = 100*fc.get(k,0)/len(first); lr = 100*lc.get(k,0)/len(last)
    print(f'  {k}: {fr:.1f}% → {lr:.1f}%  (Δ {lr-fr:+.1f})')

# C5 trajectory specifically (manuscript 의 fig1e style)
print(f'\n=== C5 (Nutrition/Lifestyle) trajectory (any-mention, all 4 periods) ===')
for period in periods:
    sub = by_period[period]
    c = amx(sub)
    rate = 100 * c.get('C5', 0) / len(sub)
    print(f'  {period}: {rate:.1f}% (n={c.get("C5",0)}/{len(sub)})')
