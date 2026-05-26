# -*- coding: utf-8 -*-
"""
답변신호 v2 (정련): FP 4대 패턴 제거
 1) 질문인용부(#질문..#답변) 제거 → 답변 본문만
 2) 답변자 서명 오탐 제거 (병원추천: '○○원장입니다' 류 제외, 추천맥락 요구)
 3) 반대의미 제거 (완치: '완치 아니/없/보장은 없/개념보다는' 제외)
 4) 무관키워드 제거 ('100%' 단독, '내원'이 한의원 동반 등)
정련 전(v1) vs 후(v2) 건수 비교 + fig5 재생성 + 리포트 갱신.
"""
import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')
from collections import Counter
import openpyxl

with open('_stage4_topic_final.jsonl', encoding='utf-8') as f:
    rows=[json.loads(l) for l in f if l.strip()]
wb=openpyxl.load_workbook('황반변성_지식인_크롤링 260415(again).xlsx', read_only=True)
ws=wb['Sheet1']; it=ws.iter_rows(values_only=True)
hdr=list(next(it)); H={n:i for i,n in enumerate(hdr)}
acs=[H[f'answer_{k}_content'] for k in range(1,6)]; jc=H['answers_json']
amap={}
for di,row in enumerate(it):
    parts=[str(row[c]) for c in acs if c<len(row) and row[c]]
    if jc<len(row) and row[jc]: parts.append(str(row[jc]))
    amap[di+2]='\n'.join(parts)
for r in rows: r['_ans_raw']=amap.get(r['row_index'],'')

# (1) 질문 인용부 제거
def clean(txt):
    # '#질문 ... #답변' / '##질문 ... ##답변' 블록 제거
    t=re.sub(r'#{1,3}\s*질문.*?#{1,3}\s*답변', ' ', txt, flags=re.S)
    # 남은 '#질문' 이후 동일줄 일부도 제거 (답변표지 없을 때)
    t=re.sub(r'#{1,3}\s*질문', ' ', t)
    return t
for r in rows: r['_ans']=clean(r['_ans_raw']).lower()

def has_any(t, kws): return any(k in t for k in kws)
def near(t, kw, pats, win=25):
    """kw 출현 위치 ±win 안에 pats 중 하나가 있으면 True"""
    i=0
    while True:
        j=t.find(kw,i)
        if j<0: return False
        seg=t[max(0,j-win):j+len(kw)+win]
        if any(p in seg for p in pats): return True
        i=j+len(kw)

# v1 (기존) 키워드
SIG_V1={
 '검사/안과 방문 권유': ['검사 받','검사받','검사를 받','안과 가','안과를 가','안과 방문','병원 가보','병원에 가','진료 받','진료받','내원','정밀검사','안저검사','oct','검진 받','진찰','외래','진료를 받','가보시','가보세요'],
 '영양제 권유': ['루테인','영양제','오메가','지아잔틴','아스타잔틴','보충제','복용하세요','드세요','섭취하','아레즈','오큐','areds','챙겨 드','복용을 권','드시는 것이','드셔'],
 '수술/레이저 언급': ['수술','레이저','광응고','광역학','pdt','유리체절제','이식','수술적'],
 '주사치료 언급': ['주사','안구주사','안내주사','유리체내','주입','항체주사','아바스틴','루센티스','아일리아','바비스모','비오뷰','마쿠젠','항vegf','anti-vegf'],
 '외부 링크/블로그': ['http','www.','blog.','cafe.','.com','.kr','카페','블로그','링크','네이버 검색','유튜브'],
 '병원/의원 추천': ['병원을 추천','안과를 추천','추천합니다','추천드','원장','교수님','저희 병원','이 병원','명의','잘하는 병원','잘보는','전문의가 있','OO안과','으로 가시','병원으로 가'],
 '한방/침/한약 언급': ['한방','한약','한의원','침 치료','침을 맞','침치료','뜸','한의사','한방치료','한방병원','약침'],
 '시력회복/완치 표현': ['완치','낫습니다','낫는다','낫게','회복됩니다','회복돼','좋아집니다','좋아져','특효','100%','확실히 좋','시력 회복','시력회복','치료됩니다','정상으로','원상복구'],
}
def v1count(name):
    return sum(1 for r in rows if has_any(r['_ans_raw'].lower(), SIG_V1[name]))

