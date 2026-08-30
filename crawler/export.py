#!/usr/bin/env python3
"""
크롤링된 raw JSON 데이터를 CSV/Excel로 변환합니다.

사용법:
    python export.py
    python export.py --format csv
    python export.py --format both
"""

import json
import re
import argparse
from pathlib import Path
from datetime import datetime

import pandas as pd


# Excel에서 허용하지 않는 제어 문자 제거
ILLEGAL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

DATA_DIR = Path(__file__).parent / "data"
RAW_DIR = DATA_DIR / "raw"
OUTPUT_DIR = DATA_DIR / "output"


def load_raw_data() -> list[dict]:
    """raw/ 디렉토리의 모든 JSON 파일을 로드합니다."""
    if not RAW_DIR.exists():
        print(f"ERROR: {RAW_DIR} 디렉토리가 없습니다. crawl_content.py를 먼저 실행해주세요.")
        return []

    results = []
    json_files = sorted(RAW_DIR.glob("*.json"))

    for filepath in json_files:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            results.append(data)

    return results


def flatten_data(raw_data: list[dict]) -> list[dict]:
    """
    중첩 구조를 플랫하게 변환합니다.
    각 행 = 하나의 질문 + 모든 답변 정보.
    """
    rows = []

    for item in raw_data:
        q = item.get("question", {})
        answers = item.get("answers", [])

        row = {
            "url": item.get("url", ""),
            "question_title": q.get("title", ""),
            "question_author": q.get("author", ""),
            "question_content": q.get("content", ""),
            "question_date": q.get("date", ""),
            "question_views": q.get("views", 0),
            "category": q.get("category", ""),
            "answer_count": item.get("answer_count", 0),
            "crawled_at": item.get("crawled_at", ""),
        }

        # 답변을 개별 컬럼으로 (최대 10개)
        for i, ans in enumerate(answers[:10], 1):
            row[f"answer_{i}_content"] = ans.get("content", "")
            row[f"answer_{i}_author"] = ans.get("author", "")
            row[f"answer_{i}_date"] = ans.get("date", "")
            row[f"answer_{i}_adopted"] = ans.get("is_adopted", False)

        # 전체 답변을 JSON 문자열로도 저장 (분석 편의)
        row["answers_json"] = json.dumps(answers, ensure_ascii=False)

        rows.append(row)

    return rows


def clean_illegal_chars(df: pd.DataFrame) -> pd.DataFrame:
    """Excel에서 허용하지 않는 제어 문자를 제거합니다."""
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].apply(lambda x: ILLEGAL_CHARS_RE.sub("", x) if isinstance(x, str) else x)
    return df


def export_to_excel(df: pd.DataFrame, filepath: Path):
    """Excel로 내보내기."""
    from openpyxl.styles import Alignment

    df = clean_illegal_chars(df)
    # Excel 셀 내 줄바꿈: \n → \r\n 변환 (Excel이 인식하는 형식)
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].apply(
            lambda x: x.replace("\r\n", "\n").replace("\n", "\r\n") if isinstance(x, str) else x
        )
    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="지식인_크롤링")

        # 컬럼 너비 자동 조정
        worksheet = writer.sheets["지식인_크롤링"]
        for i, col in enumerate(df.columns):
            max_len = max(
                df[col].astype(str).fillna("").str.len().max(),
                len(col)
            )
            col_letter = chr(65 + i) if i < 26 else f"A{chr(65 + i - 26)}"
            worksheet.column_dimensions[col_letter].width = min(max_len + 2, 50)

        # 모든 셀에 wrap_text 적용 (줄바꿈 표시)
        for row in worksheet.iter_rows():
            for cell in row:
                cell.alignment = Alignment(wrap_text=True)

    print(f"  Excel 저장: {filepath}")


def export_to_csv(df: pd.DataFrame, filepath: Path):
    """CSV로 내보내기."""
    df.to_csv(filepath, index=False, encoding="utf-8-sig")  # BOM 포함 (Excel 한글 호환)
    print(f"  CSV 저장: {filepath}")


def main():
    parser = argparse.ArgumentParser(description="크롤링 데이터 내보내기")
    parser.add_argument("--keyword", type=str, default="황반변성", help="Excel/CSV 파일명에 사용할 키워드 (기본: 황반변성)")
    parser.add_argument("--format", choices=["csv", "excel", "both"], default="both", help="출력 형식")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("크롤링 데이터 로드 중...")
    raw_data = load_raw_data()
    if not raw_data:
        print("내보낼 데이터가 없습니다.")
        return

    print(f"  {len(raw_data)}건 로드 완료")

    print("데이터 변환 중...")
    rows = flatten_data(raw_data)
    df = pd.DataFrame(rows)

    # 빈 질문 필터링
    valid_mask = (df["question_title"] != "") | (df["question_content"] != "")
    filtered = df[valid_mask]
    print(f"  유효 데이터: {len(filtered)}건 (전체: {len(df)}건)")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if args.format in ("excel", "both"):
        excel_path = OUTPUT_DIR / f"{args.keyword}_지식인_{timestamp}.xlsx"
        export_to_excel(filtered, excel_path)

    if args.format in ("csv", "both"):
        csv_path = OUTPUT_DIR / f"{args.keyword}_지식인_{timestamp}.csv"
        export_to_csv(filtered, csv_path)

    print(f"\n내보내기 완료!")
    print(f"  총 {len(filtered)}건")
    print(f"  답변 포함 건수: {(filtered['answer_count'] > 0).sum()}건")
    print(f"  평균 답변 수: {filtered['answer_count'].mean():.1f}개")


if __name__ == "__main__":
    main()
