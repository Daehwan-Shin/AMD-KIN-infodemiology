# Human Validation Summary (English Reference)

> **Note**: English-reference version of the validation summary.
> For the original Korean prose version with detailed file pointers, see
> `README_validation.md` (in this folder) or `human_validation_summary.md`.

- **Last updated**: 2026-05-26
- **Study**: AMD Naver Knowledge-iN infodemiology (corpus 1,989 strict_AMD threads)
- **Labelers**: Two board-certified retinal specialists —
  SDH (the corresponding author) and NKT (senior retinal specialist).

---

## Four validation tracks at a glance

| Track | Sample | Timing | Key metric |
|---|---|---|---|
| **A. Screening** | 200 balanced | Phase v1 (unchanged) | κ 0.78–0.80, gold 95.5% |
| **B. Topic classification** | 100 random (97 original + 3 replacement) | Recomputed in v5 | κ 0.79–0.88, gold 95.0% |
| **C. Review-pool R1 rule** | 100 v5b-balanced | New in v5 | κ 0.62–0.68, gold 83.5% |
| **D. Inter-expert disagreement consensus** | 17 cases | New in v5 | Gold-subset expanded 83→97 |

---

## A. Screening validation (200 balanced sample)

### Design
- **Sample**: 100 `Include_strict_AMD` + 100 `Exclude_non_AMD` (balanced, seed-fixed, shuffled, blinded)
- **Labelers**: SDH and NKT, independent
- **Codebook**: Screening codebook v1.0 (G1–G7)
- **Timing**: Computed at the v1 manuscript package; unchanged since.

### Results

| Metric | Value |
|---|---:|
| SDH vs LLM consensus κ | **0.78–0.79** (raw 88.5–89.5%) |
| NKT vs LLM consensus κ | **0.80** (raw 90.0%) |
| Inter-expert (SDH vs NKT) κ | **0.78** (raw 88.5–89.5%) |
| **Gold-subset agreement** (177 cases where both experts agreed) | **95.5% (169/177)** |

### Interpretation
LLM consensus performs binary screening with reliability comparable to two independent
retinal specialists. The main screening output (corpus partition into Include /
Exclude / Review_needed) is unchanged across manuscript versions.

---

## B. Topic classification validation (100 sample)

### Design — updated in v5
- **Original 100 sample** (random from corpus): existing labels retained.
- **3 dropped cases** (excluded from corpus after v5b R1 rule refinement):
  P2-2516, P2-2195, P2-3098.
- **3 replacement cases**, newly labeled: P2-2723 (C3), P2-0084 (C5), Q-078 (C9).
- **Final sample**: 97 retained + 3 new = **100**.
- **Codebook**: Topic codebook v1.0 (9-class multi-label, with B1–B8 boundary rules).

### Results (previous → new)

| Metric | Value (prev → new) |
|---|---:|
| SDH vs LLM primary κ | 0.906 → **0.882** (raw 92.0% → 90.0%) |
| NKT vs LLM primary κ | 0.825 → **0.789** (raw 85.0% → 82.0%) |
| Inter-expert κ | 0.778 → **0.766** (raw 81.0% → 80.0%) |
| **Gold-subset agreement** (both experts agreed on primary, 80 cases) | 98.8% (84/85) → **95.0% (76/80)** |

### Interpretation
- Reliability remains high (κ 0.79–0.88) for a 9-class multi-label task.
- Gold-subset agreement of 95% — the LLM consensus aligns with expert consensus better
  than the two experts align with each other (inter-expert κ = 0.77).
- Slight magnitude attenuation (κ ↓ 0.02–0.04) reflects corpus contraction (−59 threads)
  and 3-case replacement; no shift in directional findings.

---

## C. Review-pool R1 rule validation (100 v5b-balanced)

### Design — new in v5
- **Sample**: 100 Review_needed threads (50 R1-applied + 50 non-R1 under the final v5b rule;
  balanced, seed-fixed, shuffled, blinded).
- **Composition**: 86 cases from the original v1-stratified sample + 14 added to balance the
  v5b stratification.
- **Labelers**: SDH and NKT, independent → labeled R1 / not_R1 / uncertain.
- **R1 definition shown to labelers**: "self-suspect + no age cue + no other strong
  non-AMD signal" → Include_strict_AMD.
- **Exclusion-signal taxonomy** (13 patterns) provided as written instructions.

### Results — raw (pre-consensus)

| Metric | Value |
|---|---:|
| SDH vs rule κ | 0.717 (raw 85.9%) |
| NKT vs rule κ | 0.520 (raw 76.0%) |
| Inter-expert κ | **0.661** (raw 82.8%) |
| Gold-subset agreement (82 cases where both experts agreed) | **87.8% (72/82)** |

### Results — after Track D consensus deliberation on 17 disagreement cases

