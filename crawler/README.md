# Naver Knowledge-iN crawler

This folder documents the browser/API collection workflow used for Naver Knowledge-iN.
It is provided for transparency, not as a guarantee that a later live run will return the
same search index or thread set.

## Contents

- `crawl_all.py`: browser-based URL collection, content crawling, and export workflow
- `collect_urls.py`: optional Naver Search API URL collection
- `crawl_content.py`: question and captured-answer extraction
- `export.py`: Excel export
- `count_urls.py`: URL-count helper
- `사용가이드.txt`: Korean usage guide

## Setup

```bash
cd crawler
pip install -r requirements.txt
playwright install chromium
```

For the optional Naver Search API path, copy `.env.example` to `.env` and add your own
credentials. Do not commit `.env` or any crawl output. The repository `.gitignore`
excludes `crawler/data/`.

## Example

```bash
python crawl_all.py --keyword "황반변성" --date-from 20020101 --date-to 20260409
```

The manuscript analysis used a retained April 2026 crawl. A live rerun can differ because
platform indexing, deleted posts, HTML structure, and API behavior change over time.
