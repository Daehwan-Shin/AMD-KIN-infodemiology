# -*- coding: utf-8 -*-
"""corpus 1,989 재구성 + 모든 downstream 통계 재집계.

corpus 1,989 = tri (1,836) + v5b R1 (153) [P2-0969 제외, 새 케이스 1개도 drop]

이 스크립트:
1. corpus IDs 확정
2. topic FINAL 에서 labels 가져옴
3. Topic distribution (primary, any-mention)
4. Temporal trends (4 periods)
5. Drug recognition, modality, etc.
6. Save updated corpus jsonl
"""
import json, sys, re
sys.stdout.reconfigure(encoding='utf-8')
from collections import Counter, defaultdict

# === load topic FINAL (2,048) ===
with open('_stage4_topic_FINAL_v2.jsonl', encoding='utf-8') as f:
    topic_corpus = [json.loads(l) for l in f if l.strip()]
topic_by_id = {(r.get('phase2_id') or r.get('phase1_id')): r for r in topic_corpus}
tri_ids = {(r.get('phase2_id') or r.get('phase1_id'))
           for r in topic_corpus if r.get('source') == 'tri_consensus'}
v1_R1_ids = {(r.get('phase2_id') or r.get('phase1_id'))
             for r in topic_corpus if r.get('source') == 'review_resolved'}

# === v5b R1 ===
with open('_R1_v5b_predictions_648.jsonl', encoding='utf-8') as f:
    v5b = {json.loads(l)['id']: json.loads(l)['v5b'] for l in f if l.strip()}
v5b_R1 = {rid for rid, lbl in v5b.items() if lbl == 'R1'}

# === final corpus = tri ∪ (v5b R1 ∩ v1 R1) ∪ {} ===
# (P2-0969 는 v5b R1 이지만 v1 R1 아니라 topic 라벨 없음 → drop)
kept_review = v5b_R1 & v1_R1_ids  # 153
final_ids = tri_ids | kept_review
dropped_from_v1 = v1_R1_ids - v5b_R1  # 59

print(f'=== Corpus 1,989 구성 ===')
print(f'  tri_consensus:   {len(tri_ids)}')
print(f'  v5b R1 (kept):   {len(kept_review)}')
print(f'  drop from v1 R1: {len(dropped_from_v1)}')
print(f'  Total:           {len(final_ids)}')

# === build final corpus rows ===
final_corpus = [topic_by_id[rid] for rid in final_ids if rid in topic_by_id]
print(f'  rows in topic FINAL: {len(final_corpus)}')

# update source field for kept review
for r in final_corpus:
    rid = r.get('phase2_id') or r.get('phase1_id')
    if rid in kept_review:
        r['source'] = 'review_resolved_v5b'

# save
with open('_stage4_topic_FINAL_v3_1989.jsonl', 'w', encoding='utf-8') as f:
    for r in final_corpus:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')
print(f'\n→ _stage4_topic_FINAL_v3_1989.jsonl ({len(final_corpus)} rows)')

# === statistics ===
CLASSES = ['C1','C2','C3','C4','C5','C6','C7','C8','C9']
NAMES = {'C1':'Disease info','C2':'Symptoms/Dx','C3':'Tx/surgery','C4':'Anti-VEGF',
         'C5':'Nutrition/Lifestyle','C6':'Course/Prognosis','C7':'Cost/Insurance',
         'C8':'Hospital/MD','C9':'Other'}

def get_topics(r):
    p = r.get('final_primary') or r.get('primary_topic') or ''
    s = r.get('final_secondary') or r.get('secondary_topics') or []
    if isinstance(s, str):
        s = [x.strip() for x in s.split(',') if x.strip()]
    return p, s

def primary_dist(corpus):
    c = Counter(get_topics(r)[0] for r in corpus)
    return {k: 100 * c.get(k, 0) / len(corpus) for k in CLASSES}, c

def anymention_dist(corpus):
    c = Counter()
    total_mentions = 0
    for r in corpus:
        p, s = get_topics(r)
        topics = set([p] + list(s)) - {''}
        for t in topics:
            c[t] += 1
        total_mentions += len(topics)
    return {k: 100 * c.get(k, 0) / len(corpus) for k in CLASSES}, c, total_mentions

def period_of(date):
    try:
        y = int((date or '').split('.')[0])
    except: return None
    if y < 2010: return '~2009'
    if y < 2015: return '2010–14'
    if y < 2020: return '2015–19'
    return '2020–'

