#!/usr/bin/env python3
"""
Playwright + stealth 모드로 네이버 지식인 개별 페이지를 크롤링합니다.
collect_urls.py로 수집한 URL 목록(urls.json)을 입력으로 받습니다.

사용법:
    python crawl_content.py
    python crawl_content.py --limit 50
    python crawl_content.py --resume
"""

import asyncio
import json
import os
import random
import re
import sys
import argparse
import time
from pathlib import Path
from datetime import datetime

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PwTimeout

try:
    from playwright_stealth import Stealth
    _stealth = Stealth()
except ImportError:
    _stealth = None
    print("[WARN] playwright-stealth 미설치. 탐지 위험이 높아질 수 있습니다.")

DATA_DIR = Path(__file__).parent / "data"
URLS_FILE = DATA_DIR / "urls.json"
RAW_DIR = DATA_DIR / "raw"
PROGRESS_FILE = DATA_DIR / "progress.json"

# 크롤링 설정
MIN_DELAY = 3  # 최소 대기 시간 (초)
MAX_DELAY = 7  # 최대 대기 시간 (초)
MAX_RETRIES = 3
PAGE_TIMEOUT = 30000  # 30초


def load_urls() -> list[dict]:
    """urls.json에서 URL 목록 로드."""
    if not URLS_FILE.exists():
        print(f"ERROR: {URLS_FILE} 파일이 없습니다. collect_urls.py를 먼저 실행해주세요.")
        sys.exit(1)
    with open(URLS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_progress() -> set[str]:
    """이미 크롤링한 doc_id 목록 로드 (재개용)."""
    if not PROGRESS_FILE.exists():
        return set()
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        return set(json.load(f))


def save_progress(completed_ids: set[str]):
    """진행 상황 저장."""
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(completed_ids), f)


