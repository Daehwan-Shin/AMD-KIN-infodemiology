# -*- coding: utf-8 -*-
"""항VEGF 약제명 빈도 점검: 질문only / 답변only / 합산, 정확표기 vs 키워드, 출처별."""
import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')
from collections import Counter
import openpyxl

with open('_stage4_topic_final.jsonl', encoding='utf-8') as f:
    rows = [json.loads(l) for l in f if l.strip()]

wb = openpyxl.load_workbook('황반변성_지식인_크롤링 260415(again).xlsx', read_only=True)
ws = wb['Sheet1']; it = ws.iter_rows(values_only=True)
hdr = list(next(it)); H = {n:i for i,n in enumerate(hdr)}
acs = [H[f'answer_{k}_content'] for k in range(1,6)]; jc = H['answers_json']
amap = {}
for di, row in enumerate(it):
    parts = [str(row[c]) for c in acs if c < len(row) and row[c]]
    if jc < len(row) and row[jc]: parts.append(str(row[jc]))
    amap[di+2] = '\n'.join(parts)
for r in rows:
    r['_ans'] = amap.get(r['row_index'], '')
    r['_q'] = (r.get('question_title','') or '') + ' ' + (r.get('question_content','') or '')

drugs = {
 '아일리아(Eylea)': ['아일리아','아일리어','eylea','애플리버셉','aflibercept'],
 '루센티스(Lucentis)': ['루센티스','루센','lucentis','라니비주맙','ranibizumab'],
 '아바스틴(Avastin)': ['아바스틴','아바스','avastin','베바시주맙','bevacizumab'],
 '바비스모(Vabysmo)': ['바비스모','vabysmo','파리시맙','faricimab'],
 '비오뷰(Beovu)': ['비오뷰','beovu','브롤루시주맙','brolucizumab'],
 '마쿠젠(Macugen)': ['마쿠젠','macugen','페갑타닙'],
}
# 정확표기(엄격): 대표 상품명만
strict = {
 '아일리아': ['아일리아','아일리어'], '루센티스': ['루센티스'],
 '아바스틴': ['아바스틴'], '바비스모': ['바비스모'], '비오뷰': ['비오뷰'], '마쿠젠': ['마쿠젠'],
}

def cnt(field, kws):
    return sum(1 for r in rows if any(w in (r[field]).lower() for w in kws))

print('='*72)
print(f'{"약제":<16}{"질문only":>9}{"답변only":>9}{"질문+답변":>10}{"엄격(상품명)":>12}')
print('='*72)
for name, kws in drugs.items():
    key = name.split('(')[0]
    q = cnt('_q', kws)
    a = cnt('_ans', kws)
    both = sum(1 for r in rows if any(w in (r['_q']+' '+r['_ans']).lower() for w in kws))
    st = sum(1 for r in rows if any(w in (r['_q']+' '+r['_ans']).lower() for w in strict.get(key,[])))
    print(f'{name:<16}{q:>9}{a:>9}{both:>10}{st:>12}')

# 키워드별 어느 토큰이 얼마나 잡았는지 (아바스틴/루센티스 정밀)
print('\n[아바스틴 키워드별 매칭 건수 (질문+답변)]')
for w in drugs['아바스틴(Avastin)']:
    n = sum(1 for r in rows if w in (r['_q']+' '+r['_ans']).lower())
    print(f'  "{w}": {n}')
print('[루센티스 키워드별 매칭 건수]')
for w in drugs['루센티스(Lucentis)']:
    n = sum(1 for r in rows if w in (r['_q']+' '+r['_ans']).lower())
    print(f'  "{w}": {n}')

# '루센' 단독이 루센티스 아닌 것 잡는지 샘플
print('\n["루센" 매칭됐지만 "루센티스" 아닌 본문 샘플]')
c = 0
for r in rows:
    t = (r['_q']+' '+r['_ans']).lower()
    if '루센' in t and '루센티스' not in t:
        seg = t[max(0,t.find('루센')-20):t.find('루센')+20].replace('\n',' ')
        print(f'  …{seg}…')
        c += 1
        if c >= 8: break
print(f'  (총 {sum(1 for r in rows if "루센" in (r["_q"]+" "+r["_ans"]).lower() and "루센티스" not in (r["_q"]+" "+r["_ans"]).lower())}건)')

# 질문 본문만 기준 순위 (답변 영향 배제 — 환자 관심 본질)
print('\n[질문 본문만 기준 순위]')
qonly = {n: cnt('_q', k) for n,k in drugs.items()}
for n,v in sorted(qonly.items(), key=lambda x:-x[1]):
    print(f'  {n:<16} {v:>4} ({v/len(rows)*100:.1f}%)')
