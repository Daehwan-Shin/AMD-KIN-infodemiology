#!/usr/bin/env python3
"""
네이버 검색 Open API를 사용하여 지식인에서 '황반변성' 관련 URL을 수집합니다.

사용법:
    python collect_urls.py
    python collect_urls.py --keyword "황반변성 치료"
    python collect_urls.py --start-date 2020-01-01 --end-date 2024-12-31
"""

import os
import sys
import json
import time
import argparse
import re
from datetime import datetime, timedelta
from urllib.parse import quote, unquote
from pathlib import Path

import requests
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv(Path(__file__).parent / ".env")

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
API_URL = "https://openapi.naver.com/v1/search/kin.json"

DATA_DIR = Path(__file__).parent / "data"
URLS_FILE = DATA_DIR / "urls.json"


def search_kin(keyword: str, start: int = 1, display: int = 100, sort: str = "sim") -> dict | None:
    """네이버 지식인 검색 API 호출."""
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {
        "query": keyword,
        "display": display,
        "start": start,
        "sort": sort,  # sim(정확도), date(날짜)
    }

    try:
        resp = requests.get(API_URL, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"  [ERROR] API 호출 실패 (start={start}): {e}")
        return None


def extract_kin_id(link: str) -> str | None:
    """지식인 URL에서 고유 ID를 추출합니다."""
    # https://kin.naver.com/qna/detail.naver?d1id=...&dirId=...&docId=123456
    match = re.search(r"docId=(\d+)", link)
    if match:
        return match.group(1)
    # 모바일 URL 등 다른 형태
    match = re.search(r"/(\d+)(?:\?|$)", link)
    if match:
        return match.group(1)
    return link  # fallback: URL 자체를 ID로 사용


def collect_urls_for_keyword(keyword: str, max_results: int = 1000, sort: str = "sim") -> list[dict]:
    """단일 키워드로 최대 max_results개의 URL을 수집합니다."""
    results = []
    seen_ids = set()

    # API 제한: start는 1~1000, display는 최대 100
    for start in range(1, min(max_results, 1000) + 1, 100):
        display = min(100, max_results - start + 1)
        print(f"  검색 중... start={start}, display={display}")

        data = search_kin(keyword, start=start, display=display, sort=sort)
        if not data or "items" not in data:
            break

        items = data["items"]
        if not items:
            print(f"  더 이상 결과가 없습니다. (total={data.get('total', 0)})")
            break

        for item in items:
            link = item.get("link", "")
            doc_id = extract_kin_id(link)

            if doc_id in seen_ids:
                continue
            seen_ids.add(doc_id)

            # HTML 태그 제거
            title = re.sub(r"<[^>]+>", "", item.get("title", ""))
            description = re.sub(r"<[^>]+>", "", item.get("description", ""))

            results.append({
                "doc_id": doc_id,
                "url": link,
                "title": title,
                "description": description,
            })

        # API rate limit 존중
        time.sleep(0.2)

    return results


def collect_single_keyword(keyword: str) -> list[dict]:
    """
    단일 키워드로 정확도순 + 최신순 검색하여 URL을 수집합니다.
    네이버 API 제한: start 1~1000, 키워드당 최대 1,000건.
    """
    all_results = []
    seen_ids = set()

    # 정확도순 검색
    print(f"\n[1/2] 정확도순 검색: '{keyword}'")
    sim_results = collect_urls_for_keyword(keyword, max_results=1000)
    for r in sim_results:
        if r["doc_id"] not in seen_ids:
            seen_ids.add(r["doc_id"])
            all_results.append(r)
    print(f"  → {len(sim_results)}건 수집 (누적: {len(all_results)}건)")

    # 최신순 검색 (sort=date)
    print(f"\n[2/2] 최신순 검색: '{keyword}'")
    date_results = collect_urls_for_keyword(keyword, max_results=1000, sort="date")
    new_count = 0
    for r in date_results:
        if r["doc_id"] not in seen_ids:
            seen_ids.add(r["doc_id"])
            all_results.append(r)
            new_count += 1
    print(f"  → {len(date_results)}건 수집, 신규 {new_count}건 (누적: {len(all_results)}건)")

    return all_results


def save_urls(results: list[dict], filepath: Path):
    """수집된 URL 목록을 JSON으로 저장합니다."""
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # 기존 파일이 있으면 병합
    existing = []
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            existing = json.load(f)

    existing_ids = {r["doc_id"] for r in existing}
    new_results = [r for r in results if r["doc_id"] not in existing_ids]

    merged = existing + new_results

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"\n저장 완료: {filepath}")
    print(f"  기존: {len(existing)}건, 신규: {len(new_results)}건, 총: {len(merged)}건")


def main():
    parser = argparse.ArgumentParser(description="네이버 지식인 URL 수집기")
    parser.add_argument("--keyword", default="황반변성", help="검색 키워드 (기본: 황반변성)")
    parser.add_argument("--start-date", default="2015-01-01", help="검색 시작일 (기본: 2015-01-01)")
    parser.add_argument("--end-date", default=datetime.now().strftime("%Y-%m-%d"), help="검색 종료일 (기본: 오늘)")
    parser.add_argument("--output", default=str(URLS_FILE), help="출력 파일 경로")
    args = parser.parse_args()

    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        print("ERROR: .env 파일에 NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET을 설정해주세요.")
        print("  cp .env.example .env  # 그 후 키 입력")
        sys.exit(1)

    print("=" * 60)
    print(f"네이버 지식인 URL 수집기")
    print(f"  키워드: {args.keyword}")
    print(f"  기간: {args.start_date} ~ {args.end_date}")
    print("=" * 60)

    results = collect_single_keyword(args.keyword)
    save_urls(results, Path(args.output))

    print(f"\n총 {len(results)}건의 URL을 수집했습니다.")


if __name__ == "__main__":
    main()
