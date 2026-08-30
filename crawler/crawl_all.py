#!/usr/bin/env python3
"""
네이버 지식인 검색 결과를 수집합니다.
kin.naver.com 검색 + 기간 필터(period) + page 파라미터로 URL 수집 후,
개별 페이지 본문 크롤링 + Excel/CSV 내보내기를 수행합니다.

사용법:
    python crawl_all.py --keyword "황반변성"
    python crawl_all.py --keyword "녹내장" --date-from 20250101 --date-to 20250131
    python crawl_all.py --keyword "황반변성" --date-from 20250501 --date-to 20250531 --limit 10
    python crawl_all.py --resume
    python crawl_all.py --fresh --keyword "황반변성" --date-from 20250101 --date-to 20250131
"""

import asyncio
import json
import re
import random
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import quote

from playwright.async_api import async_playwright, TimeoutError as PwTimeout
from bs4 import BeautifulSoup

try:
    from playwright_stealth import Stealth
    _stealth = Stealth()
except ImportError:
    _stealth = None
    print("[WARN] playwright-stealth 미설치. 탐지 위험이 높아질 수 있습니다.")

from crawl_content import parse_question, parse_answers

DATA_DIR = Path(__file__).parent / "data"
URLS_FILE = DATA_DIR / "pw_urls.json"
RAW_DIR = DATA_DIR / "raw"
PROGRESS_FILE = DATA_DIR / "pw_progress.json"
OUTPUT_DIR = DATA_DIR / "output"

DEFAULT_KEYWORD = "황반변성"
# kin.naver.com 검색 URL (period 파라미터로 기간 필터)
KIN_SEARCH_URL = "https://kin.naver.com/search/list.nhn"

MIN_DELAY = 3
MAX_DELAY = 7
MAX_RETRIES = 3
PAGE_TIMEOUT = 30000


def load_progress() -> set[str]:
    if not PROGRESS_FILE.exists():
        return set()
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        return set(json.load(f))


def save_progress(completed_ids: set[str]):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(completed_ids), f)


def save_raw_result(doc_id: str, data: dict):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    filepath = RAW_DIR / f"{doc_id}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _save_urls(results: list[dict]):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(URLS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def generate_weekly_ranges(date_from: str, date_to: str) -> list[tuple[str, str]]:
    """주 단위 날짜 범위 생성. 입력: YYYYMMDD, 출력: (YYYY.MM.DD., YYYY.MM.DD.) period 형식"""
    start = datetime.strptime(date_from, "%Y%m%d")
    end = datetime.strptime(date_to, "%Y%m%d")
    ranges = []
    current = start
    while current <= end:
        range_end = min(current + timedelta(days=6), end)
        s = current.strftime("%Y.%m.%d.")
        e = range_end.strftime("%Y.%m.%d.")
        ranges.append((s, e))
        current = range_end + timedelta(days=1)
    return ranges


def extract_doc_ids_from_page(soup: BeautifulSoup, seen_ids: set, results: list) -> int:
    """kin.naver.com 검색 결과 페이지에서 docId, URL, 제목을 추출."""
    search_list = soup.select_one("ul.basic1")
    if not search_list:
        return 0

    new_count = 0
    for li in search_list.select("li"):
        # dt > a 태그에서 제목 링크 추출
        title_link = li.select_one("dt a[href]")
        if not title_link:
            continue
        href = title_link.get("href", "")
        match = re.search(r"docId=(\d+)", href)
        if not match:
            continue
        doc_id = match.group(1)
        if doc_id in seen_ids:
            continue
        seen_ids.add(doc_id)
        title = title_link.get_text(strip=True)
        if href.startswith("/"):
            href = "https://kin.naver.com" + href
        results.append({"doc_id": doc_id, "url": href, "title": title})
        new_count += 1
    return new_count


