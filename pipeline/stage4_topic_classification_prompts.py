"""Generate Codex prompts for topic classification (chunks of 512 items each)."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

TPL = """You are a retina specialist doing TOPIC classification of strict-AMD Naver Knowledge-iN questions, applying Topic Codebook v1.0 (9 categories C1-C9, multi-label). This is an INDEPENDENT second-annotator pass for inter-LLM reliability — classify solely by the codebook, do not guess prior labels.

YOUR TASK
1. Read the topic codebook: codebook/stage4_topic_codebook_v1.0.md (or the *_EN.md reference version)
2. Read the {N} items: _stage4_chunk_{CK}.jsonl (each line: id, question_title, question_content)
3. For EACH item assign primary_topic (one C-code C1-C9) + secondary_topics (0-3 C-codes) per the codebook tiebreakers.
4. Write all {N} results as JSONL to: _stage4_codex_chunk_{CK}.jsonl

OUTPUT FORMAT (one line per item, original order)
{{"id":"<id>","primary_topic":"C#","secondary_topics":["C#",...],"reason":"<one short Korean sentence>"}}

RULES
- primary_topic exactly one of C1..C9. secondary_topics list (may be []).
- Apply codebook tiebreakers. Most posts 0-2 secondary; do not over-tag.
- Treat each item independently. Process in batches, write incrementally.

DELIVERABLE
_stage4_codex_chunk_{CK}.jsonl must have exactly {N} valid JSONL lines.
When done report total lines and primary_topic distribution (C1..C9).
"""
for i in range(1, 5):
    n = 512
    with open(f'_stage4_codex_prompt_chunk_{i}.txt', 'w', encoding='utf-8') as f:
        f.write(TPL.replace('{CK}', str(i)).replace('{N}', str(n)))
    print(f'_stage4_codex_prompt_chunk_{i}.txt 작성')
