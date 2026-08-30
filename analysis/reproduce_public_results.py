"""Reproduce final public-data topic, temporal, QC, and C9 source-table results."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data" / "strict_AMD_corpus_1989.csv"
C9_SOURCE = ROOT / "tables" / "c9_subgroup_source_table.csv"
TOPICS = [f"C{i}" for i in range(1, 10)]
PERIODS = ["<=2009", "2010-2014", "2015-2019", "2020 onward"]


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def secondary(value: str) -> set[str]:
    return {item.strip() for item in re.split(r"[;,|]", value or "") if item.strip()}


def period(year: int) -> str:
    if year <= 2009:
        return PERIODS[0]
    if year <= 2014:
        return PERIODS[1]
    if year <= 2019:
        return PERIODS[2]
    return PERIODS[3]


def bh_adjust(values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(values.items(), key=lambda item: item[1])
    m = len(ordered)
    output: dict[str, float] = {}
    running = 1.0
    for reverse_index, (name, value) in enumerate(reversed(ordered), start=1):
        rank = m - reverse_index + 1
        running = min(running, value * m / rank)
        output[name] = running
    return output


def cochran_armitage(years: list[int], flags: list[int]) -> dict[str, float]:
    unique_years = sorted(set(years))
    n_by_year = [sum(year == value for year in years) for value in unique_years]
    positive_by_year = [
        sum(flag for year, flag in zip(years, flags) if year == value)
        for value in unique_years
    ]
    total = sum(n_by_year)
    positives = sum(positive_by_year)
    proportion = positives / total
    score_mean = sum(n * value for n, value in zip(n_by_year, unique_years)) / total
    numerator = sum(
        positives_at_year * (value - score_mean)
        for positives_at_year, value in zip(positive_by_year, unique_years)
    )
    variance = proportion * (1 - proportion) * (
        sum(n * value * value for n, value in zip(n_by_year, unique_years))
        - sum(n * value for n, value in zip(n_by_year, unique_years)) ** 2 / total
    )
    z = numerator / math.sqrt(variance) if variance > 0 else 0.0
    return {"z": z, "p": math.erfc(abs(z) / math.sqrt(2))}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    rows = load_csv(CORPUS)
    secondary_values = [secondary(row["secondary_topics"]) for row in rows]
    normalized = [
        re.sub(r"\s+", " ", (row["question_title"] + "\n" + row["question_content"]).strip().lower())
        for row in rows
    ]

    primary = Counter(row["primary_topic"] for row in rows)
    any_mention = Counter()
    for row, extra in zip(rows, secondary_values):
        for topic in {row["primary_topic"], *extra}:
            any_mention[topic] += 1

    period_counts = Counter(period(int(row["question_year"])) for row in rows)
    period_primary = {
        label: Counter(
            row["primary_topic"]
            for row in rows
            if period(int(row["question_year"])) == label
        )
        for label in PERIODS
    }

    years = [int(row["question_year"]) for row in rows]
    primary_tests = {
        topic: cochran_armitage(years, [int(row["primary_topic"] == topic) for row in rows])
        for topic in TOPICS
    }
    any_tests = {
        topic: cochran_armitage(
            years,
            [
                int(row["primary_topic"] == topic or topic in extra)
                for row, extra in zip(rows, secondary_values)
            ],
        )
        for topic in TOPICS
    }
    primary_q = bh_adjust({topic: value["p"] for topic, value in primary_tests.items()})
    any_q = bh_adjust({topic: value["p"] for topic, value in any_tests.items()})
    for topic in TOPICS:
        primary_tests[topic]["q"] = primary_q[topic]
        any_tests[topic]["q"] = any_q[topic]

    contingency = [[period_primary[label][topic] for topic in TOPICS] for label in PERIODS]
    row_totals = [sum(row) for row in contingency]
    column_totals = [sum(row[index] for row in contingency) for index in range(len(TOPICS))]
    chi_square = 0.0
    for row_index, values in enumerate(contingency):
        for column_index, observed in enumerate(values):
            expected = row_totals[row_index] * column_totals[column_index] / len(rows)
            chi_square += (observed - expected) ** 2 / expected
    cramer_v = math.sqrt(chi_square / (len(rows) * 3))

    duplicate_counts = Counter(normalized)
    duplicate_groups = [value for value in duplicate_counts.values() if value > 1]
    retained = set()
    deduplicated = []
    for row, key in zip(rows, normalized):
        if key not in retained:
            retained.add(key)
            deduplicated.append(row)
    dedup_primary = Counter(row["primary_topic"] for row in deduplicated)
    max_difference = max(
        abs(primary[topic] / len(rows) * 100 - dedup_primary[topic] / len(deduplicated) * 100)
        for topic in TOPICS
    )

    c9_rows = load_csv(C9_SOURCE)
    c9_overall = {
        row["subgroup"]: int(row["count"])
        for row in c9_rows
        if row["period"] == "overall"
    }
    c9_s1 = [
        int(row["count"])
        for row in c9_rows
        if row["subgroup"] == "S1_post_injection_AE" and row["period"] != "overall"
    ]

    result = {
        "corpus": {
            "n": len(rows),
            "unique_ids": len({row["id"] for row in rows}),
            "primary_repeated_in_secondary": sum(
                row["primary_topic"] in extra for row, extra in zip(rows, secondary_values)
            ),
            "mean_topics_per_thread": sum(1 + len(extra) for extra in secondary_values) / len(rows),
            "threads_with_secondary": sum(bool(extra) for extra in secondary_values),
            "duplicate_content_excess_rows": sum(value - 1 for value in duplicate_groups),
            "duplicate_content_groups": len(duplicate_groups),
            "deduplicated_n": len(deduplicated),
            "max_primary_rate_change_percentage_points": max_difference,
        },
        "primary": {topic: {"n": primary[topic], "pct": primary[topic] / len(rows) * 100} for topic in TOPICS},
        "any_mention": {topic: {"n": any_mention[topic], "pct": any_mention[topic] / len(rows) * 100} for topic in TOPICS},
        "period_n": {label: period_counts[label] for label in PERIODS},
        "global_primary_composition": {"chi_square": chi_square, "df": 24, "cramers_v": cramer_v},
        "primary_trends": primary_tests,
        "any_mention_trends": any_tests,
        "c9_aggregate_source": {"overall": c9_overall, "s1_period_counts": c9_s1},
    }

    assert result["corpus"]["n"] == 1989
    assert result["corpus"]["unique_ids"] == 1989
    assert result["corpus"]["primary_repeated_in_secondary"] == 0
    assert result["period_n"] == {"<=2009": 62, "2010-2014": 215, "2015-2019": 667, "2020 onward": 1045}
    assert c9_overall["S1_post_injection_AE"] == 187
    assert c9_s1 == [4, 18, 52, 113]

    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
