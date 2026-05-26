# -*- coding: utf-8 -*-
"""C9 subgroup analysis — corpus 1,989 기준."""
import json, re, sys, os
sys.stdout.reconfigure(encoding='utf-8')
from collections import Counter, defaultdict

with open('_stage4_topic_FINAL_v3_1989.jsonl', encoding='utf-8') as f:
    rows = [json.loads(l) for l in f if l.strip()]
def yr(r):
    m=re.match(r'(\d{4})', r.get('question_date','') or '')
    return int(m.group(1)) if m else None
rows=[r for r in rows if r.get('final_primary') and yr(r)]

c9_any = [r for r in rows if r['final_primary']=='C9' or 'C9' in (r.get('final_secondary') or [])]
c9_pri = [r for r in c9_any if r['final_primary']=='C9']
print(f'Corpus: {len(rows)}')
print(f'C9 (primary OR secondary): {len(c9_any)} ({len(c9_any)/len(rows)*100:.1f}%)')
print(f'C9 primary: {len(c9_pri)} ({len(c9_pri)/len(rows)*100:.1f}%)')

def text(r):
    q=(r.get('question_title','')+' '+r.get('question_content','')).lower()
    rs=' '.join(filter(None,[r.get('topic_reason',''), r.get('codex_reason',''),
                              r.get('opus_reason',''), r.get('gemini_reason','')])).lower()
    return q, rs

SUBS={
 'S1_post_injection_AE': [
    ('주사 후','주사후','주입 후','주입후','시술 후','시술후','주사를 맞','주사 맞','주사후 통증','주사후 시력',
     '주사 부작용','안압 상승','동공 확장','눈 통증','출혈','이물감','시야 이상','광시','b7'),
    ('reason','부작용','후유증','안전성','시술 후','주사 후')],
 'S2_drug_food_interaction': [
    ('함께 먹','같이 먹','병용','동시 복용','상호작용','복용중인','홍삼','한약','항암','다이어트약','결핵약',
     '스테로이드','혈압약','고지혈증','당뇨약','진통제','감기약','b2'),
    ('reason','상호작용','병용','약물','b2','다이어트')],
 'S3_other_ophth_postproc': [
    ('백내장 수술','라식','라섹','녹내장','당뇨망막','망막박리','중심성','중심장액','황반원공','맥락막',
     '안구건조','비문증','광시증','콘택트','렌즈 끼','복시','b4'),
    ('reason','b4','타질환','수술 후','동반','별도')],
 'S4_nonspecific_dx': [
    ('망막변성','망막변증','신생혈관 외','노안',),
    ('reason','비특이','비-amd','진단 불확실','제외 고려','망막변성','망막변증')],
 'S5_lifestyle_protective': [
    ('안경 맞','선글라스 맞','조명','보호 안경','색안경','보안경','보호 렌즈','맞춤 안경'),
    ('reason','안경','선글라스','조명')],
 'S6_caregiver_admin': [
    ('돌봄','요양','케어','보호자','복약','대신','부양'),
    ('reason','돌봄','보호자')],
}

def classify(r):
    q, rs = text(r)
    cats = []
    for sub, (qkws, rkws) in SUBS.items():
        if any(k in q for k in qkws) or any(k in rs for k in rkws[1:]):
            cats.append(sub)
    return cats or ['S7_other']

# 분류 분포
print(f'\n=== C9 sub-category 분포 (C9 any-mention {len(c9_any)}건, multi-tag 가능) ===')
all_subs = Counter()
for r in c9_any:
    for s in classify(r):
        all_subs[s] += 1
for s, n in sorted(all_subs.items(), key=lambda x: -x[1]):
    print(f'  {s:<32} {n:>3} ({n/len(c9_any)*100:4.1f}%)')

# 기간별
def bucket(y): return '~2009' if y<=2009 else '2010-14' if y<=2014 else '2015-19' if y<=2019 else '2020~'
order = ['~2009','2010-14','2015-19','2020~']
byb = {b: [] for b in order}
for r in c9_any:
    byb[bucket(yr(r))].append(r)
all_byb = {b: [] for b in order}
for r in rows:
    all_byb[bucket(yr(r))].append(r)

print(f'\n=== Sub-category 기간별 (분모=전체 corpus 기간 N) ===')
print(f'{"sub":<32}'+ ' '.join(f'{b:>15}' for b in order))
for s in sorted(all_subs, key=lambda x: -all_subs[x]):
    line = f'{s:<32}'
    for b in order:
        n = sum(1 for r in byb[b] if s in classify(r))
        rate = n / len(all_byb[b]) * 100 if all_byb[b] else 0
        line += f'  {n:>3} ({rate:>4.1f}%)'
    print(line)

# S1 absolute count change
print(f'\n=== S1 post-injection AE 절대 건수 변화 ===')
s1_by_period = {b: sum(1 for r in byb[b] if 'S1_post_injection_AE' in classify(r)) for b in order}
print(f'  ~2009: {s1_by_period["~2009"]}')
print(f'  2010-14: {s1_by_period["2010-14"]}')
print(f'  2015-19: {s1_by_period["2015-19"]}')
print(f'  2020~: {s1_by_period["2020~"]}')
print(f'  변화: {s1_by_period["~2009"]} → {s1_by_period["2020~"]} ({s1_by_period["2020~"]/max(s1_by_period["~2009"],1):.0f}-fold)')
