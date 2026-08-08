# AMD-KIN-infodemiology

Reproducible analysis code for the paper:

> **What the Public Asks About Age-Related Macular Degeneration:**
> **A Multi-LLM Analysis of 20 Years of Korean Online Questions and Their Answer Ecosystem**
> Daehwan Shin et al. — submitted to *JMIR Public Health and Surveillance*, 2026.

---

## Overview

This repository contains the codebooks, pipeline scripts, analysis code, and
de-identified corpus used in the paper.

- **Corpus**: 1,989 strict-AMD threads from Naver Knowledge-iN (2004–2026)
- **Pipeline**: tri-LLM consensus (Claude Opus 4.7 + OpenAI Codex gpt-5.5 + Google Gemini 3 Pro)
- **Validation**: two retinal specialists on three independent samples
  (Screening n=200, Topic n=100, Review-pool R1 rule n=100)
- **Topics**: 9-class multi-label classification scheme (C1–C9)
- **Codebooks v1.0** included: screening (G1–G7) and topic (B1–B8 boundary rules)
- **Bilingual documentation**: codebooks and the validation summary are provided in both
  the original Korean prose version and an English reference version (`*_EN.md`).
  Korean keyword patterns are kept as-is (they are *data* — used for matching against
  Korean question text); structural rules and examples are translated.

---

## Repository Structure

```
AMD-KIN-infodemiology/
├── README.md
├── LICENSE                 (MIT)
├── .gitignore
├── requirements.txt
│
├── codebook/               Stage 2 (screening) and Stage 4 (topic) codebooks v1.0
│   ├── stage2_screening_codebook_v1.0.md       (Korean prose, with English structural rules)
│   ├── stage2_screening_codebook_v1.0_EN.md    (English reference)
│   ├── stage4_topic_codebook_v1.0.md           (Korean)
│   └── stage4_topic_codebook_v1.0_EN.md        (English reference)
├── pipeline/               Multi-LLM screening → topic classification → R1 rule for Review pool
├── analysis/               Topic distribution, temporal trends, C9 subgroup, drug, modality, answer signals
├── validation/             Cohen's κ for screening, topic, and R1 rule against two retinal specialists
│   ├── README_validation.md     (Korean summary)
│   └── README_validation_EN.md  (English reference)
└── data/                   De-identified strict-AMD corpus (1,989 threads)
```

---

## Pipeline Overview

1. **Stage 1 — Keyword filter** (`pipeline/stage1_keyword_filter.py`)
   20,797 raw threads → 3,848 candidates (Korean AMD keyword filter).

2. **Stage 2 — Multi-LLM screening** (`pipeline/stage2_screening_run.py`)
   Claude Opus 4.7 + OpenAI Codex apply screening codebook v1.0 (G1–G7) to assign
   `Include_strict_AMD`, `Review_needed`, `Exclude_non_AMD`, or `Unclear`.

3. **Stage 3 — Tie-break + majority vote** (`pipeline/stage3_majority_vote.py`)
   Gemini 3 Pro resolves discordant cases; 2-of-3 majority voting yields
   1,836 strict-AMD threads (with 648 `Review_needed` retained).

4. **Stage 4 — Topic classification** (`pipeline/stage4_topic_classification_prompts.py`,
   `pipeline/stage4_topic_merge.py`)
   9-class multi-label classification (C1–C9) using topic codebook v1.0 with
   B1–B8 boundary rules.

5. **R1 rule for Review pool** (`pipeline/rule_R1_review_pool_v5b.py`)
   Resolves the 648-thread review pool: self-suspected, age-cue-absent cases
   without exclusion signals (test-normal, told-not-AMD, non-AMD cause, peripheral
   procedure, AMD-not-main) are reclassified as Include_strict_AMD (n=153).
   Final corpus: **1,989 strict-AMD threads**.

---

## Analysis Modules (`analysis/`)

| Module | Description |
|---|---|
| `corpus_construction.py` | Builds the 1,989-thread corpus **(requires non-public LLM intermediate outputs)** |
| `temporal_trends.py` | Per-period primary and any-mention rate tables (rates only; trend tests are in `cochran_armitage_trend.py`) |
| `c5_trajectory.py` | C5 period mention-share trajectory (reference; main-text Figure 3 plots the primary-topic rate) |
| `c9_subgroup.py` | Figure 4 — sub-category decomposition of C9 (S1–S7) |
| `drug_recognition.py` | Anti-VEGF agent mentions, Q vs A **(requires non-public answer text; not reproducible from the public CSV)** |
| `answer_signals.py` | 8 answer-text signals with PPV-validated lexicons **(requires non-public answer text)** |
| `modality_injection_nutrition.py` | Treatment modality, C4/C5 sub-concerns **(requires non-public answer text)** |
| `cochran_armitage_trend.py` | χ² independence + Cochran–Armitage trend tests (primary **and** any-mention) with BH-FDR |

