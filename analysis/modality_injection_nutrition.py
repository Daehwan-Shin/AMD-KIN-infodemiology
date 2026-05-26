# -*- coding: utf-8 -*-
"""
Stage 5 세부 분석 (strict_AMD 2,048건):
 1) 기간별 대표주제 구성 변화
 2) 치료 방식 및 항VEGF 약제명 언급 빈도
 3) 주사치료 관련 세부 관심사
 4) 영양제 및 생활습관 관련 키워드
 5) 답변 내 신호 (한방·완치·외부링크·병원추천)
"""
import json, re, sys, statistics
sys.stdout.reconfigure(encoding='utf-8')
from collections import Counter, defaultdict
import openpyxl

CNAME = {'C1':'질환정보·원인','C2':'증상·진단·검사','C3':'치료일반·수술','C4':'항VEGF주사',
 'C5':'영양·생활습관','C6':'경과·예후·실명','C7':'비용·보험·행정','C8':'병원·의료진','C9':'기타'}

with open('_stage4_topic_final.jsonl', 'r', encoding='utf-8') as f:
    rows = [json.loads(l) for l in f if l.strip()]
print(f'strict_AMD: {len(rows)}건')

# ---- 원본 엑셀에서 row_index→답변 텍스트 조인 ----
SRC = '황반변성_지식인_크롤링 260415(again).xlsx'
wb = openpyxl.load_workbook(SRC, read_only=True)
ws = wb['Sheet1']
it = ws.iter_rows(values_only=True)
hdr = list(next(it))
H = {name: i for i, name in enumerate(hdr)}
ans_cols = [H[f'answer_{k}_content'] for k in range(1, 6)]
title_c, json_c = H['question_title'], H['answers_json']

want = {}
for r in rows:
    want[r['row_index']] = r

# 엑셀은 데이터가 2행부터; row_index 의미 검증 위해 enumerate 두 방식 비교
ans_by_excelrow = {}     # 엑셀 물리행(2-base) → 답변텍스트
ans_by_dataidx = {}      # 0-base 데이터 인덱스 → 답변텍스트
title_by_excelrow, title_by_dataidx = {}, {}
for di, row in enumerate(it):
    excelrow = di + 2
    parts = []
    for c in ans_cols:
        v = row[c] if c < len(row) else None
        if v:
            parts.append(str(v))
    jv = row[json_c] if json_c < len(row) else None
    if jv:
        parts.append(str(jv))
    txt = '\n'.join(parts)
    tt = str(row[title_c]) if row[title_c] else ''
    ans_by_excelrow[excelrow] = txt
    ans_by_dataidx[di] = txt
    title_by_excelrow[excelrow] = tt
    title_by_dataidx[di] = tt

# 매핑 방식 자동 판별 (title 일치율 높은 쪽)
def match_rate(tmap):
    ok = tot = 0
    for r in rows[:300]:
        ri = r['row_index']
        if ri in tmap:
            tot += 1
            if tmap[ri][:20] == (r.get('question_title','') or '')[:20]:
                ok += 1
    return ok / tot if tot else 0
r_excel = match_rate(title_by_excelrow)
r_data = match_rate(title_by_dataidx)
use = ans_by_excelrow if r_excel >= r_data else ans_by_dataidx
print(f'row_index 매핑 판별: excelrow={r_excel:.0%} / dataidx={r_data:.0%} → '
      f'{"excelrow" if use is ans_by_excelrow else "dataidx"} 사용')

for r in rows:
    r['_answer'] = use.get(r['row_index'], '')
ans_cov = sum(1 for r in rows if r['_answer'])
print(f'답변 조인: {ans_cov}/{len(rows)}건 ({ans_cov/len(rows)*100:.1f}%)\n')

def qtext(r):
    return (r.get('question_title','') or '') + ' ' + (r.get('question_content','') or '')

def yr(r):
    d = (r.get('question_date','') or '')
    m = re.match(r'(\d{4})', d)
    return int(m.group(1)) if m else None

OUT = []
def p(s=''):
    print(s); OUT.append(s)

# ===== 1) 기간별 대표주제 구성 변화 =====
p('='*70)
p('1) 기간별 대표주제 구성 변화 (primary_topic 비중 %)')
p('='*70)
years = [yr(r) for r in rows if yr(r)]
p(f'기간: {min(years)} ~ {max(years)}, 연도 결측 {sum(1 for r in rows if yr(r) is None)}건')
# 구간 버킷
def bucket(y):
    if y is None: return '미상'
    if y <= 2009: return '~2009'
    if y <= 2013: return '2010-13'
    if y <= 2017: return '2014-17'
    if y <= 2021: return '2018-21'
    if y <= 2023: return '2022-23'
    return '2024-26'
order = ['~2009','2010-13','2014-17','2018-21','2022-23','2024-26']
by_b = defaultdict(list)
for r in rows:
    by_b[bucket(yr(r))].append(r)