async def collect_urls(page, keyword: str, date_from: str = "20020101", date_to: str = None, fresh: bool = False) -> list[dict]:
    """kin.naver.com 검색 + period 기간 필터 + page 파라미터로 URL을 수집합니다."""
    keyword_encoded = quote(keyword)
    if date_to is None:
        date_to = datetime.now().strftime("%Y%m%d")
    results = []
    seen_ids = set()

    # 기존 수집 파일이 있으면 로드 (fresh가 아닌 경우)
    if not fresh and URLS_FILE.exists():
        with open(URLS_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
            for item in existing:
                seen_ids.add(item["doc_id"])
                results.append(item)
        print(f"  기존 URL 파일 로드: {len(results)}건")

    date_ranges = generate_weekly_ranges(date_from, date_to)
    print(f"  수집 기간: {date_from}~{date_to} ({len(date_ranges)}개 주별 범위)")

    for range_start, range_end in date_ranges:
        period = f"{range_start}|{range_end}"
        pg = 1
        empty_count = 0

        while True:
            url = (
                f"{KIN_SEARCH_URL}?sort=none&section=kin"
                f"&query={keyword_encoded}"
                f"&period={quote(period, safe='')}"
                f"&page={pg}"
            )

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)
                await page.wait_for_timeout(random.uniform(1000, 2000))
            except PwTimeout:
                print(f"    [TIMEOUT] {range_start}~{range_end} page={pg}, 재시도...")
                await asyncio.sleep(5)
                continue
            except Exception as e:
                print(f"    [ERROR] {range_start}~{range_end} page={pg}: {e}")
                await asyncio.sleep(5)
                empty_count += 1
                if empty_count >= 3:
                    break
                continue

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")

            # 결과 없음 판별
            if soup.select_one("div.notfound") or not soup.select_one("ul.basic1"):
                break

            new_count = extract_doc_ids_from_page(soup, seen_ids, results)

            if new_count == 0:
                empty_count += 1
                if empty_count >= 2:
                    break
            else:
                empty_count = 0

            pg += 1
            await asyncio.sleep(random.uniform(0.5, 1.5))

        # 주별 저장
        _save_urls(results)
        rs = range_start.replace(".", "")[:8]
        re_ = range_end.replace(".", "")[:8]
        rs_fmt = datetime.strptime(rs, "%Y%m%d").strftime("%Y.%m.%d")
        re_fmt = datetime.strptime(re_, "%Y%m%d").strftime("%m.%d")
        print(f"  [{rs_fmt}~{re_fmt}] 누적 {len(results)}건")

    return results


async def crawl_content(page, urls_data: list[dict], limit: int | None = None, resume: bool = True):
    """수집된 URL의 본문을 크롤링합니다."""
    completed_ids = load_progress() if resume else set()
    remaining = [u for u in urls_data if u["doc_id"] not in completed_ids]
    if limit:
        remaining = remaining[:limit]

    total = len(remaining)
    if total == 0:
        print("  크롤링할 항목이 없습니다.")
        return

    print(f"\n  크롤링 시작: {total}건 (이미 완료: {len(completed_ids)}건)")
    print(f"  예상 소요 시간: {total * (MIN_DELAY + MAX_DELAY) / 2 / 60:.1f}분\n")

    success_count = 0
    fail_count = 0

    for i, item in enumerate(remaining, 1):
        doc_id = item["doc_id"]
        url = item["url"]
        print(f"  [{i}/{total}] {item.get('title', '')[:50]}...")

        result = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)
                await page.wait_for_timeout(2000)
                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")
                question = parse_question(soup)
                answers = parse_answers(soup)

                if not question["title"] and not question["content"]:
                    await page.wait_for_timeout(3000)
                    html = await page.content()
                    soup = BeautifulSoup(html, "html.parser")
                    question = parse_question(soup)
                    answers = parse_answers(soup)

                result = {
                    "url": url,
                    "doc_id": doc_id,
                    "question": question,
                    "answers": answers,
                    "answer_count": len(answers),
                    "crawled_at": datetime.now().isoformat(),
                }
                break
            except PwTimeout:
                print(f"      [TIMEOUT] 시도 {attempt}/{MAX_RETRIES}")
            except Exception as e:
                print(f"      [ERROR] 시도 {attempt}/{MAX_RETRIES}: {e}")

            if attempt < MAX_RETRIES:
                await asyncio.sleep(random.uniform(5, 10))

        if result:
            save_raw_result(doc_id, result)
            completed_ids.add(doc_id)
            success_count += 1
            actual_title = result["question"].get("title", "")
            if actual_title:
                item["title"] = actual_title
            print(f"      [OK] 답변 {result['answer_count']}개")
        else:
            fail_count += 1
            print(f"      [FAIL] 크롤링 실패")

        if i % 10 == 0:
            save_progress(completed_ids)
            print(f"      [진행상황 저장] 성공: {success_count}, 실패: {fail_count}")

        await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

    save_progress(completed_ids)
    _save_urls(urls_data)
    print(f"\n  크롤링 완료! 성공: {success_count}건, 실패: {fail_count}건")


