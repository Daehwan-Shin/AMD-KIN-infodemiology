"""
2-of-3 majority vote: Codex × Opus × Gemini → 최종 라벨 갱신.

규칙:
- Codex == Opus 인 합의 케이스 (2,733건): 그대로 유지 (consensus='agree')
- Disagreement 1,115건: Gemini 라벨을 받아 2-of-3 majority 적용
    · 3개 중 2개 이상 같으면 → 그 라벨
    · 3개 다 다르면 → 'Review_needed' (보수적)
- consensus 필드: 'agree' (원래) / 'gemini_majority' (2-of-3) / 'three_way_split' (3 모두 다름)
"""
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')
from collections import Counter

# 기존 final
with open('_stage2_full_final.jsonl', 'r', encoding='utf-8') as f:
    items = [json.loads(line) for line in f if line.strip()]

# Gemini 결과 4 chunks 합쳐서 dict로
gemini = {}
for i in range(1, 5):
    path = f'_stage3_gemini_chunk_{i}.jsonl'
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    o = json.loads(line)
                    gemini[o['id']] = o['AMD_status']
    except FileNotFoundError:
        print(f'⚠ {path} 없음 (Gemini 아직 미실행?)')

print(f'Gemini 라벨 수신: {len(gemini)}/1115')

if len(gemini) == 0:
    print('Gemini 결과 없어 종료. Gemini 실행 후 다시 돌리세요.')
    sys.exit(0)

# Majority vote 적용
labels = ['Include_strict_AMD', 'Review_needed', 'Exclude_non_AMD', 'Unclear']
out = []
n_agree = 0
n_majority = 0
n_split = 0
n_missing_gemini = 0

for m in items:
    sid = m.get('phase2_id') or m.get('phase1_id')
    c = m['codex_AMD_status']
    o = m['opus_AMD_status']
    consensus = m['consensus']

    if consensus == 'agree':
        # 원래 합의: 그대로
        n_agree += 1
        out.append({**m, 'gemini_AMD_status': None, 'final_v3': c, 'consensus_v3': 'agree'})
    else:
        # disagreement → Gemini 봐서 majority
        g = gemini.get(sid)
        if g is None:
            n_missing_gemini += 1
            out.append({**m, 'gemini_AMD_status': None, 'final_v3': 'Review_needed',
                        'consensus_v3': 'gemini_missing'})
            continue
        votes = Counter([c, o, g])
        top_label, top_count = votes.most_common(1)[0]
        if top_count >= 2:
            n_majority += 1
            out.append({**m, 'gemini_AMD_status': g, 'final_v3': top_label,
                        'consensus_v3': 'gemini_majority'})
        else:
            n_split += 1
            out.append({**m, 'gemini_AMD_status': g, 'final_v3': 'Review_needed',
                        'consensus_v3': 'three_way_split'})

# 저장
with open('_stage3_full_final_v3.jsonl', 'w', encoding='utf-8') as f:
    for r in out:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')
print(f'저장: _stage3_full_final_v3.jsonl ({len(out)}건)')

print(f'\n== Consensus breakdown ==')
print(f'  agree (Codex=Opus):           {n_agree}')
print(f'  gemini_majority (2-of-3):     {n_majority}')
print(f'  three_way_split (모두 다름):   {n_split}')
if n_missing_gemini:
    print(f'  ⚠ gemini 응답 누락:           {n_missing_gemini}')

# 최종 라벨 분포
print(f'\n== Final v3 distribution ==')
dist_v3 = Counter(r['final_v3'] for r in out)
total = sum(dist_v3.values())
for lbl in labels:
    print(f'  {lbl:<22} {dist_v3.get(lbl,0):>5} ({dist_v3.get(lbl,0)/total*100:.1f}%)')

# 이전 v2 (disagreement→Review) 분포와 비교
print(f'\n== v2 (disagreement→Review) vs v3 (majority) 비교 ==')
dist_v2 = Counter(r['final_AMD_status'] for r in out)
print(f'{"label":<22} {"v2":>8} {"v3":>8} {"Δ":>8}')
for lbl in labels:
    v2 = dist_v2.get(lbl, 0)
    v3 = dist_v3.get(lbl, 0)
    d = v3 - v2
    sign = '+' if d > 0 else ''
    print(f'  {lbl:<22} {v2:>8} {v3:>8} {sign}{d:>7}')

# strict_AMD v3 저장
strict_v3 = [r for r in out if r['final_v3'] == 'Include_strict_AMD']
with open('_stage3_strict_AMD_v3.jsonl', 'w', encoding='utf-8') as f:
    for r in strict_v3:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')
print(f'\n★ strict_AMD v3: {len(strict_v3)}건 → _stage3_strict_AMD_v3.jsonl')

# Review pool v3
review_v3 = [r for r in out if r['final_v3'] == 'Review_needed']
with open('_stage3_review_pool_v3.jsonl', 'w', encoding='utf-8') as f:
    for r in review_v3:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')
print(f'Review_needed v3: {len(review_v3)}건 → _stage3_review_pool_v3.jsonl')