codes = [f'C{i}' for i in range(1,10)]
hdrline = f'{"기간":<9}{"n":>5}  ' + ' '.join(f'{c:>5}' for c in codes)
p(hdrline)
for b in order:
    grp = by_b.get(b, [])
    if not grp: continue
    cc = Counter(x['primary_topic'] for x in grp)
    line = f'{b:<9}{len(grp):>5}  ' + ' '.join(f'{cc.get(c,0)/len(grp)*100:>4.0f}%' for c in codes)
    p(line)
p('  (열=C1..C9 primary 비중) 코드: ' + ' / '.join(f'{c}={CNAME[c]}' for c in codes))

# ===== 2) 치료 방식 및 항VEGF 약제명 =====
p('\n'+'='*70)
p('2) 치료 방식 / 항VEGF 약제명 언급 빈도 (질문+답변 합산, 건수 기준)')
p('='*70)
drugs = {
 '아일리아(Eylea)': ['아일리아','아일리어','eylea','애플리버셉','aflibercept'],
 '루센티스(Lucentis)': ['루센티스','lucentis','라니비주맙','ranibizumab'],
 '아바스틴(Avastin)': ['아바스틴','avastin','베바시주맙','bevacizumab'],
 '바비스모(Vabysmo)': ['바비스모','vabysmo','파리시맙','faricimab'],
 '비오뷰(Beovu)': ['비오뷰','beovu','브롤루시주맙','brolucizumab'],
 '마쿠젠(Macugen)': ['마쿠젠','macugen','페갑타닙'],
 '바이오시밀러/기타': ['아멜리부','바이우비즈','루센비에스','byooviz'],
}
modal = {
 '항VEGF 주사': ['주사','안구주사','유리체내','주입','항체주사','anti-vegf','항vegf'],
 '광역학치료(PDT)': ['광역학','pdt','비쥬다인','베르테포르핀'],
 '레이저': ['레이저','광응고','laser'],
 '수술': ['수술','유리체절제','이식'],
 '약물/경구': ['먹는약','경구','복용약','알약'],
 '주사제 일반(미상)': ['눈주사','눈에 주사','안구 주사'],
}
def count_hits(d):
    res = {}
    for k, kws in d.items():
        n = 0
        for r in rows:
            t = (qtext(r) + ' ' + r['_answer']).lower()
            if any(kw in t for kw in kws):
                n += 1
        res[k] = n
    return res
def hits_field(d, field):
    res = {}
    for k, kws in d.items():
        if field == 'both':
            n = sum(1 for r in rows if any(kw in (qtext(r)+' '+r['_answer']).lower() for kw in kws))
        elif field == 'q':
            n = sum(1 for r in rows if any(kw in qtext(r).lower() for kw in kws))
        else:
            n = sum(1 for r in rows if any(kw in r['_answer'].lower() for kw in kws))
        res[k] = n
    return res
p('[항VEGF 약제명] 질문기준 / 답변기준 / 질문+답변 (strict_AMD 2,048건)')
dq, da, db = hits_field(drugs,'q'), hits_field(drugs,'a'), hits_field(drugs,'both')
p(f'  {"약제":<20}{"질문":>7}{"답변":>7}{"합산":>7}')
for k,_ in sorted(db.items(), key=lambda x:-x[1]):
    p(f'  {k:<20}{dq[k]:>7}{da[k]:>7}{db[k]:>7}')
p('  ※ 질문(환자)기준은 아바스틴 우세, 답변(의료진)기준은 루센티스 우세 — 인지 격차')
p('[치료 모달리티]')
for k, n in sorted(count_hits(modal).items(), key=lambda x:-x[1]):
    p(f'  {k:<22} {n:>4}건 ({n/len(rows)*100:4.1f}%)')

# ===== 3) 주사치료 세부 관심사 =====
p('\n'+'='*70)
p('3) 주사치료 관련 세부 관심사 (C4 primary 또는 secondary subset)')
p('='*70)
inj = [r for r in rows if r['primary_topic']=='C4' or 'C4' in r.get('secondary_topics',[])]
p(f'주사 관련 질문(C4 prim/sec): {len(inj)}건')
sub = {
 '효과/호전 정도': ['효과','좋아지','호전','잘보','회복','나아','개선'],
 '주기/횟수/간격': ['몇번','횟수','주기','간격','얼마나 자주','매달','한달','개월마다','평생'],
 '통증/시술 과정': ['아프','통증','따가','무서','과정','어떻게 맞','마취'],
 '부작용/위험': ['부작용','출혈','염증','감염','후유증','위험','안압'],
 '비용/보험': ['비용','얼마','보험','급여','산정특례','지원','만원'],
 '시기/타이밍': ['언제','시기','시점','초기','늦','조기','타이밍'],
 '중단/내성/한계': ['안맞','중단','내성','효과없','더이상','소용','계속 맞아야'],
 '실명 예방 여부': ['실명','막을','예방','진행 막'],
}
for k, kws in sub.items():
    n = sum(1 for r in inj if any(kw in qtext(r) for kw in kws))
    p(f'  {k:<16} {n:>4}건 ({n/len(inj)*100:4.1f}%)' if inj else k)