# v2 정련 검출
def detect_v2(r, name):
    t=r['_ans']
    if name=='검사/안과 방문 권유':
        kws=['검사 받','검사받','검사를 받','검사를받','안과 가보','안과로 가','안과 방문','안과를 방문',
             '진료 받','진료받','진료를 받','정밀검사','검진 받','진찰 받','안과에 가','병원에 가보']
        if not has_any(t,kws): return False
        # 한의원 내원 광고 제외
        return True
    if name=='영양제 권유':
        return has_any(t,['루테인','영양제','오메가','지아잔틴','아스타잔틴','보충제','눈영양','눈 영양',
            '복용하세요','드세요','섭취하','챙겨 드','복용을 권','드셔','아레즈','오큐바이트','areds'])
    if name=='수술/레이저 언급':
        return has_any(t,['수술','레이저','광응고','광역학','pdt','유리체절제'])
    if name=='주사치료 언급':
        return has_any(t,['주사','안구주사','안내주사','유리체내','항체주사','아바스틴','루센티스','아일리아',
            '바비스모','비오뷰','마쿠젠','항vegf','anti-vegf','주입술'])
    if name=='외부 링크/블로그':
        return has_any(t,['http','www.','blog.','cafe.','.com','.kr','네이버 검색','네임카드','유튜브','블로그에','카페에'])
    if name=='병원/의원 추천':
        # 서명 제외: '원장 입니다/원장입니다' 형태는 추천 아님
        # 추천 맥락 키워드만
        rec=['병원을 추천','안과를 추천','병원 추천','안과 추천','추천해 드','추천해드','추천드립니다',
             '명의','잘하는 병원','잘보는','잘 보는 안과','잘봐주','잘 봐주','유명한 안과','전문의가 있는 안과',
             '병원으로 가보','병원으로 가시','으로 가보세요','알아보세요']
        if has_any(t,rec): return True
        # '원장님' + 추천동사 근접
        if near(t,'원장님',['추천','잘본','잘 본','잘봐','잘 봐','알아보','유명','계시']) : return True
        return False
    if name=='한방/침/한약 언급':
        return has_any(t,['한방','한약','한의원','한의사','침 치료','침치료','침을 맞','뜸','약침','한방치료','한방병원','해독요법','한의학'])
    if name=='시력회복/완치 표현':
        # 부정/무관 제외
        hits=False
        for kw in ['완치','시력회복','시력 회복','원상복구','정상으로 회복','정상으로 돌아','특효','낫습니다','낫게 해','회복된다']:
            if kw in t:
                # '완치' 부정 컨텍스트 제외
                if kw=='완치' and near(t,'완치',['아니','없','보장은 없','개념보다','어렵','불가']):
                    continue
                hits=True; break
        # '100%' 는 '100% 완치/회복' 결합만
        if not hits and ('100% 완치' in t or '100% 회복' in t or '100%회복' in t):
            hits=True
        return hits
    return False

names=list(SIG_V1.keys())
print(f'{"신호":<20}{"v1(원)":>8}{"v2(정련)":>9}{"Δ":>7}')
print('-'*48)
v2res={}
for nm in names:
    v1=v1count(nm)
    v2=sum(1 for r in rows if detect_v2(r,nm))
    v2res[nm]=v2
    print(f'{nm:<20}{v1:>8}{v2:>9}{v2-v1:>+7}')

# fig5 v2 재생성
import matplotlib, os
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib import font_manager
# Cross-platform Korean font detection (Windows · macOS · Linux)
for fp in ['C:/Windows/Fonts/malgun.ttf',
           '/System/Library/Fonts/Supplemental/AppleGothic.ttf',
           '/usr/share/fonts/truetype/nanum/NanumGothic.ttf']:
    if os.path.exists(fp):
        font_manager.fontManager.addfont(fp)
        plt.rcParams['font.family']=font_manager.FontProperties(fname=fp).get_name()
        break
plt.rcParams['axes.unicode_minus']=False; plt.rcParams['figure.dpi']=300
N=len(rows)
data=sorted(v2res.items(), key=lambda x:x[1])
RED={'한방/침/한약 언급','시력회복/완치 표현'}
fig,ax=plt.subplots(figsize=(10,5.5))
cols=['#E15759' if k in RED else '#F28E2B' for k,_ in data]
bars=ax.barh([k for k,_ in data],[v for _,v in data],color=cols,edgecolor='white')
for b,(k,v) in zip(bars,data):
    ax.text(v+max(v2res.values())*0.012,b.get_y()+b.get_height()/2,
            f'{v}  ({v/N*100:.1f}%)',va='center',fontsize=9)
ax.set_xlim(0,max(v2res.values())*1.18)
ax.set_title('답변 내 신호 (정련 v2, strict_AMD 2,048건)',fontsize=13,fontweight='bold')
ax.text(0.99,-0.11,'빨강=비의학 권유(한방·완치) · 질문인용/서명/부정맥락 제거',
        transform=ax.transAxes,ha='right',fontsize=8,color='#E15759')
plt.tight_layout(); plt.savefig('_stage5_figures/fig5_답변신호.png',bbox_inches='tight'); plt.close()
print('\n→ _stage5_figures/fig5_답변신호.png (v2 갱신)')

with open('_stage5_signal_v2.txt','w',encoding='utf-8') as f:
    f.write(f'{"신호":<20}{"v1":>7}{"v2":>7}{"v2%":>8}\n')
    for nm in names:
        v2=v2res[nm]; f.write(f'{nm:<20}{v1count(nm):>7}{v2:>7}{v2/N*100:>7.1f}%\n')
print('→ _stage5_signal_v2.txt')
