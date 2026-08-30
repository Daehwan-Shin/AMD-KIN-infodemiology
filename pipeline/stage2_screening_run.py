"""
Stage 2: AMD screening via the Anthropic API
Released screening codebook v1.0 (frozen G1-G7 rule set)

Usage:
    # Pilot
    python pipeline/stage2_screening_run.py --input _pilot_sample_50.jsonl --output _stage2_pilot_opus.jsonl --model opus --concurrency 5

    # Full run (3,848 items)
    python pipeline/stage2_screening_run.py --input _stage1_candidates.jsonl --output _stage2_full.jsonl --model opus --concurrency 8
"""
import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv

# ---------- Configuration ----------
MODELS = {
    "sonnet": "claude-sonnet-4-6",
    "opus":   "claude-opus-4-7",
    "haiku":  "claude-haiku-4-5-20251001",
}

# Pricing per million tokens (USD) — update if Anthropic changes pricing
PRICING = {
    "claude-sonnet-4-6": {"input": 3.0,  "output": 15.0, "cache_write": 3.75,  "cache_read": 0.30},
    "claude-opus-4-7":   {"input": 15.0, "output": 75.0, "cache_write": 18.75, "cache_read": 1.50},
    "claude-haiku-4-5-20251001": {"input": 1.0, "output": 5.0, "cache_write": 1.25, "cache_read": 0.10},
}

SCRIPT_DIR = Path(__file__).parent
SYSTEM_PROMPT_PATH = SCRIPT_DIR.parent / "codebook" / "stage2_screening_codebook_v1.0.md"

VALID_STATUSES = {"Include_strict_AMD", "Review_needed", "Exclude_non_AMD", "Unclear"}

# ---------- Helpers ----------
def load_jsonl(path: Path) -> list[dict]:
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def append_jsonl(path: Path, record: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_completed(path: Path) -> set[str]:
    """Return set of validation_ids already processed (for resume)."""
    completed = set()
    if not path.exists():
        return completed
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line.strip())
                vid = rec.get("validation_id") or rec.get("pilot_id") or rec.get("doc_id")
                if vid:
                    completed.add(vid)
            except Exception:
                continue
    return completed


def get_item_id(item: dict) -> str:
    """Return the best available identifier."""
    return (
        item.get("pilot_id")
        or item.get("validation_id")
        or item.get("doc_id")
        or str(item.get("row_index", ""))
    )


def make_user_message(item: dict) -> str:
    title = (item.get("question_title") or "").strip()
    content = (item.get("question_content") or "").strip()
    return f"질문 제목: {title}\n\n질문 본문:\n{content}"


def safe_parse_json(text: str) -> dict | None:
    """Extract JSON object from model output even if surrounded by extra text."""
    text = text.strip()
    if text.startswith("```"):
        # remove code fences
        text = text.split("```", 2)[1] if "```" in text else text
        if text.startswith("json"):
            text = text[4:]
        text = text.strip("` \n")
    # find first { and last }
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    snippet = text[start:end + 1]
    try:
        return json.loads(snippet)
    except json.JSONDecodeError:
        return None


def validate_response(parsed: dict) -> bool:
    if not isinstance(parsed, dict):
        return False
    if "AMD_status" not in parsed or "reason" not in parsed:
        return False
    if parsed["AMD_status"] not in VALID_STATUSES:
        return False
    return True


