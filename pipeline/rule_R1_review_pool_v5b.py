# -*- coding: utf-8 -*-
"""Rule v5b = v5 + P4.5/P5 더 광범위한 패턴.

추가 패턴:
  P4.5b (told NOT AMD / self-denial):
    - "황반변성 처럼 (...) 전혀 없" / "황반변성 같은 (...) 없" — self-denial
  P5b (exam normal — broader phrases):
    - "황반변성 검사 (...) 큰 이상 없"
    - "별말 없" / "별다른 말 없"
    - "딱히 (...) 언급 없" / "딱히 (...) 문제 없"
"""
import json, sys, re
sys.stdout.reconfigure(encoding='utf-8')
from collections import Counter
from sklearn.metrics import cohen_kappa_score, confusion_matrix
import openpyxl

with open('_stage3_review_pool_v3.jsonl', encoding='utf-8') as f:
    pool = [json.loads(l) for l in f if l.strip()]
pool_by_id = {(r.get('phase2_id') or r.get('phase1_id')): r for r in pool}
with open('_R1_validation_key.jsonl', encoding='utf-8') as f:
    key = [json.loads(l) for l in f if l.strip()]


def classify_v5b(r):
    body = (r.get('question_content') or '')
    title = (r.get('question_title') or '')
    body_full = title + '  ' + body
    txt = ' '.join([(r.get('codex_reason') or ''), (r.get('opus_reason') or '')])
    has = lambda code: bool(re.search(rf'\b{code}\b', txt))

    if has('G2') or '아니라고' in txt or '황반변성 아님' in txt:
        return 'not_R1', 'P1 G2'
    if has('G7'): return 'not_R1', 'P2 G7'

    amd_mentions = len(re.findall(r'황반\s*변성|AMD\b', body_full))
    others = ['백내장','녹내장','망막박리','망막열공','비문증','포도막염','결막염','안압',
              '익상편','시신경','시야결손','시야장애','난시','근시','원시','약시','사시',
              '사위','안검하수','망막색소변성','망막혈관폐쇄','시신경유두']
    if amd_mentions <= 2 and sum(1 for d in others if d in body_full) >= 2:
        return 'not_R1', 'P3.5 Type 1'

    if has('G6') or '약물성' in txt or '결핵약' in txt or '불스아이' in txt:
        return 'not_R1', 'P4 G6'

    # P4.5 — told NOT AMD (확장: self-denial of AMD symptoms)
    told_not = [
        r'황반\s*변성\s*(은|이|을)?\s*(아니라고|아니랍|아니래|아닙니다|아님|아닌|아니래요)',
        r'황반\s*변성\s*(은|이|을)?\s*없(다고|답|대|어요|었다|었답)',
        r'(검사|진단|결과)\s*상.{0,15}황반\s*변성.{0,15}(아니|없)',
        r'다행히.{0,15}황반\s*변성.{0,5}(아니|없)',
        r'AMD\s*(는|은)?\s*(아니|없)',
        # ── NEW: self-denial of AMD symptoms ──
        r'황반\s*변성\s*(처럼|같은|같이).{0,80}(전혀\s*없|는\s*없|은\s*없)',
        r'(황반\s*변성\s*증상).{0,40}(전혀\s*없|는\s*없)',
        r'(전혀\s*없|이런\s*증상\s*없).{0,80}황반\s*변성\s*(처럼|같|증상)',
    ]
    if any(re.search(p, body_full) for p in told_not):
        return 'not_R1', 'P4.5 told NOT / self-denial'

    # P5 — AMD 검사 정상 (확장)
    test_normal = [
        r'(안저|정밀|산동|망막|황반)\s*검사.{0,40}(정상|이상\s*없|이상이\s*없|이상은\s*없)',
        r'(정상|이상\s*없|이상이\s*없|이상은\s*없).{0,30}(안저|망막|황반\s*변성)',
        r'황반\s*변성\s*검사.{0,40}(정상|이상\s*없|아니라고|아님)',
        r'(아무\s*이상\s*없|이상이\s*없다고|정상이라고|정상이였|정상이었)',
        r'황반.{0,10}깨끗',
        r'암슬러.{0,5}격자.{0,20}(아무\s*렇지|이상\s*없|아무\s*문제|정상)',
        r'(검진|검사).{0,15}아무\s*이상\s*없',
        r'(검진|검사)\s*받았.{0,5}(이상|문제)\s*없',
        # ── NEW broader exam-normal phrases ──
        r'황반\s*변성\s*검사.{0,30}(큰\s*)?이상\s*(은\s*|이\s*)?없',
        r'안과.{0,20}별\s*말\s*없',
        r'(별\s*다른\s*말|별다른\s*소견|별\s*다른\s*문제)\s*없',
        r'(딱히|별\s*다른).{0,20}(언급|소견|이상|문제|소견).{0,10}(못\s*받|없|들\s*못)',
        r'(별\s*문제|큰\s*문제|특별한\s*문제)\s*(은\s*|이\s*|가\s*)?\s*없',
        r'(병원|안과)\s*갔.{0,15}별\s*말\s*없',
        r'(병원|안과)\s*갔.{0,15}이상\s*(은\s*|이\s*)?\s*없',
        # 의사 reassurance
        r'(걱정\s*안\s*해\s*도|걱정\s*하지\s*마|걱정\s*없다)',
        # 진료/검사 결과 별 이상 없음 broad
        r'(진료|검진|검사|결과).{0,30}별\s*이상\s*없',
        r'(진료|검진|검사|결과).{0,30}이상\s*소견\s*없',
    ]
    if any(re.search(p, body_full) for p in test_normal):
        return 'not_R1', 'P5 검사 정상 (확장)'

    # P6 — Non-AMD 원인
    non_amd = [
        r'백신\s*(접종|후|차|이후|증상|반응|부작용)',
        r'(화이자|모더나|아스트라|얀센)\s*(백신|접종)?\s*(후|이후|차)',
        r'(약\s*부작용|약을?\s*먹.{0,5}(후|이후)|약물\s*부작용)',
        r'편두통\s*약', r'플래시.{0,15}(본|쳐다본|보고)\s*(후|이후)',
        r'(외상|충격|부딪|맞은\s*후)',
    ]
    if any(re.search(p, body_full) for p in non_amd):
        return 'not_R1', 'P6 Non-AMD'

    # P7 — Title 다른 안과
    if any(p in title for p in ['난시','라식','라섹','쌍수','앞트임','비문증']):
        return 'not_R1', 'P7 title'
    if re.match(r'^\s*루테인', title):
        return 'not_R1', 'P7 루테인'

    # P8-P13 (v5 동일, single-LLM trigger)
    if has('G3') or '백내장' in txt or '라식' in txt or '라섹' in txt or '복시' in txt or '진료과' in txt:
        return 'not_R1', 'P8 G3'
    if has('G5'): return 'not_R1', 'P9 G5'
    if has('R4') or '동반' in txt or '격자변성' in txt or '망막박리' in txt:
        return 'not_R1', 'P10 R4'
    if has('R5') or '칼럼' in txt or '기고' in txt or '스팸' in txt:
        return 'not_R1', 'P11 R5'
    if '근시' in txt: return 'not_R1', 'P12 근시'
    if ('borderline' in txt or '40대' in txt or '30대' in txt
            or '경계 연령' in txt or '경계연령' in txt):
        return 'not_R1', 'P13 borderline'

    # P14 자가의심 (LLM rationale only)
    if has('R1') or '자가 의심' in txt or '자가의심' in txt:
        return 'R1', 'P14 자가의심'

    return 'not_R1', 'P15 기타'