# ===== 4) 영양제·생활습관 키워드 =====
p('\n'+'='*70)
p('4) 영양제·생활습관 키워드 (C5 primary/secondary subset)')
p('='*70)
nut = [r for r in rows if r['primary_topic']=='C5' or 'C5' in r.get('secondary_topics',[])]
p(f'영양·생활 관련: {len(nut)}건')
supp = {
 '루테인': ['루테인'], '지아잔틴': ['지아잔틴','지아젠틴','제아잔틴'],
 '오메가3': ['오메가','오메가3','오메가-3'], '아스타잔틴': ['아스타잔틴','아스타'],
 '빌베리/베리류': ['빌베리','블루베리','베리'], 'AREDS/오큐바이트류': ['areds','오큐바이트','아레즈','오큐','오큐레이드','오큐테인'],
 '비타민/미네랄': ['비타민','아연','루테인지아잔틴','미네랄','셀레늄'],
 '제품·복용시기': ['언제 먹','식후','공복','복용','함께 먹','병용','상호작용'],
}
for k, kws in supp.items():
    n = sum(1 for r in nut if any(kw in qtext(r).lower() for kw in kws))
    p(f'  영양제: {k:<16} {n:>4}건 ({n/len(nut)*100:4.1f}%)' if nut else k)
life = {
 '음식/식이': ['음식','식단','식이','먹으면','채소','당근','등푸른'],
 '자외선/선글라스': ['자외선','선글라스','햇빛','uv'],
 '금연/흡연': ['금연','담배','흡연'],
 '전자기기/블루라이트': ['핸드폰','스마트폰','컴퓨터','모니터','블루라이트','tv'],
 '운동/생활관리': ['운동','관리','생활습관','수면','스트레스'],
 '예방 일반': ['예방','조심','악화 막','진행 늦'],
}
for k, kws in life.items():
    n = sum(1 for r in nut if any(kw in qtext(r).lower() for kw in kws))
    p(f'  생활:   {k:<16} {n:>4}건 ({n/len(nut)*100:4.1f}%)' if nut else k)

# ===== 5) 답변 내 신호 =====
p('\n'+'='*70)
p('5) 답변 내 신호 (답변 있는 건 대상)')
p('='*70)
ans_rows = [r for r in rows if r['_answer']]
p(f'답변 보유: {len(ans_rows)}건')
sig = {
 '검사/안과 방문 권유': ['검사 받','검사받','검사를 받','안과 가','안과를 가','안과 방문','병원 가보','병원에 가',
   '진료 받','진료받','내원','정밀검사','안저검사','oct','검진 받','진찰','외래','진료를 받','가보시','가보세요'],
 '영양제 권유': ['루테인','영양제','오메가','지아잔틴','아스타잔틴','보충제','복용하세요','드세요','섭취하',
   '아레즈','오큐','areds','챙겨 드','복용을 권','드시는 것이','드셔'],
 '수술/레이저 언급': ['수술','레이저','광응고','광역학','pdt','유리체절제','이식','수술적'],
 '주사치료 언급': ['주사','안구주사','안내주사','유리체내','주입','항체주사','아바스틴','루센티스','아일리아',
   '바비스모','비오뷰','마쿠젠','항vegf','anti-vegf'],
 '외부 링크/블로그': ['http','www.','blog.','cafe.','.com','.kr','카페','블로그','링크','네이버 검색','유튜브'],
 '병원/의원 추천': ['병원을 추천','안과를 추천','추천합니다','추천드','원장','교수님','저희 병원','이 병원',
   '명의','잘하는 병원','잘보는','전문의가 있','OO안과','으로 가시','병원으로 가'],
 '한방/침/한약 언급': ['한방','한약','한의원','침 치료','침을 맞','침치료','뜸','한의사','한방치료','한방병원','약침'],
 '시력회복/완치 표현': ['완치','낫습니다','낫는다','낫게','회복됩니다','회복돼','좋아집니다','좋아져','특효',
   '100%','확실히 좋','시력 회복','시력회복','치료됩니다','정상으로','원상복구'],
}
for k, kws in sig.items():
    n = sum(1 for r in ans_rows if any(kw in r['_answer'].lower() for kw in kws))
    p(f'  {k:<16} {n:>4}건 ({n/len(ans_rows)*100:4.1f}%)')
# 채택답변 길이/개수 간단 통계
alen = [len(r['_answer']) for r in ans_rows]
p(f'\n  답변텍스트 길이 평균 {statistics.mean(alen):.0f}자 / 중앙 {statistics.median(alen):.0f}자')

# 저장
with open('_stage5_report.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(OUT))
print('\n→ _stage5_report.txt 저장')
