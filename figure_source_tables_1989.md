# AMD KIN — Figure Source Tables (final corpus N=1,989)

작성 2026-06-19 · 1,989 strict-AMD corpus 재집계 · 공동연구자(남기태 교수님) 공유용

- 최종 corpus **N = 1989** (`_stage4_topic_FINAL_v3_1989.jsonl`)
- 4 기간 n = **62 / 215 / 667 / 1045**
- 라벨: `final_primary`(단일 dominant) + `final_secondary`(0–3, multi-label)
- 약제·답변신호·모달리티 표는 원자료 답변텍스트 join 결과(검증 완료값)

## Figure 2 — Topic distribution

| Topic | Primary n | Primary % | Any-mention n | Any-mention % |
|---|--:|--:|--:|--:|
| C1 Disease info/etiology | 196 | 9.9 | 289 | 14.5 |
| C2 Symptoms/diagnosis | 340 | 17.1 | 465 | 23.4 |
| C3 Treatment/surgery | 224 | 11.3 | 398 | 20.0 |
| C4 Anti-VEGF injection | 82 | 4.1 | 272 | 13.7 |
| C5 Nutrition/lifestyle | 446 | 22.4 | 586 | 29.5 |
| C6 Course/prognosis | 129 | 6.5 | 365 | 18.4 |
| C7 Cost/insurance | 156 | 7.8 | 194 | 9.8 |
| C8 Hospital/physician | 188 | 9.5 | 253 | 12.7 |
| C9 Other/adverse | 228 | 11.5 | 304 | 15.3 |

mean topics/thread = **1.57**

## Figure 3 — Temporal trends (primary-topic rate per period)

각 기간 컬럼 합 ≈ 100% (primary 단일라벨). Panel 3A(line)·3B(stacked) 공통.

| Topic | ~2009 | 2010-14 | 2015-19 | 2020~ |
|---|--:|--:|--:|--:|
| C1 | 19.4 | 16.3 | 10.5 | 7.6 |
| C2 | 4.8 | 11.6 | 16.8 | 19.1 |
| C3 | 14.5 | 13.0 | 14.8 | 8.4 |
| C4 | 17.7 | 5.1 | 2.8 | 3.9 |
| C5 | 4.8 | 26.0 | 26.4 | 20.2 |
| C6 | 11.3 | 2.8 | 7.6 | 6.2 |
| C7 | 11.3 | 9.3 | 5.5 | 8.8 |
| C8 | 6.5 | 8.8 | 6.9 | 11.4 |
| C9 | 9.7 | 7.0 | 8.5 | 14.4 |

**C5 mention-share trajectory** (3A 점선; 분모 = 기간 전체 mention 수)

| | ~2009 | 2010-14 | 2015-19 | 2020~ |
|---|--:|--:|--:|--:|
| C5 mention-share % | 8.5 | 23.5 | 21.9 | 16.4 |

> 주: 본문 Results 의 C1/C2/C3/C4 first→last 값(7.6/19.1/8.4/3.9 등)은 위 ~2009 vs 2020~ 컬럼과 일치.

## Figure 5 — Anti-VEGF agent mentions (thread counts; Q=question side, A=answer side)

| Agent | side | ~2009 | 2010-14 | 2015-19 | 2020~ | total | Z | q(BH) |
|---|:--:|--:|--:|--:|--:|--:|--:|--:|
| Bevacizumab | Q | 1 | 11 | 19 | 17 | 48 | -2.40 | .041 |
| Bevacizumab | A | 9 | 37 | 58 | 70 | 174 | -4.67 | <.001 |
| Ranibizumab | Q | 11 | 14 | 10 | 7 | 42 | -8.61 | <.001 |
| Ranibizumab | A | 23 | 39 | 64 | 70 | 196 | -8.00 | <.001 |
| Aflibercept | Q | 0 | 6 | 5 | 10 | 21 | -0.95 | .49 |
| Aflibercept | A | 1 | 8 | 11 | 23 | 43 | -0.44 | .73 |
| Faricimab | Q | 0 | 0 | 0 | 1 | 1 | — | ns |
| Faricimab | A | 0 | 0 | 0 | 2 | 2 | — | ns |
| Brolucizumab | Q | 0 | 0 | 0 | 0 | 0 | — | - |
| Brolucizumab | A | 0 | 0 | 0 | 3 | 3 | — | ns |