---

## Validation (`validation/`)

| Track | Sample | Script |
|---|---|---|
| Screening (binary) | 200 balanced threads | `screening_kappa.py` |
| Topic (9-class) | 100 random threads | `topic_kappa.py` |
| Review-pool R1 rule (binary) | 100 balanced threads | `r1_rule_kappa.py` |

See `validation/README_validation.md` for the full validation summary table.

---

## De-identified Corpus (`data/strict_AMD_corpus_1989.csv`)

| Column | Description |
|---|---|
| `id` | Anonymized identifier (T-0001 to T-1989) |
| `question_year` | Year only (month/day removed for de-identification) |
| `category` | Naver Knowledge-iN category metadata |
| `question_title` | Question title (phone/email/URL redacted) |
| `question_content` | Question body (phone/email/URL redacted) |
| `primary_topic` | C1–C9 (single dominant intent) |
| `secondary_topics` | `;`-separated list of additional C-categories (multi-label) |
| `source` | `tri_llm_consensus` or `review_pool_R1_v5b` |

**Privacy**: Phone numbers, email addresses, and URLs are redacted with `[PHONE-REDACTED]`,
`[EMAIL-REDACTED]`, `[URL-REDACTED]` tokens. Original thread IDs are not provided.

**Redistribution**: The raw Naver Knowledge-iN threads themselves cannot be redistributed
due to platform terms of service. The de-identified CSV here is the analysis-ready derivative
deposited as a Multimedia Appendix to the paper.

---

## Figure Source Tables & Answer-Signal Lexicons

- **`tables/figure_source_tables_1989.md`** — per-figure aggregated source tables (counts and rates) recomputed on the final N=1,989 corpus, covering Figures 2–5 and S1–S6. These are the exact values plotted in the manuscript figures, allowing each figure to be reproduced and verified.
- **`codebook/answer_signal_lexicons.md`** — the full Korean keyword lexicons and refinement rules (refined detector v2) for the eight answer-ecosystem signals (manuscript Multimedia Appendix 2).

**Answer-signal precision (PPV)**: Positive predictive values were estimated by manually adjudicating 25 keyword-matched threads per signal (pooled PPV 70.5%, 95% CI 63.8–76.4; per-signal values reported in the paper). The raw adjudication snippets contain identifiable physician/clinic names and patient question text, so — consistent with the corpus de-identification policy above — they are **not redistributed**; the validated PPV summary in the paper is the reproducible artifact.

---

## Requirements

Python 3.12+

```bash
pip install -r requirements.txt
```

---

## Reproducing the Analyses

1. The de-identified corpus is already included at `data/strict_AMD_corpus_1989.csv`.
2. Generate the JSONL working file expected by the analysis scripts:
   ```bash
   python analysis/_csv_to_jsonl.py
   ```
   This produces `_stage4_topic_FINAL_v3_1989.jsonl` in the repository root (referenced by the public analysis scripts).
3. Run any module in `analysis/` or `validation/` from the repository root:
   ```bash
   python analysis/c9_subgroup.py
   python validation/topic_kappa.py
   ```

   **Reproducibility scope.** Topic-based analyses (`temporal_trends.py`, `cochran_armitage_trend.py`, `c5_trajectory.py`, `c9_subgroup.py`) run entirely from the public CSV. Answer-signal, drug-recognition, and modality analyses require the responder answer text, which cannot be redistributed under the platform's terms of service; their aggregate outputs are provided in `tables/figure_source_tables_1989.md`.
4. Re-running the pipeline from raw data (`pipeline/stage1` ~ `stage4`) requires:
   - Raw Naver Knowledge-iN dump (not redistributed — see Data Availability statement in the paper)
   - API keys for Anthropic (Claude Opus), OpenAI (Codex), Google (Gemini)

---

## License

MIT — see `LICENSE`.

---

## Citation

```
[Citation will be added upon publication]
```

---

## Contact

Daehwan Shin · https://github.com/Daehwan-Shin
E-mail: xtls0819@naver.com

---

## Acknowledgments

The authors thank the two retinal specialists who performed independent expert labeling
across all four validation tracks (binary screening, multi-label topic, R1 rule, and
inter-expert disagreement consensus).
