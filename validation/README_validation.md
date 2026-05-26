# Human Validation 종합 정리

> **최종 갱신**: 2026-05-26
> **연구**: AMD Naver Knowledge-iN infodemiology (corpus 1,989 strict_AMD)
> **Labelers**: 두 retinal specialist — SDH (저자) / NKT (senior retinal specialist)

---

## 한눈에 보는 4가지 validation track

| Track | Sample | 시점 | 주요 metric |
|---|---|---|---|
| **A. Screening** | 200 balanced | v1 (기존) | κ 0.78–0.80, gold 95.5% |
| **B. Topic classification** | 100 random (97 기존 + 3 교체) | v5 (재집계) | κ 0.79–0.88, gold 95.0% |
| **C. Review-pool R1 rule** | 100 v5b-balanced | v5 (신규) | κ 0.62–0.68, gold 83.5% |
| **D. Inter-expert disagreement consensus** | 17 cases | v5 (신규) | gold-subset 83→97 확장 |

---

## A. Screening validation (200 balanced sample)

### 설계
- **샘플**: 100 `Include_strict_AMD` + 100 `Exclude_non_AMD` (balanced, seed-fixed, shuffled, blinded)
- **Labelers**: SDH, NKT (각자 독립)
- **Codebook**: Screening codebook v1.0 (G1–G7)
- **시기**: v1 패키지 시점 (변경 없음)

### 결과

| 지표 | 값 |
|---|---:|
| SDH vs LLM consensus κ | **0.78–0.79** (raw 88.5–89.5%) |
| NKT vs LLM consensus κ | **0.80** (raw 90.0%) |
| Inter-expert (SDH vs NKT) κ | **0.78** (raw 88.5–89.5%) |
| **Gold-subset agreement** (양 expert 일치 177건) | **95.5% (169/177)** |

### 해석
LLM consensus 가 inter-expert reliability 와 동등한 신뢰도로 binary screening 을 수행. main screening 결과는 **변경 없음** (corpus 정의 자체는 그대로).

---

## B. Topic classification validation (100 sample)

### 설계 — v5 업데이트 반영
- **원본 100 sample** (random from corpus): 기존 라벨링 유지
- **3 dropped 케이스** (v5b 적용 시 corpus 에서 빠짐): P2-2516, P2-2195, P2-3098
- **3 replacement 신규 라벨링**: P2-2723 (C3), P2-0084 (C5), Q-078 (C9)
- 최종 sample: 97 기존 + 3 신규 = **100**
- **Codebook**: Topic codebook v1.0 (9-class, B1–B8 boundary rules)

### 결과

| 지표 | 값 (이전 → 새) |
|---|---:|
| SDH vs LLM primary κ | 0.906 → **0.882** (raw 92.0% → 90.0%) |
| NKT vs LLM primary κ | 0.825 → **0.789** (raw 85.0% → 82.0%) |
| Inter-expert κ | 0.778 → **0.766** (raw 81.0% → 80.0%) |
| **Gold-subset agreement** (양 expert primary 일치 80건) | 98.8% (84/85) → **95.0% (76/80)** |

### 해석
- 9-class multi-label 분류에서 여전히 매우 높은 신뢰도 (κ 0.79–0.88)
- Gold-subset 일치 95% — inter-expert κ=0.77 보다 LLM 가 더 잘 align
- 약간의 magnitude 감소 (κ -0.024 ~ -0.036) 는 corpus 축소 (-59) 와 3 case replacement 의 자연스러운 결과

---

## C. Review-pool R1 rule validation (v5b balanced 100)

### 설계 — 신규 (v5 패키지에 처음 추가)
- **샘플**: 100 review-pool threads (50 R1-applied + 50 non-R1 under v5b; balanced, seed-fixed, shuffled, blinded)
- **구성**: 86 기존 + 14 추가 (v5b 분포로 rebalance 후 ADD15 라벨링)
- **Labelers**: SDH, NKT 독립 → R1 / not_R1 / uncertain 판정
- **R1 정의 제시**: R1 = "자가 의심 + age cue 없음 + 다른 강한 비AMD 신호 없음" → Include_strict_AMD
- 13가지 배제 신호 taxonomy 도 안내문에 포함

### 결과 (raw, pre-consensus)

| 지표 | 값 |
|---|---:|
| SDH vs rule κ | 0.717 (raw 85.9%) |
| NKT vs rule κ | 0.520 (raw 76.0%) |
| Inter-expert κ | **0.661** (raw 82.8%) |
| Gold-subset agreement (양 expert 일치 82건) | **87.8% (72/82)** |

### 결과 (Track D 의 disagreement 17 final consensus 반영 후)

| 지표 | 값 |
|---|---:|
| SDH vs rule κ (consensus 반영) | **0.677** (raw 83.8%) |
| NKT vs rule κ (consensus 반영) | **0.620** (raw 81.0%) |
| **Gold-subset** (양 expert 일치 97건) | **83.5% (81/97)** |
| - gold-R1 일치 | 83.0% (39/47) |
| - gold-not_R1 일치 | 84.0% (42/50) |