def save_raw_result(doc_id: str, data: dict):
    """개별 크롤링 결과를 JSON으로 저장."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    filepath = RAW_DIR / f"{doc_id}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _is_open100(soup: BeautifulSoup) -> bool:
    """open100 페이지인지 판별."""
    return soup.select_one("div.end_question") is not None and soup.select_one("div.endTitleSection") is None


def _parse_open100(soup: BeautifulSoup) -> dict:
    """open100/detail.naver 페이지 파싱."""
    question = {
        "title": "",
        "content": "",
        "date": "",
        "views": 0,
        "category": "",
        "author": "",
    }

    # 제목: <title> 태그에서 " : 지식iN" 제거
    title_tag = soup.select_one("title")
    if title_tag:
        t = title_tag.get_text(strip=True)
        t = re.sub(r"\s*:\s*지식iN\s*$", "", t)
        question["title"] = t

    # 본문: div._endContents (부모: div.end_question)
    content_el = soup.select_one("div.end_question div._endContents")
    if content_el:
        question["content"] = content_el.get_text("\n", strip=True)

    # 날짜 + 조회수 + 작성자: #content 첫 div 텍스트에서 추출
    content_div = soup.select_one("#content > div")
    if content_div:
        text = content_div.get_text()
        # 날짜
        date_match = re.search(r"(\d{4}\.\d{2}\.\d{2})", text)
        if date_match:
            question["date"] = date_match.group(1)
        # 조회수
        views_match = re.search(r"조회\s*([\d,]+)", text)
        if views_match:
            question["views"] = int(views_match.group(1).replace(",", ""))
        # 작성자: 날짜 바로 앞의 텍스트 (ID 패턴)
        author_match = re.search(r"\n([a-zA-Z0-9_*]+(?:\*+)?)\s*\n\s*\d{4}\.\d{2}\.\d{2}", text)
        if author_match:
            question["author"] = author_match.group(1).strip()

    return question


def parse_question(soup: BeautifulSoup) -> dict:
    """질문 영역 파싱. qna와 open100 페이지 모두 지원."""
    # open100 페이지 판별
    if _is_open100(soup):
        return _parse_open100(soup)

    question = {
        "title": "",
        "content": "",
        "date": "",
        "views": 0,
        "category": "",
        "author": "",
    }

    # 질문 제목: endTitleSection 내부 텍스트에서 "질문" 접두어 제거
    title_el = soup.select_one("div.endTitleSection")
    if title_el:
        title_text = title_el.get_text(strip=True)
        # "질문" 접두어 제거
        if title_text.startswith("질문"):
            title_text = title_text[2:].strip()
        question["title"] = title_text
    else:
        # fallback: <title> 태그에서 " : 지식iN" 제거
        title_tag = soup.select_one("title")
        if title_tag:
            t = title_tag.get_text(strip=True)
            t = re.sub(r"\s*:\s*지식iN\s*$", "", t)
            question["title"] = t

    # 질문 본문: questionDetail 영역
    content_el = soup.select_one("div.questionDetail")
    if content_el:
        question["content"] = content_el.get_text("\n", strip=True)

    # 작성일 + 조회수: div.userInfo 내 span.infoItem 에서 추출
    info_items = soup.select("div.userInfo span.infoItem")
    for item in info_items:
        text = item.get_text(strip=True)
        # 작성일
        date_match = re.search(r"(\d{4}\.\d{2}\.\d{2})", text)
        if "작성일" in text and date_match:
            question["date"] = date_match.group(1)
        # 조회수
        if "조회수" in text:
            nums = re.findall(r"[\d,]+", text)
            if nums:
                question["views"] = int(nums[0].replace(",", ""))

    # 작성자: div.userInfo 내 name_area
    author_el = soup.select_one("div.userInfo div.name_area, div.userInfo strong.name")
    if author_el:
        question["author"] = author_el.get_text(strip=True)

    # 카테고리/태그: div.tagList 내 a.tag
    tags = []
    for tag_el in soup.select("div.tagList a.tag"):
        tag_text = tag_el.get_text(strip=True).replace("새 창", "").strip()
        if tag_text:
            tags.append(tag_text)
    question["category"] = ", ".join(tags)

    return question


def parse_answers(soup: BeautifulSoup) -> list[dict]:
    """답변 영역 파싱."""
    answers = []

    # 답변 컨테이너: answerArea._contentWrap._answer
    answer_containers = soup.select("div.answerArea._contentWrap._answer")

    for container in answer_containers:
        answer = {
            "content": "",
            "author": "",
            "date": "",
            "is_adopted": False,
        }

        # "삭제된 답변" 건너뛰기
        if "삭제된 답변" in container.get_text()[:50]:
            continue

        # 답변 본문: answerDetail._endContents
        content_el = container.select_one("div.answerDetail._endContents")
        if content_el:
            answer["content"] = content_el.get_text("\n", strip=True)

        # 작성자: name_area 클래스 (div 또는 strong)
        author_el = container.select_one("div.name_area, strong.name")
        if author_el:
            answer["author"] = author_el.get_text(strip=True)

        # 작성일: p.answerDate
        date_el = container.select_one("p.answerDate")
        if date_el:
            date_match = re.search(r"\d{4}\.\d{2}\.\d{2}\.", date_el.get_text())
            if date_match:
                answer["date"] = date_match.group()

        # 채택 여부: answerInfo 영역 내 "채택" 텍스트
        info_el = container.select_one("div.answerInfo")
        if info_el and "채택" in info_el.get_text():
            answer["is_adopted"] = True

        # 빈 답변 필터링
        if answer["content"]:
            answers.append(answer)

    return answers


async def crawl_single_page(page, url: str) -> dict | None:
    """단일 페이지 크롤링."""
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)
        # JS 렌더링 대기
        await page.wait_for_timeout(2000)

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        question = parse_question(soup)
        answers = parse_answers(soup)

        # 최소한 제목이나 내용이 있어야 유효
        if not question["title"] and not question["content"]:
            # 더 기다려본 후 재시도
            await page.wait_for_timeout(3000)
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            question = parse_question(soup)
            answers = parse_answers(soup)

        return {
            "url": url,
            "question": question,
            "answers": answers,
            "answer_count": len(answers),
            "crawled_at": datetime.now().isoformat(),
        }

    except PwTimeout:
        print(f"    [TIMEOUT] {url}")
        return None
    except Exception as e:
        print(f"    [ERROR] {url}: {e}")
        return None


async def crawl_all(urls_data: list[dict], limit: int | None = None, resume: bool = True):
    """전체 URL 목록을 크롤링합니다."""
    completed_ids = load_progress() if resume else set()

    # 이미 완료된 항목 필터링
    remaining = [u for u in urls_data if u["doc_id"] not in completed_ids]
    if limit:
        remaining = remaining[:limit]

    total = len(remaining)
    if total == 0:
        print("크롤링할 항목이 없습니다. (모두 완료되었거나 URL이 비어있음)")
        return

    print(f"\n크롤링 시작: {total}건 (이미 완료: {len(completed_ids)}건)")
    print(f"예상 소요 시간: {total * (MIN_DELAY + MAX_DELAY) / 2 / 60:.1f}분\n")

    success_count = 0
    fail_count = 0

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
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="ko-KR",
        )
        page = await context.new_page()

        # stealth 모드 적용
        if _stealth:
            await _stealth.apply_stealth_async(page)

        for i, item in enumerate(remaining, 1):
            doc_id = item["doc_id"]
            url = item["url"]
            print(f"[{i}/{total}] {item.get('title', '')[:50]}...")

            result = None
            for attempt in range(1, MAX_RETRIES + 1):
                result = await crawl_single_page(page, url)
                if result:
                    break
                if attempt < MAX_RETRIES:
                    wait = random.uniform(5, 10)
                    print(f"    재시도 {attempt}/{MAX_RETRIES} ({wait:.1f}초 대기)")
                    await asyncio.sleep(wait)

            if result:
                save_raw_result(doc_id, result)
                completed_ids.add(doc_id)
                success_count += 1
                q = result["question"]
                print(f"    ✓ 질문: {q['title'][:40]} | 답변: {result['answer_count']}개")
            else:
                fail_count += 1
                print(f"    ✗ 크롤링 실패")

            # 진행 상황 주기적 저장 (10건마다)
            if i % 10 == 0:
                save_progress(completed_ids)
                print(f"    [진행상황 저장] 성공: {success_count}, 실패: {fail_count}")

            # 랜덤 대기
            delay = random.uniform(MIN_DELAY, MAX_DELAY)
            await asyncio.sleep(delay)

        await browser.close()

    # 최종 진행 상황 저장
    save_progress(completed_ids)

    print(f"\n{'=' * 60}")
    print(f"크롤링 완료!")
    print(f"  성공: {success_count}건")
    print(f"  실패: {fail_count}건")
    print(f"  저장 위치: {RAW_DIR}")
    print(f"{'=' * 60}")


def main():
    parser = argparse.ArgumentParser(description="네이버 지식인 본문 크롤러")
    parser.add_argument("--limit", type=int, default=None, help="크롤링할 최대 건수")
    parser.add_argument("--resume", action="store_true", default=True, help="이전 진행 상황에서 재개")
    parser.add_argument("--fresh", action="store_true", help="처음부터 다시 크롤링")
    args = parser.parse_args()

    resume = not args.fresh
    urls_data = load_urls()
    print(f"URL 파일 로드: {len(urls_data)}건")

    asyncio.run(crawl_all(urls_data, limit=args.limit, resume=resume))


if __name__ == "__main__":
    main()