# ---------- Main classification ----------
async def classify_one(
    client: anthropic.AsyncAnthropic,
    item: dict,
    system_prompt: str,
    model: str,
    semaphore: asyncio.Semaphore,
    max_retries: int = 3,
) -> dict:
    item_id = get_item_id(item)
    user_msg = make_user_message(item)

    async with semaphore:
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                resp = await client.messages.create(
                    model=model,
                    max_tokens=400,
                    system=[
                        {
                            "type": "text",
                            "text": system_prompt,
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                    messages=[{"role": "user", "content": user_msg}],
                )
                raw_text = "".join(
                    block.text for block in resp.content if block.type == "text"
                )
                parsed = safe_parse_json(raw_text)
                if parsed is None or not validate_response(parsed):
                    raise ValueError(f"Invalid JSON or schema: {raw_text[:200]}")

                usage = resp.usage
                return {
                    "id": item_id,
                    "AMD_status": parsed["AMD_status"],
                    "reason": parsed["reason"],
                    "raw_output": raw_text,
                    "model": model,
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                    "cache_creation_input_tokens": getattr(
                        usage, "cache_creation_input_tokens", 0
                    ) or 0,
                    "cache_read_input_tokens": getattr(
                        usage, "cache_read_input_tokens", 0
                    ) or 0,
                    "attempt": attempt,
                    "ok": True,
                }
            except (anthropic.RateLimitError, anthropic.APIStatusError) as e:
                last_error = str(e)
                wait = 2 ** attempt + 1
                print(
                    f"  [{item_id}] retry {attempt}/{max_retries} after {wait}s: {e}",
                    file=sys.stderr,
                )
                await asyncio.sleep(wait)
            except Exception as e:
                last_error = str(e)
                print(
                    f"  [{item_id}] error attempt {attempt}/{max_retries}: {e}",
                    file=sys.stderr,
                )
                await asyncio.sleep(2)

        return {
            "id": item_id,
            "AMD_status": None,
            "reason": None,
            "raw_output": None,
            "model": model,
            "ok": False,
            "error": last_error,
            "attempt": max_retries,
        }


def compute_cost(records: list[dict], model: str) -> dict:
    rates = PRICING[model]
    in_tok = sum(r.get("input_tokens", 0) for r in records if r.get("ok"))
    out_tok = sum(r.get("output_tokens", 0) for r in records if r.get("ok"))
    cache_w = sum(r.get("cache_creation_input_tokens", 0) for r in records if r.get("ok"))
    cache_r = sum(r.get("cache_read_input_tokens", 0) for r in records if r.get("ok"))
    cost = (
        in_tok / 1_000_000 * rates["input"]
        + out_tok / 1_000_000 * rates["output"]
        + cache_w / 1_000_000 * rates["cache_write"]
        + cache_r / 1_000_000 * rates["cache_read"]
    )
    return {
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "cache_write_tokens": cache_w,
        "cache_read_tokens": cache_r,
        "total_cost_usd": round(cost, 4),
    }


async def main_async(args):
    load_dotenv()
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.", file=sys.stderr)
        print("  .env 파일에 ANTHROPIC_API_KEY=sk-ant-... 를 추가하세요.", file=sys.stderr)
        sys.exit(1)

    model = MODELS[args.model]
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"ERROR: 입력 파일 없음: {input_path}", file=sys.stderr)
        sys.exit(1)

    system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    items = load_jsonl(input_path)
    print(f"입력: {len(items)} items from {input_path}")
    print(f"모델: {model}")
    print(f"출력: {output_path}")
    print(f"동시 요청: {args.concurrency}")

    # Resume support
    completed = load_completed(output_path) if args.resume else set()
    if completed:
        print(f"  이미 처리됨: {len(completed)}건 (--resume)")
    remaining = [it for it in items if get_item_id(it) not in completed]
    print(f"  처리 대상: {len(remaining)}건")

    if not remaining:
        print("처리할 항목이 없습니다.")
        return

    client = anthropic.AsyncAnthropic()
    semaphore = asyncio.Semaphore(args.concurrency)

    if args.fresh and output_path.exists():
        output_path.unlink()

    start = time.time()
    processed = 0
    failed = 0
    all_records = []

    async def task(it):
        nonlocal processed, failed
        rec = await classify_one(client, it, system_prompt, model, semaphore)
        # carry over original metadata for traceability
        rec["pilot_id_or_id"] = get_item_id(it)
        rec["question_title"] = it.get("question_title", "")
        append_jsonl(output_path, rec)
        all_records.append(rec)
        if rec.get("ok"):
            processed += 1
        else:
            failed += 1
        if (processed + failed) % 25 == 0:
            elapsed = time.time() - start
            rate = (processed + failed) / max(elapsed, 1e-9)
            eta = (len(remaining) - processed - failed) / max(rate, 1e-9)
            print(
                f"  진행: {processed + failed}/{len(remaining)} "
                f"(성공 {processed}, 실패 {failed}) "
                f"속도 {rate:.1f}/s, ETA {eta/60:.1f}분"
            )

    await asyncio.gather(*[task(it) for it in remaining])

    elapsed = time.time() - start
    cost = compute_cost(all_records, model)

    print()
    print("=" * 60)
    print("Stage 2 완료")
    print("=" * 60)
    print(f"  처리 시간: {elapsed/60:.1f}분")
    print(f"  성공: {processed}, 실패: {failed}")
    print(f"  입력 토큰: {cost['input_tokens']:,}")
    print(f"  출력 토큰: {cost['output_tokens']:,}")
    print(f"  캐시 쓰기 토큰: {cost['cache_write_tokens']:,}")
    print(f"  캐시 읽기 토큰: {cost['cache_read_tokens']:,}")
    print(f"  비용: ${cost['total_cost_usd']}")
    print(f"  결과 파일: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Stage 2: AMD Screening via Anthropic API")
    parser.add_argument("--input", required=True, help="입력 JSONL 파일 (Stage 1 candidates or pilot)")
    parser.add_argument("--output", required=True, help="출력 JSONL 파일 (결과 + 토큰 사용량)")
    parser.add_argument("--model", choices=list(MODELS.keys()), default="sonnet",
                        help="사용 모델 (default: sonnet)")
    parser.add_argument("--concurrency", type=int, default=5,
                        help="동시 API 요청 수 (default: 5)")
    parser.add_argument("--resume", action="store_true",
                        help="기존 결과 파일에 이어쓰기 (이미 처리한 ID 건너뜀)")
    parser.add_argument("--fresh", action="store_true",
                        help="기존 출력 파일 삭제 후 처음부터")
    args = parser.parse_args()

    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
