# 전문가 비교 및 review-pool 내부 평가

최종 갱신: 2026-08-30

Screening과 topic classification은 독립 blinded 전문가 비교 표본이며, review-pool
규칙은 같은 개발 workflow 안에서 수행한 내부 agreement assessment로 구분한다.
모든 행에서 Expert 1과 Expert 2는 같은 전문의를 뜻한다.

| Task | Expert 1 vs pipeline/rule | Expert 2 vs pipeline/rule | Inter-expert | 독립 일치 subset |
|---|---:|---:|---:|---:|
| Screening, binary (n=200) | κ=.800; 90.0% | κ=.790; 89.5% | κ=.789; 89.5% | 169/177=95.5% |
| Primary topic, 9 class (n=100) | κ=.882; 90.0% | κ=.789; 82.0% | κ=.766; 80.0% | 76/80=95.0% |
| Review-pool rule, 내부 pre-consensus (n=99-100) | κ=.717; 85.9% | κ=.520; 76.0% | κ=.661; 82.8% | 72/82=87.8% |

Review-pool disagreement를 공동합의한 뒤 rule은 consensus label 97건 중 81건과
일치했다(83.5%). 이 값은 post-consensus 결과이므로 독립 pre-consensus 수치와
같은 행에서 혼합하지 않는다.

## 공개 aggregate 재현

`aggregate_validation_counts.json`에는 record ID와 원문 없이 aggregate confusion
matrix만 포함되어 있다. 다음 명령으로 raw agreement와 Cohen κ를 다시 계산한다.

```bash
python validation/reproduce_aggregate_validation.py
```

원래의 row-level 전문가 판정 workbook은 공개하지 않는다. 따라서 기존
`screening_kappa.py`, `topic_kappa.py`, `r1_rule_kappa.py`는 내부 workbook이 있어야
실행되며, `reproduce_aggregate_validation.py`는 공개 파일만으로 실행된다.

## 해석 원칙

- Screening과 primary-topic classification은 독립 blinded specialist label과 비교했다.
- Review-pool rule 표본은 rule-development workflow의 일부이므로 외부 holdout
  validation으로 부르지 않는다.
- Gold 또는 concordant subset은 공동합의 전 두 전문의가 독립적으로 일치한 사례다.
