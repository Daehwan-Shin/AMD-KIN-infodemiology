# -*- coding: utf-8 -*-
"""Convert the released CSV to the JSONL format expected by analysis scripts.

The analysis scripts in this folder load `_stage4_topic_FINAL_v3_1989.jsonl`
(the intermediate output of the corpus_construction step). Run this helper once
to derive that JSONL from the released `data/strict_AMD_corpus_1989.csv`.

    cd analysis/
    python _csv_to_jsonl.py

Output: ../_stage4_topic_FINAL_v3_1989.jsonl (repository root; analysis scripts run from root).
"""
import csv, json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
csv.field_size_limit(2_000_000)

src = Path(__file__).resolve().parent.parent / 'data/strict_AMD_corpus_1989.csv'
dst = Path(__file__).resolve().parent.parent / '_stage4_topic_FINAL_v3_1989.jsonl'

with open(src, encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))
print(f'Loaded {len(rows)} rows from {src.name}')

with open(dst, 'w', encoding='utf-8') as f:
    for r in rows:
        sec = r['secondary_topics']
        secondary_list = [s.strip() for s in sec.split(';') if s.strip()] if sec else []
        secondary_list = [t for t in secondary_list if t != r['primary_topic']]  # drop primary if duplicated in secondary
        out = {
            'phase2_id': r['id'],                     # anonymized id
            'question_date': r['question_year'],      # year only
            'category': r['category'],
            'question_title': r['question_title'],
            'question_content': r['question_content'],
            'final_primary': r['primary_topic'],
            'final_secondary': secondary_list,
            'source': ('tri_consensus' if r['source'] == 'tri_llm_consensus'
                       else 'review_resolved_v5b'),
        }
        f.write(json.dumps(out, ensure_ascii=False) + '\n')
print(f'Wrote → {dst.name}')
print('Now you can run any analysis/*.py script (run from the repository root).')
