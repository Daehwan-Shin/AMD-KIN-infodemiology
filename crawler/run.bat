@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo =========================================
echo  네이버 지식인 '황반변성' 크롤러
echo =========================================

REM .env 확인
if not exist .env (
    echo ERROR: .env 파일이 없습니다.
    echo   copy .env.example .env
    echo   그 후 네이버 API 키를 입력해주세요.
    pause
    exit /b 1
)

REM Step 1: URL 수집
echo.
echo [Step 1/3] URL 수집 (네이버 검색 API)
python collect_urls.py
if errorlevel 1 (
    echo URL 수집 실패
    pause
    exit /b 1
)

REM Step 2: 본문 크롤링
echo.
echo [Step 2/3] 본문 크롤링 (Playwright)
python crawl_content.py
if errorlevel 1 (
    echo 본문 크롤링 실패
    pause
    exit /b 1
)

REM Step 3: Excel/CSV 내보내기
echo.
echo [Step 3/3] Excel/CSV 내보내기
python export.py
if errorlevel 1 (
    echo 내보내기 실패
    pause
    exit /b 1
)

echo.
echo 완료! data\output\ 디렉토리를 확인해주세요.
pause