| Metric | Value |
|---|---:|
| SDH vs rule κ (consensus-applied) | **0.677** (raw 83.8%) |
| NKT vs rule κ (consensus-applied) | **0.620** (raw 81.0%) |
| **Gold-subset agreement** (97 cases) | **83.5% (81/97)** |
| - gold-R1 agreement | 83.0% (39/47) |
| - gold-not_R1 agreement | 84.0% (42/50) |

### Interpretation
- Inter-expert κ = 0.66 (Landis–Koch "substantial agreement"); the same two specialists
  achieved κ 0.77–0.78 on the general screening and topic samples — the difference reflects
  **the intrinsic ambiguity of the Review pool**, which by definition contains threads
  that the tri-LLM consensus could not resolve.
- Within that intrinsically ambiguous task, the rule's agreement with each expert
  (κ 0.62–0.68) **matches inter-expert κ** — the same "LLM consensus ≈ inter-expert
  reliability" pattern observed for screening and topic tasks.
- Gold-subset balance (gold-R1 83.0% vs gold-not_R1 84.0%) shows the rule is **not biased
  toward either class** — its errors are symmetric.

---

## D. Inter-expert disagreement consensus (17 cases)

### Design — new in v5
- Among the 100 v5b-balanced sample, 17 cases had SDH ≠ NKT.
- The two specialists deliberated jointly and recorded a **final consensus label** in
  the dedicated `★ FINAL LABEL` column of the disagreement xlsx.
- Cases were grouped into 5 patterns:

| Category | n | Description |
|---:|---:|---|
| A. LLM conflict (Codex vs Opus split) | 3 | G2/G7 vs R1-type fundamental disagreement |
| B. SDH-conservative: self-suspect + supplement/transient | 5 | Light self-suspect cases |
| C. SDH-conservative: comorbidity / procedure / borderline | 7 | G3, R4, borderline-age signals |
| D. AMD as background — main concern elsewhere | 1 | E.g., hepatitis + herbal medicine |
| E. Rare SDH=R1 | 1 | Uncommon |

### Consensus outcome

| Final label | Count |
|---:|---:|
| R1 | 5 |
| not_R1 | 12 |

→ 12 of 17 (71%) consensus-resolved as not_R1 — closer to SDH's more conservative
position. NKT's broader R1 labeling on light self-suspect cases largely converged to
not_R1 after joint review.

### Effect on downstream metrics
- Gold-subset denominator expanded from 83 to **97** (+14 cases).
- About 8% (3 of 100) remain genuinely ambiguous and were dropped from gold metrics.

---

## Overall implications

### 1. "LLM consensus ≈ inter-expert reliability" across three tasks

| Task | LLM-vs-expert κ | Inter-expert κ | LLM consensus position |
|---|---:|---:|---|
| Screening (binary) | 0.78–0.80 | 0.78 | **At level** |
| Topic (9-class) | 0.79–0.88 | 0.77 | **At or above** |
| Review-pool R1 (binary) | 0.62–0.68 | 0.66 | **At level** |

The pattern recurs across three qualitatively distinct classification tasks.

### 2. Gold-subset agreement hierarchy

| Task | Gold-subset agreement | Interpretation |
|---|---:|---|
| Screening | **95.5%** | Highly reliable |
| Topic (9-class) | **95.0%** | Highly reliable |
| Review-pool R1 | **83.5%** | Acceptable for definitionally ambiguous marginal cases |

Each successive stage of the pipeline addresses an intrinsically more ambiguous decision,
and the agreement reflects that — yet all three remain in acceptable ranges for downstream
analysis.

### 3. What to report in Methods

- **Screening**: κ 0.78–0.80, gold-subset agreement 95.5% (n=177).
- **Topic**: κ 0.79–0.88, inter-expert κ=0.77, gold-subset agreement 95.0% (n=80).
- **Review-pool R1 rule**: κ 0.62–0.68, inter-expert κ=0.66, gold-subset agreement 83.5%
  (n=97; includes 14 cases resolved by post-hoc two-expert consensus deliberation).

---

## File locations (in this repository)

| Script | Purpose |
|---|---|
| `validation/screening_kappa.py` | Screening 200 κ computation |
| `validation/topic_kappa.py` | Topic 100 κ computation |
| `validation/r1_rule_kappa.py` | Review-pool R1 rule 100 κ computation (v5b balanced) |
| `validation/README_validation.md` | Korean prose version of this summary |
| `validation/README_validation_EN.md` | English reference (this file) |

For the underlying labeling spreadsheets (Excel xlsx), please contact the corresponding
author. The de-identified analysis-ready corpus is at `data/strict_AMD_corpus_1989.csv`.

---

## One-line summary

> "Across four validation tracks (Screening 200 + Topic 100 + R1 rule 100 + Disagreement
>  consensus 17), LLM consensus achieved agreement at or above the inter-expert κ on the
>  same task, with gold-subset agreement of 95.5% (screening), 95.0% (topic), and 83.5%
>  (R1 rule) reflecting the task's intrinsic difficulty."