def export_data(keyword: str, urls_data: list[dict] = None):
    """raw JSON 데이터를 Excel로 내보냅니다. urls_data가 있으면 해당 건만 내보냅니다."""
    import pandas as pd
    from openpyxl.styles import Alignment
    from export import flatten_data, clean_illegal_chars, ILLEGAL_CHARS_RE

    if not RAW_DIR.exists():
        print("  raw 디렉토리가 없습니다.")
        return

    # urls_data가 있으면 해당 doc_id만, 없으면 전체
    if urls_data:
        target_ids = {item["doc_id"] for item in urls_data}
    else:
        target_ids = None

    raw_data = []
    for filepath in sorted(RAW_DIR.glob("*.json")):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if target_ids is None or data.get("doc_id") in target_ids:
            raw_data.append(data)

    if not raw_data:
        print("  내보낼 데이터가 없습니다.")
        return

    rows = flatten_data(raw_data)
    df = pd.DataFrame(rows)
    df = clean_illegal_chars(df)

    # Excel 셀 내 줄바꿈: \n → \r\n 변환 (Excel이 인식하는 형식)
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].apply(
            lambda x: x.replace("\r\n", "\n").replace("\n", "\r\n") if isinstance(x, str) else x
        )

    valid_mask = (df["question_title"] != "") | (df["question_content"] != "")
    df = df[valid_mask]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    xlsx_path = OUTPUT_DIR / f"{keyword}_지식인_{timestamp}.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="지식인_크롤링")
        worksheet = writer.sheets["지식인_크롤링"]
        for i, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).fillna("").str.len().max(), len(col))
            col_letter = chr(65 + i) if i < 26 else f"A{chr(65 + i - 26)}"
            worksheet.column_dimensions[col_letter].width = min(max_len + 2, 50)
        for row in worksheet.iter_rows():
            for cell in row:
                cell.alignment = Alignment(wrap_text=True)
    print(f"  Excel 저장: {xlsx_path}")

    print(f"\n  총 {len(df)}건, 답변 포함: {(df['answer_count'] > 0).sum()}건")


async def main_async(keyword: str, limit: int | None, resume: bool, date_from: str = "20020101", date_to: str = None):
    if date_to is None:
        date_to = datetime.now().strftime("%Y%m%d")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="ko-KR",
        )
        page = await context.new_page()
        if _stealth:
            await _stealth.apply_stealth_async(page)

        # Step 1: URL 수집
        print("=" * 60)
        print(f"네이버 지식인 '{keyword}' 크롤러 (kin.naver.com)")
        print("=" * 60)
        print("\n[Step 1/3] URL 수집")
        urls_data = await collect_urls(page, keyword=keyword, date_from=date_from, date_to=date_to, fresh=not resume)
        print(f"  총 {len(urls_data)}건 수집 완료")

        # Step 2: 본문 크롤링
        print("\n[Step 2/3] 본문 크롤링")
        await crawl_content(page, urls_data, limit=limit, resume=resume)

        await browser.close()

    # Step 3: 내보내기
    print("\n[Step 3/3] Excel 내보내기")
    export_data(keyword, urls_data)

    print("\n" + "=" * 60)
    print("완료! data/output/ 디렉토리를 확인해주세요.")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="네이버 지식인 크롤러 (kin.naver.com)")
    parser.add_argument("--keyword", type=str, default=DEFAULT_KEYWORD, help=f"검색 키워드 (기본: {DEFAULT_KEYWORD})")
    parser.add_argument("--limit", type=int, default=None, help="본문 크롤링 최대 건수")
    parser.add_argument("--resume", action="store_true", default=True, help="이전 진행 상황에서 재개")
    parser.add_argument("--fresh", action="store_true", help="처음부터 다시 크롤링")
    parser.add_argument("--date-from", type=str, default="20020101", help="수집 시작일 (YYYYMMDD)")
    parser.add_argument("--date-to", type=str, default=datetime.now().strftime("%Y%m%d"), help="수집 종료일 (YYYYMMDD, 기본: 오늘)")
    args = parser.parse_args()

    resume = not args.fresh
    asyncio.run(main_async(keyword=args.keyword, limit=args.limit, resume=resume, date_from=args.date_from, date_to=args.date_to))


if __name__ == "__main__":
    main()
