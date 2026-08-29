"""Recalculate raw agreement and Cohen kappa from public aggregate matrices."""

from __future__ import annotations

import json
from pathlib import Path


SOURCE = Path(__file__).with_name("aggregate_validation_counts.json")


def metrics(matrix: dict[str, object]) -> tuple[int, float, float]:
    counts = matrix["counts"]
    n = sum(sum(row) for row in counts)
    observed = sum(counts[index][index] for index in range(len(counts))) / n
    row_totals = [sum(row) for row in counts]
    column_totals = [sum(row[index] for row in counts) for index in range(len(counts))]
    expected = sum(row * column for row, column in zip(row_totals, column_totals)) / (n * n)
    kappa = (observed - expected) / (1 - expected) if expected < 1 else 1.0
    return n, observed, kappa


def show(name: str, matrix: dict[str, object]) -> None:
    n, raw, kappa = metrics(matrix)
    print(f"{name:<38} n={n:>3}  raw={raw * 100:5.1f}%  kappa={kappa:.3f}")


def main() -> None:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    screening = data["screening"]
    print("Screening")
    show("Expert 1 vs pipeline", screening["expert_1_vs_pipeline"])
    show("Expert 2 vs pipeline", screening["expert_2_vs_pipeline"])
    show("Expert 1 vs Expert 2", screening["expert_1_vs_expert_2"])
    gold = screening["expert_concordant_subset"]
    print(f"Gold subset: {gold['pipeline_matches']}/{gold['n']}={gold['pipeline_matches'] / gold['n'] * 100:.1f}%")

    topic = data["topic"]
    print("\nTopic classification")
    show("Expert 1 vs pipeline", topic["expert_1_vs_pipeline"])
    show("Expert 2 vs pipeline", topic["expert_2_vs_pipeline"])
    show("Expert 1 vs Expert 2", topic["expert_1_vs_expert_2"])
    gold = topic["expert_concordant_subset"]
    print(f"Gold subset: {gold['pipeline_matches']}/{gold['n']}={gold['pipeline_matches'] / gold['n'] * 100:.1f}%")

    review = data["review_pool_rule"]["pre_consensus_independent"]
    print("\nReview-pool rule: pre-consensus independent labels")
    show("Expert 1 vs rule", review["expert_1_vs_rule"])
    show("Expert 2 vs rule", review["expert_2_vs_rule"])
    show("Expert 1 vs Expert 2", review["expert_1_vs_expert_2"])
    gold = review["expert_concordant_subset"]
    print(f"Concordant subset: {gold['rule_matches']}/{gold['n']}={gold['rule_matches'] / gold['n'] * 100:.1f}%")

    post = data["review_pool_rule"]["post_consensus_adjudicated"]
    print(f"Post-consensus: {post['rule_matches']}/{post['n']}={post['rule_matches'] / post['n'] * 100:.1f}%")


if __name__ == "__main__":
    main()

