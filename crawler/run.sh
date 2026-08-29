#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "========================================="
echo " 네이버 지식인 '황반변성' 크롤러"
echo "========================================="

# .env 확인
if [ ! -f .env ]; then
    echo "ERROR: .env 파일이 없습니다."
    echo "  cp .env.example .env"
    echo "  그 후 네이버 API 키를 입력해주세요."
    exit 1
fi

# Step 1: URL 수집
echo ""
echo "[Step 1/3] URL 수집 (네이버 검색 API)"
python3 collect_urls.py

# Step 2: 본문 크롤링
echo ""
echo "[Step 2/3] 본문 크롤링 (Playwright)"
python3 crawl_content.py

# Step 3: Excel/CSV 내보내기
echo ""
echo "[Step 3/3] Excel/CSV 내보내기"
python3 export.py

echo ""
echo "완료! data/output/ 디렉토리를 확인해주세요."