**기간별 비율(%)** = 위 count / 기간 n. 예: Ranibizumab A 2020~ = 70/1045 = 6.7%.
Cochran–Armitage trend test (score 1–4), BH-FDR across 10 tests (5 drugs × Q/A).

## Figure 6 — Answer-ecosystem signals (refined detector v2; N=1,989)

| Signal | n | % | PPV (Wilson 95% CI) |
|---|--:|--:|---|
| Supplement recommendation | 827 | 41.6 | 96% (80.5–99.3) |
| Surgery / laser mention | 634 | 31.9 | — |
| Injection mention | 610 | 30.7 | — |
| External link / blog | 577 | 29.0 | 100% (86.7–100) |
| Traditional medicine | 504 | 25.3 | — |
| Hospital / clinic referral | 425 | 21.4 | 40% (23.4–59.3) |
| Examination / clinic-visit referral | 417 | 21.0 | — |
| Cure / vision-recovery claim | 168 | 8.4 | — |

pooled PPV = 70.5% (63.8–76.4). 신호는 multi-label(한 답변에 복수 신호 독립 카운트).

## Figure S1 — Annual strict-AMD thread counts

| Year | n | | Year | n | | Year | n |
|--:|--:|---|--:|--:|---|--:|--:|
| 2004 | 2 | | 2005 | 5 | | 2006 | 5 |
| 2007 | 8 | | 2008 | 10 | | 2009 | 32 |
| 2010 | 23 | | 2011 | 25 | | 2012 | 33 |
| 2013 | 60 | | 2014 | 74 | | 2015 | 84 |
| 2016 | 97 | | 2017 | 129 | | 2018 | 154 |
| 2019 | 203 | | 2020 | 170 | | 2021 | 185 |
| 2022 | 157 | | 2023 | 203 | | 2024 | 165 |
| 2025 | 123 | | 2026 | 42 | |  |  |

2002–2003 = 0 (strict-AMD 미부합). 4 기간 경계: ≤2009 / 2010–14 / 2015–19 / 2020~.

## Figure S3 — Treatment modality mention rate (N=1,989, Q+A combined)

| Modality | n | % |
|---|--:|--:|
| Intravitreal injection | 737 | 37.1 |
| Surgery | 537 | 27.0 |
| Laser | 341 | 17.1 |
| Photodynamic therapy (PDT) | 230 | 11.6 |

모달리티는 thread당 1회, 상호배타 아님.

## Figure S4 — Injection-related sub-concerns (n=272; C4 primary or secondary)

| Sub-concern | n | % |
|---|--:|--:|
| 효과/호전 정도 | 80 | 29.4 |
| 주기/횟수/간격 | 46 | 16.9 |
| 통증/시술 과정 | 30 | 11.0 |
| 부작용/위험 | 47 | 17.3 |
| 비용/보험 | 66 | 24.3 |
| 시기/타이밍 | 37 | 13.6 |
| 중단/내성/한계 | 16 | 5.9 |
| 실명 예방 여부 | 36 | 13.2 |

분모 n=272 = C4 any-mention(`final_*`). 하위범주 multi-tag.

## Figure S5 — Nutrition/lifestyle sub-categories (n=586; C5 primary or secondary)

| Sub-category | n | % |
|---|--:|--:|
| 영양제 루테인 | 182 | 31.1 |
| 영양제 지아잔틴 | 59 | 10.1 |
| 영양제 오메가3 | 46 | 7.8 |
| 영양제 아스타잔틴 | 18 | 3.1 |
| 영양제 빌베리/베리류 | 26 | 4.4 |
| 영양제 AREDS/오큐바이트류 | 38 | 6.5 |
| 영양제 비타민/미네랄 | 65 | 11.1 |
| 영양제 제품·복용시기 | 87 | 14.8 |
| 생활 음식/식이 | 196 | 33.4 |
| 생활 자외선/선글라스 | 23 | 3.9 |
| 생활 금연/흡연 | 17 | 2.9 |
| 생활 전자기기/블루라이트 | 27 | 4.6 |
| 생활 운동/생활관리 | 158 | 27.0 |
| 생활 예방 일반 | 62 | 10.6 |

분모 n=586 = C5 any-mention(`final_*`). 하위범주 multi-tag.

---
*모든 수치는 final 1,989 corpus 기준으로 재현 가능. 약제/신호/모달리티는 원자료 답변텍스트 필요(스크립트: `_stage9_drug_trend_v6.py`, `_stage5_signals_v2.py`, `_stage5_detailed_analysis.py`).*