### 해석
- Inter-expert κ=0.66 — Review pool 이 정의상 ambiguous case 들 (tri-LLM 합의 못 이룬 marginal threads) 이라 본질적 모호성 반영
- LLM rule (v5b) 이 expert 와 ~84% 일치 → main screening (95.5%) 보다는 낮지만, review pool 의 marginal character 고려 시 acceptable
- gold-R1 과 gold-not_R1 모두 ~83-84% 균형 → rule 이 한쪽으로 치우치지 않음

---

## D. Inter-expert disagreement final consensus (17 cases)

### 설계 — 신규
- 100 v5b-balanced sample 중 SDH ≠ NKT 17 cases
- 두 전문의가 함께 review 후 final consensus 라벨 합의 (xlsx 의 `★ FINAL LABEL` 컬럼)
- 17 cases 를 5가지 패턴으로 분류:

| Category | n | 설명 |
|---:|---:|---|
| A. LLM 충돌 (Codex·Opus 의견 갈림) | 3 | G2/G7 vs R1 같은 fundamental disagreement |
| B. SDH conservative — 자가의심+영양제/일시적 | 5 | 가벼운 self-suspect 케이스 |
| C. SDH conservative — 동반/시술/borderline | 7 | G3·R4·borderline age 신호 |
| D. AMD 배경 — 질문은 다른 주제 | 1 | 간염·한방 등 main concern |
| E. Rare SDH=R1 | 1 | 드문 케이스 |

### 최종 합의 결과

| 합의 label | 수 |
|---:|---:|
| R1 | 5 |
| not_R1 | 12 |

→ 17 합의 중 **12 (71%) 가 not_R1** 로 수렴 — NKT 가 R1 으로 본 일부 자가의심 케이스가 합의에선 not_R1 으로 정리됨 (SDH 의 더 보수적 판단이 합의에 가까움).

### 의미
- Gold-subset 분모: 83건 → **97건** (+14) 으로 확장
- Rule v5b 의 evaluation 이 더 신뢰 가능 (분모 확대)
- 8% 정도의 uncertain · genuinely ambiguous case 만 잔존

---

## 종합 의미

### 1. Multi-LLM consensus 가 inter-expert reliability 와 동등

| Task | LLM-vs-expert κ | inter-expert κ | LLM consensus 위치 |
|---|---:|---:|---|
| Screening (binary) | 0.78–0.80 | 0.78 | **at level** |
| Topic (9-class) | 0.79–0.88 | 0.77 | **at or above** |
| Review-pool R1 (binary) | 0.62–0.68 | 0.66 | **at level** |

→ "**LLM consensus ≈ inter-expert reliability**" 패턴이 3가지 task 에서 모두 재현

### 2. Gold-subset agreement 의 hierarchy

| Task | Gold-subset agreement | 해석 |
|---|---:|---|
| Screening | **95.5%** | 매우 신뢰 가능 |
| Topic (9-class) | **95.0%** | 매우 신뢰 가능 |
| Review-pool R1 | **83.5%** | acceptable (review pool 정의상 marginal) |

→ Pipeline 의 각 단계가 점진적으로 모호성 증가, 그러나 모두 acceptable 한 신뢰도

### 3. Methods 에서 reporting 할 수치

- **Screening**: κ 0.78–0.80, gold 95.5% (n=177)
- **Topic**: κ 0.79–0.88, inter-expert κ=0.77, gold 95.0% (n=80)
- **Review-pool R1 rule**: κ 0.62–0.68, inter-expert κ=0.66, gold 83.5% (n=97; consensus-resolved cases included)

---

## 파일 위치

### 원본 라벨링 데이터 (수정용자료/)
- `AMD_R1_validation_ADD15_v5b_SDH_done.xlsx` (SDH R1 추가 14)
- `AMD_R1_validation_ADD15_v5b_NKT__NKTdone.xlsx` (NKT R1 추가 14)
- `AMD_R1_inter_expert_disagreement_v2_NKTdone.xlsx` (disagreement 17 final consensus)
- `AMD_topic_replacement_3_SDH_done.xlsx` (SDH topic 교체 3)
- `AMD_topic_replacement_3_NKT_NKTdone.xlsx` (NKT topic 교체 3)

### 기존 라벨링 (corpus 변경 전)
- `AMD_R1_validation_100_SDH_Done.xlsx` (SDH R1 100, 재고려 65:35 반영)
- `AMD_R1_validation_100_NKT_Done.xlsx` (NKT R1 100)
- `AMD_topic_human_validation_100_SDH.xlsx` (SDH topic 100)
- `AMD_topic_human_validation_100_NKT_1.xlsx` (NKT topic 100)
- `AMD_validation_review_template_260420.xlsx` (screening 200 sample)

### 분석 산출물
- `_v5b_final_records.csv` — R1 v5b-balanced 100 통합 결과
- `_corpus_transition_v5b.csv` — v1↔v5b corpus transition
- `_topic_validation_v5b_impact.csv` — topic validation 영향 분석
- `_R1_validation_key_v5b_balanced.jsonl` — R1 100 sample key (analyst 용)

---

## 한 줄 요약

> "**4-track human validation** (screening 200 + topic 100 + R1 rule 100 + disagreement consensus 17) 모두에서 LLM consensus 가 inter-expert reliability 와 동등하거나 그 이상의 일치를 보였고, 각 stage 의 gold-subset agreement 는 task 의 본질적 난이도 (95.5% → 95.0% → 83.5%) 를 반영."