# === apply v5b to 100 sample ===
new_labels = []
for k in key:
    pr = pool_by_id[k['id']]
    lbl, branch = classify_v5b(pr)
    new_labels.append({'no': k['sample_no'], 'id': k['id'], 'v5b': lbl, 'branch': branch,
                       'v1': k['rule_label']})
v5b_dist = Counter(n['v5b'] for n in new_labels)
print(f'v5b 100-sample: {dict(v5b_dist)}')

# load labels
def load(p):
    wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
    ws = wb['data']; rows = {}
    for r in ws.iter_rows(min_row=2, values_only=True):
        no, rid, _, _, lbl, _ = r
        rows[no] = (lbl or '').strip()
    wb.close(); return rows
sdh = load('AMD_R1_validation_100_SDH_Done.xlsx')
nkt = load('AMD_R1_validation_100_NKT_Done.xlsx')

by_no = {n['no']: n for n in new_labels}

def kappa(rule_key, label_dict, name):
    pairs = []
    for no in range(1, 101):
        rl = by_no[no][rule_key]; el = label_dict[no]
        if el in ('R1','not_R1') and rl in ('R1','not_R1'):
            pairs.append((rl, el))
    if not pairs: return
    y_rule, y_exp = zip(*pairs)
    yt = [['R1','not_R1'].index(x) for x in y_rule]
    yp = [['R1','not_R1'].index(x) for x in y_exp]
    raw = sum(1 for a,b in zip(yt,yp) if a==b)/len(yt)
    k = cohen_kappa_score(yt, yp)
    cm = confusion_matrix(y_rule, y_exp, labels=['R1','not_R1'])
    print(f'  {name}  n={len(pairs)}  κ={k:.3f}  raw={raw*100:.1f}%')
    print(f'    rule_R1→exp_R1={cm[0,0]} rule_R1→exp_not={cm[0,1]} | rule_not→exp_R1={cm[1,0]} rule_not→exp_not={cm[1,1]}')

