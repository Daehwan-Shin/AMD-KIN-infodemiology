# -*- coding: utf-8 -*-
"""
A3 기간별 주제 추세 통계검정:
 - 전체: 기간(4구간) × primary_topic χ² 독립성
 - 주제별: 연도(연속 score) Cochran–Armitage trend test (Z, two-sided p)
 - 다중비교: Benjamini–Hochberg FDR 보정
"""
import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')
from collections import Counter, defaultdict
import numpy as np
from scipy.stats import chi2_contingency, norm

CNAME={'C1':'질환정보·원인','C2':'증상·진단·검사','C3':'치료일반·수술','C4':'항VEGF주사',
 'C5':'영양·생활습관','C6':'경과·예후·실명','C7':'비용·보험·행정','C8':'병원·의료진','C9':'기타'}
codes=[f'C{i}' for i in range(1,10)]

with open('_stage4_topic_FINAL_v3_1989.jsonl', encoding='utf-8') as f:
    rows=[json.loads(l) for l in f if l.strip()]
def yr(r):
    m=re.match(r'(\d{4})', r.get('question_date','') or ''); return int(m.group(1)) if m else None
rows=[r for r in rows if yr(r)]
print(f'분석 대상: {len(rows)}건 (연도 {min(yr(r) for r in rows)}~{max(yr(r) for r in rows)})')

# ---- 1) 전체 χ²: 4구간 × 9주제 ----
def bucket(y):
    return '~2009' if y<=2009 else '2010-14' if y<=2014 else '2015-19' if y<=2019 else '2020~'
order=['~2009','2010-14','2015-19','2020~']
tab=np.zeros((len(order),9),dtype=int)
for r in rows:
    bi=order.index(bucket(yr(r))); ci=codes.index(r['final_primary']); tab[bi,ci]+=1
chi2,p,dof,_=chi2_contingency(tab)
# Cramér's V
nN=tab.sum(); V=np.sqrt(chi2/(nN*(min(tab.shape)-1)))
print(f'\n[전체 독립성] 4기간 × 9주제 χ²={chi2:.1f}, df={dof}, p={p:.3e}, Cramér V={V:.3f}')
print('  → 주제 구성이 기간에 따라 유의하게 다름' if p<.05 else '  → 유의차 없음')

# ---- 2) 주제별 Cochran–Armitage (연도 연속 score) ----
def cochran_armitage(year_arr, bin_arr):
    yrs=sorted(set(year_arr))
    n=np.array([np.sum(year_arr==y) for y in yrs],float)
    r=np.array([np.sum(bin_arr[year_arr==y]) for y in yrs],float)
    s=np.array(yrs,float)
    N=n.sum(); R=r.sum(); pbar=R/N
    sbar=np.sum(n*s)/N
    T=np.sum(r*(s-sbar))
    var=pbar*(1-pbar)*(np.sum(n*s**2)-(np.sum(n*s)**2)/N)
    if var<=0: return 0.0,1.0,0.0
    Z=T/np.sqrt(var)
    pval=2*norm.sf(abs(Z))
    return Z,pval,pbar

yarr=np.array([yr(r) for r in rows])
res=[]
for c in codes:
    b=np.array([1 if r['final_primary']==c else 0 for r in rows])
    Z,pv,pb=cochran_armitage(yarr,b)
    # 방향: 초기(≤2012) vs 후기(≥2018) 비율
    early=b[yarr<=2012].mean()*100 if (yarr<=2012).any() else 0
    late =b[yarr>=2018].mean()*100 if (yarr>=2018).any() else 0
    res.append([c,Z,pv,early,late,'▲증가' if Z>0 else '▼감소'])

# BH-FDR 보정
ps=sorted([(r[2],i) for i,r in enumerate(res)])
m=len(ps); adj=[0]*m
prev=1.0
for rank,(pv,idx) in enumerate(reversed(ps)):
    k=m-rank
    val=min(prev, pv*m/k); prev=val; adj[idx]=val

print('\n[주제별 시간 추세] Cochran–Armitage (연도 연속, two-sided)')
print(f'{"주제":<18}{"Z":>7}{"p":>11}{"p(FDR)":>11}  {"≤2012%":>7}{"≥2018%":>7}  방향')
for i,(c,Z,pv,e,l,d) in enumerate(res):
    sig='***' if adj[i]<.001 else '**' if adj[i]<.01 else '*' if adj[i]<.05 else 'ns'
    print(f'{c} {CNAME[c]:<14}{Z:>7.2f}{pv:>11.2e}{adj[i]:>11.2e}  {e:>6.1f}%{l:>6.1f}%  {d} {sig}')
print('  *** p<.001  ** p<.01  * p<.05  ns 비유의 (FDR 보정)')


# ---- 3) any-mention Cochran-Armitage (primary OR secondary), BH-FDR across 9 ----
def anyset(r):
    ss=r.get('final_secondary') or []
    if isinstance(ss,str): ss=[x.strip() for x in re.split(r'[;,]',ss) if x.strip()]
    return set([r['final_primary']]+list(ss))-{''}
res_am=[]
for c in codes:
    b=np.array([1 if c in anyset(r) else 0 for r in rows])
    Z,pv,pb=cochran_armitage(yarr,b); res_am.append([c,Z,pv])
ps2=sorted([(res_am[i][2],i) for i in range(len(res_am))]); adj2=[0]*len(res_am); prev=1.0
for rank,(pv,idx) in enumerate(reversed(ps2)):
    k=len(res_am)-rank; val=min(prev,pv*len(res_am)/k); prev=val; adj2[idx]=val
print()
print('[any-mention time trend] Cochran-Armitage (primary OR secondary; BH-FDR across 9)')
for i,(c,Z,pv) in enumerate(res_am):
    sig='***' if adj2[i]<.001 else '**' if adj2[i]<.01 else '*' if adj2[i]<.05 else 'ns'
    print(f'{c} {CNAME[c]:<14}{Z:>7.2f}{pv:>11.2e}{adj2[i]:>11.2e}  {sig}')

# 저장
with open('_stage5_trend_stats.txt','w',encoding='utf-8') as f:
    f.write(f'전체 χ²={chi2:.1f}, df={dof}, p={p:.3e}, Cramér V={V:.3f}\n\n')
    f.write(f'{"주제":<18}{"Z":>7}{"p":>11}{"p_FDR":>11}{"≤2012%":>8}{"≥2018%":>8} 방향\n')
    for i,(c,Z,pv,e,l,d) in enumerate(res):
        f.write(f'{c} {CNAME[c]:<14}{Z:>7.2f}{pv:>11.2e}{adj[i]:>11.2e}{e:>7.1f}%{l:>7.1f}% {d}\n')
print('\n→ _stage5_trend_stats.txt 저장')