# Primary
print(f'\n=== Primary topic distribution (n={len(final_corpus)}) ===')
pd_full, pd_count = primary_dist(final_corpus)
print(f'{"":<6} {"NAME":<22} {"%":>7} {"n":>6}')
for k in CLASSES:
    print(f'  {k:<4} {NAMES[k]:<22} {pd_full[k]:>6.1f} {pd_count[k]:>5}')

# Any-mention
print(f'\n=== Any-mention distribution ===')
am_full, am_count, total_men = anymention_dist(final_corpus)
mean_topics = total_men / len(final_corpus)
print(f'(mean {mean_topics:.2f} topics/thread)')
print(f'{"":<6} {"NAME":<22} {"%":>7} {"n":>6}')
for k in CLASSES:
    print(f'  {k:<4} {NAMES[k]:<22} {am_full[k]:>6.1f} {am_count[k]:>5}')

# Temporal (any-mention)
print(f'\n=== Temporal any-mention (%) ===')
periods = ['~2009', '2010–14', '2015–19', '2020–']
by_period = defaultdict(list)
for r in final_corpus:
    p = period_of(r.get('question_date',''))
    if p: by_period[p].append(r)
print(f'\n  period    n      ' + ' '.join(f'{k:>5}' for k in CLASSES))
for period in periods:
    sub = by_period[period]
    if not sub: continue
    d, _, _ = anymention_dist(sub)
    row = f'  {period:<10}{len(sub):>4}    ' + ' '.join(f'{d[k]:>5.1f}' for k in CLASSES)
    print(row)

# Year counts (figS1)
print(f'\n=== Yearly counts ===')
year_counts = Counter()
for r in final_corpus:
    try:
        y = int((r.get('question_date','') or '').split('.')[0])
        year_counts[y] += 1
    except: pass
for y in sorted(year_counts):
    print(f'  {y}: {year_counts[y]}')

# Modality counts (fig2b)
print(f'\n=== Modality mentions (fig2b) ===')
modality_keywords = {
    'Anti-VEGF intravitreal': ['항VEGF', '아바스틴', '루센티스', '아일리아', '바비스모', '비오뷰',
                                'Avastin', 'Lucentis', 'Eylea', 'Vabysmo', 'Beovu',
                                '안구주사', '유리체내', 'IVI', '주사치료'],
    'Surgery': ['수술', '시술', 'surgery'],
    'Laser': ['레이저', 'laser'],
    'PDT': ['광역학', 'PDT', 'photodynamic'],
    'Injection (unspecified)': ['주사'],
    'Oral medication': ['약', '먹는'],
}
modality_count = Counter()
for r in final_corpus:
    text = ' '.join([r.get('question_title',''), r.get('question_content','')])
    for mod, kws in modality_keywords.items():
        if any(kw in text for kw in kws):
            modality_count[mod] += 1
print(f'{"Modality":<32} {"n":>6} {"%":>7}')
for mod in ['Anti-VEGF intravitreal', 'Surgery', 'Laser', 'PDT', 'Injection (unspecified)', 'Oral medication']:
    n = modality_count.get(mod, 0)
    print(f'  {mod:<30} {n:>5} {100*n/len(final_corpus):>6.1f}')

# Drug recognition (fig2a) - basic version
print(f'\n=== Drug recognition (fig2a, question-side only — body) ===')
drugs = {
    'Ranibizumab (Lucentis)': ['루센티스', 'Lucentis', 'ranibizumab'],
    'Bevacizumab (Avastin)':  ['아바스틴', 'Avastin', 'bevacizumab'],
    'Aflibercept (Eylea)':    ['아일리아', 'Eylea', 'aflibercept'],
    'Brolucizumab (Beovu)':   ['비오뷰', 'Beovu', 'brolucizumab'],
    'Faricimab (Vabysmo)':    ['바비스모', 'Vabysmo', 'faricimab'],
    'Pegaptanib (Macugen)':   ['마쿠젠', 'Macugen', 'pegaptanib'],
}
drug_count = Counter()
for r in final_corpus:
    body = r.get('question_content','') or ''
    for drug, kws in drugs.items():
        if any(kw in body for kw in kws):
            drug_count[drug] += 1
print(f'{"Drug":<32} {"n":>6}')
for drug in drugs:
    print(f'  {drug:<30} {drug_count.get(drug,0):>5}')