print('\n=== v5b vs current labels ===')
kappa('v5b', sdh, 'SDH(updated) vs v5b')
kappa('v5b', nkt, 'NKT vs v5b')

gold = [no for no in range(1,101) if sdh[no] == nkt[no] and sdh[no] in ('R1','not_R1')]
gold_m = sum(1 for no in gold if by_no[no]['v5b'] == sdh[no])
print(f'\nGold-subset (n={len(gold)}): {gold_m}/{len(gold)} = {100*gold_m/len(gold):.1f}%')

# v5 vs v5b 변화
print(f'\n=== v5b 변화 (vs v5 in 100 sample) ===')
# v5 dist was 36 R1, 64 not_R1
# v5b dist
diff_r1_to_not = sum(1 for n in new_labels if n['v5b'] == 'not_R1')
print(f'  v5b R1 / not_R1 = {v5b_dist["R1"]} / {v5b_dist["not_R1"]}')

# === apply v5b to full 648 ===
print(f'\n=== v5b on full 648 ===')
v5b_full = Counter(); v5b_branches = Counter()
for r in pool:
    lbl, branch = classify_v5b(r)
    v5b_full[lbl] += 1
    v5b_branches[branch] += 1
print(f'v5b: R1={v5b_full["R1"]} ({v5b_full["R1"]/648*100:.1f}%) | not_R1={v5b_full["not_R1"]} ({v5b_full["not_R1"]/648*100:.1f}%)')
print(f'\nbranches:')
for b, c in v5b_branches.most_common():
    print(f'  {c:>4}  {b}')

# 비교
print(f'\n=== Summary v1 / v5 / v5b ===')
print('                  v1      v5      v5b')
print(f'648-R1          212     165     {v5b_full["R1"]}')
print(f'prevalence     32.7%   25.5%   {v5b_full["R1"]/648*100:.1f}%')

# === 사용자 발견 케이스 진단 ===
print(f'\n=== 사용자가 짚은 케이스들이 v5b 에서 어떻게 분류되는지 ===')
check_ids = ['P2-1099', 'P2-1241', 'P2-1294', 'P2-2516', 'P2-3075', 'P2-3358']
for rid in check_ids:
    if rid not in pool_by_id: continue
    lbl, br = classify_v5b(pool_by_id[rid])
    title = pool_by_id[rid].get('question_title','')[:50]
    print(f'  {rid:<8}  v5b = {lbl:<7} ({br:<25})  {title}')

# save
with open('_R1_v5b_predictions_648.jsonl', 'w', encoding='utf-8') as f:
    for r in pool:
        rid = r.get('phase2_id') or r.get('phase1_id')
        lbl, branch = classify_v5b(r)
        f.write(json.dumps({'id': rid, 'v5b': lbl, 'branch_v5b': branch}, ensure_ascii=False) + '\n')
print(f'\n→ _R1_v5b_predictions_648.jsonl')
