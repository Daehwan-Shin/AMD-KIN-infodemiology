# Expert Comparison and Review-Pool Assessment

Updated: 2026-08-30

The repository separates two independent expert-comparison samples from the internal
review-pool rule assessment. Expert 1 and Expert 2 refer to the same specialists across
all rows.

| Task | Expert 1 vs pipeline/rule | Expert 2 vs pipeline/rule | Inter-expert | Concordant subset |
|---|---:|---:|---:|---:|
| Screening, binary (n=200) | κ=.800; 90.0% | κ=.790; 89.5% | κ=.789; 89.5% | 169/177=95.5% |
| Primary topic, 9 class (n=100) | κ=.882; 90.0% | κ=.789; 82.0% | κ=.766; 80.0% | 76/80=95.0% |
| Review-pool rule, internal pre-consensus (n=99-100) | κ=.717; 85.9% | κ=.520; 76.0% | κ=.661; 82.8% | 72/82=87.8% |

After joint adjudication of review-pool disagreements, the rule matched 81 of 97
consensus-labeled cases (83.5%). This post-consensus value is reported separately because
it is not the same stage as the independent pre-consensus metrics.

## Public aggregate reproduction

`aggregate_validation_counts.json` contains aggregate confusion matrices only. It includes
no record IDs or text. Recalculate raw agreement and Cohen kappa with:

```bash
python validation/reproduce_aggregate_validation.py
```

The original row-level review workbooks are not publicly redistributed. The legacy
`screening_kappa.py`, `topic_kappa.py`, and `r1_rule_kappa.py` scripts therefore require
retained internal workbooks, whereas `reproduce_aggregate_validation.py` is fully public.

## Interpretation

- Screening and primary-topic classification used independent blinded specialist labels.
- The review-pool rule sample belonged to the rule-development workflow and is an internal
  agreement assessment, not an untouched external validation set.
- Gold or concordant subsets contain cases on which the two specialists independently
  agreed before any joint adjudication.
