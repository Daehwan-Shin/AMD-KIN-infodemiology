#!/usr/bin/env python3
"""
네이버 지식인 '황반변성' 검색 결과 URL 건수를 월별로 분석합니다.
search.naver.com 무한스크롤 API를 활용합니다.

사용법:
    python count_urls.py
    python count_urls.py --date-from 20200101 --date-to 20261231
    python count_urls.py --date-from 20250101 --date-to 20250331
"""

import asyncio
import json
import re
import argparse
from datetime import datetime, timedelta
from urllib.parse import quote

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

DEFAULT_KEYWORD = "황반변성"
SEARCH_BASE = "https://search.naver.com/search.naver"


def generate_monthly_ranges(date_from: str, date_to: str) -> list[tuple[str, str]]:
    start = datetime.strptime(date_from, "%Y%m%d")
    end = datetime.strptime(date_to, "%Y%m%d")
    ranges = []
    current = start
    while current <= end:
        month_end = (current.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        range_end = min(month_end, end)
        ranges.append((current.strftime("%Y%m%d"), range_end.strftime("%Y%m%d")))
        current = range_end + timedelta(days=1)
    return ranges


def extract_doc_ids(html_str: str, seen: set) -> int:
    soup = BeautifulSoup(html_str, "html.parser")
    n = 0
    for a in soup.select('a[href*="detail.naver"][href*="docId"]'):
        href = a.get("href", "")
        if "answerNo" in href or "profileLink" in href:
            continue
        m = re.search(r"docId=(\d+)", href)
        if m and m.group(1) not in seen:
            seen.add(m.group(1))
            n += 1
    return n


async def count_period(page, keyword_encoded: str, start: str, end: str) -> int:
    seen = set()
    nso = f"so:r,p:from{start}to{end}"
    url = f"{SEARCH_BASE}?ssc=tab.kin.kqna&query={keyword_encoded}&sm=tab_opt&nso={nso}"

    try:
        await page.goto(url, wait_until="networkidle", timeout=15000)
        await page.wait_for_timeout(2000)
    except Exception:
        return 0

    html = await page.content()
    soup = BeautifulSoup(html, "html.parser")
    container = soup.select_one(".fds-kin-item-list-tab")
    if not container:
        return 0
    extract_doc_ids(str(container), seen)

    api_responses = []

    async def capture(response):
        if "s.search.naver.com/p/kin" in response.url:
            try:
                api_responses.append(await response.text())
            except Exception:
                pass

    page.on("response", capture)

    empty = 0
    while empty < 3:
        api_responses.clear()
        await page.mouse.move(500, 500)
        for _ in range(5):
            await page.mouse.wheel(0, 800)
            await page.wait_for_timeout(200)
        await page.wait_for_timeout(2000)

        if not api_responses:
            empty += 1
            continue

        batch_new = 0
        for resp_text in api_responses:
            try:
                data = json.loads(resp_text)
                html_chunk = data.get("collection", [{}])[0].get("html", "")
                batch_new += extract_doc_ids(html_chunk, seen)
            except (json.JSONDecodeError, IndexError, KeyError):
                pass

        if batch_new == 0:
            empty += 1
        else:
            empty = 0

    page.remove_listener("response", capture)
    return len(seen)


async def main_async(keyword: str, date_from: str, date_to: str):
    keyword_encoded = quote(keyword)
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

        ranges = generate_monthly_ranges(date_from, date_to)

        print("=" * 50, flush=True)
        print(f"  '{keyword}' 월별 URL 건수 분석", flush=True)
        print(f"  기간: {date_from} ~ {date_to} ({len(ranges)}개월)", flush=True)
        print("=" * 50, flush=True)

        total = 0
        yearly_totals = {}

        for i, (rs, re_) in enumerate(ranges):
            count = await count_period(page, keyword_encoded, rs, re_)
            year = rs[:4]
            month = rs[4:6]
            yearly_totals[year] = yearly_totals.get(year, 0) + count
            total += count

            if count > 0:
                print(f"  {year}.{month}: {count:>5}건  (누적: {total})", flush=True)

            if (i + 1) % 12 == 0 or i == len(ranges) - 1:
                cur_year = rs[:4]
                if yearly_totals.get(cur_year, 0) > 0:
                    print(f"  --- {cur_year}년 소계: {yearly_totals[cur_year]}건 ---", flush=True)

        print(f"\n{'=' * 50}", flush=True)
        print("  연도별 합계:", flush=True)
        for year in sorted(yearly_totals.keys()):
            if yearly_totals[year] > 0:
                print(f"    {year}: {yearly_totals[year]:>5}건", flush=True)
        print(f"\n  총합: {total}건", flush=True)
        print(f"{'=' * 50}", flush=True)

        await browser.close()


def main():
    parser = argparse.ArgumentParser(
        description="네이버 지식인 월별 URL 건수 분석"
    )
    parser.add_argument(
        "--keyword", type=str, default=DEFAULT_KEYWORD,
        help=f"검색 키워드 (기본: {DEFAULT_KEYWORD})"
    )
    parser.add_argument(
        "--date-from", type=str, default="20020101",
        help="분석 시작일 (YYYYMMDD, 기본: 20020101)"
    )
    parser.add_argument(
        "--date-to", type=str, default=datetime.now().strftime("%Y%m%d"),
        help="분석 종료일 (YYYYMMDD, 기본: 오늘)"
    )
    args = parser.parse_args()
    asyncio.run(main_async(keyword=args.keyword, date_from=args.date_from, date_to=args.date_to))


if __name__ == "__main__":
    main()
