# AMD-KIN-infodemiology

Reproducibility materials for:

> **Age-Related Macular Degeneration Questions and the Online Answer Ecosystem on a Korean Public Q&A Platform:**
> **An Infodemiology Study Using a Multi-LLM Consensus Pipeline**

Target journal: *JMIR Public Health and Surveillance*.

## Study snapshot

- Final codebook-defined strict AMD corpus: **1,989 threads**
- Source platform: Naver Knowledge-iN
- Post dates: 2004 through April 9, 2026; 2026 is a partial year
- Screening pipeline: Opus 4.7, Codex gpt-5.5, and Gemini 3 Pro
- Independent expert-comparison samples: binary screening (n=200) and primary-topic classification (n=100)
- Review-pool R1 rule: separate **internal agreement assessment** (n=100)
- Topic coding: one primary topic plus optional secondary topics across C1-C9

## Repository structure

```text
.
├── analysis/       public-corpus analyses and reproducibility checks
├── codebook/       released screening and topic codebooks v1.0
├── crawler/        crawler and export workflow; no crawl output or credentials
├── data/           deidentified strict AMD corpus (N=1,989)
├── pipeline/       keyword filtering, model prompting/merging, and review-pool rule
├── tables/         aggregate source tables used for main and supplementary figures
└── validation/     aggregate confusion matrices, scripts, and validation summaries
```

## Pipeline

1. Keyword filtering reduced 20,797 retrieved threads to 3,848 candidates.
2. Opus 4.7 and Codex independently applied the released screening codebook v1.0.
3. Gemini adjudicated disagreements; 2-of-3 majority voting produced 1,836 strict AMD threads.
4. The final R1 clinical-review rule resolved a 648-thread review pool, adding 153 threads.
5. The final strict AMD corpus contained **1,989 threads**.
6. Opus and Codex assigned primary and optional secondary topic labels; Gemini adjudicated discordant primary labels, and 26 residual cases were finalized by two-expert consensus.

Internal code values such as `Include_strict_AMD`, `Review_needed`, and
`Exclude_non_AMD` are retained in scripts for compatibility. The manuscript uses the
reader-facing terms strict AMD, clinical review, and non-AMD.

## Reproducibility scope

### Fully reproducible from the released corpus

- corpus QC and duplicate-content sensitivity analysis
- primary-topic and any-mention distributions
- four-period primary-topic tables
- calendar-year Cochran-Armitage trend tests with BH correction
- global primary-topic chi-square and Cramer's V

Run:

```bash
python analysis/reproduce_public_results.py --output public_reproducibility_report.json
```

### Reproducible from public aggregate counts

- screening, topic, and review-pool agreement statistics
- C9 S1-S7 source values used in Figure 4
- answer-text, drug, modality, C4, and C5 source values used in the manuscript figures

Run:

```bash
python validation/reproduce_aggregate_validation.py
```

The validation JSON contains only aggregate confusion matrices; it includes no record
identifiers or text.

### Requires retained nonpublic inputs

- re-running the complete multi-LLM pipeline requires the raw crawl, intermediate model outputs, and API access
- exact row-level C9 S1-S7 assignment requires retained LLM rationales
- answer-text, drug, and treatment-modality detection requires captured answer text
- row-level expert-validation scripts require expert review workbooks

For analyses in this category, public aggregate source tables define the reproducibility
boundary. The repository does not imply that all analyses can be regenerated from the
released question-only CSV.

## Released corpus

`data/strict_AMD_corpus_1989.csv` contains:

| Column | Description |
|---|---|
| `id` | anonymized identifier T-0001 to T-1989 |
| `question_year` | year only |
| `category` | platform category metadata |
| `question_title` | deidentified title |
| `question_content` | deidentified body |
| `primary_topic` | one C1-C9 dominant topic |
| `secondary_topics` | semicolon-separated additional topics |
| `source` | tri-LLM consensus or review-pool rule |

Original platform IDs, URLs, author names, captured answer text, and full raw crawl are not
included. Public text can still carry reidentification risk through search; users should
apply appropriate ethics and platform-governance review before redistributing derivatives.

## Figure source tables

- `tables/figure_source_tables_1989.md`: final counts, percentages, trend results, and reported PPVs
- `tables/c9_subgroup_source_table.csv`: exact aggregate values for Figure 4
- `codebook/answer_signal_lexicons.md`: Korean keyword lexicons and v2 refinement rules

Regenerate the neutral, submission-oriented Figures 2-5 with:

```bash
python figures/build_main_figures.py \
  --corpus data/strict_AMD_corpus_1989.csv \
  --c9-source tables/c9_subgroup_source_table.csv \
  --output figures/generated
```

The reported answer-signal PPVs are author-adjudicated values. Row-level adjudication text
is not publicly redistributed.

## Crawler

The scripts under `crawler/` document the collection workflow. A live rerun can differ as
platform indexing, deleted posts, HTML structure, and API behavior change. See
`crawler/README.md` and `crawler/사용가이드.txt`.

## Model and codebook provenance

- Anthropic: `claude-opus-4-7`
- OpenAI: Codex CLI v0.130.0 with `gpt-5.5`, medium reasoning effort
- Google: `gemini-3-pro-preview`, server-resolved as `gemini-3.1-pro-preview`
- Released screening codebook v1.0: frozen G1-G7 rule set
- Released topic codebook v1.0: frozen B1-B8 rule set

Model-based screening and adjudication occurred May 13-14, 2026; topic model runs occurred
May 18, 2026; final corpus refinements were completed by May 26, 2026.

## Setup

```bash
pip install -r requirements.txt
python analysis/_csv_to_jsonl.py
```

The second command creates the public question-only JSONL used by several legacy analysis
modules. Modules requiring answer text or internal model rationales will report or document
that additional input boundary.

## Citation

```text
[Citation will be added upon publication]
```

## Contact

Daehwan Shin: https://github.com/Daehwan-Shin
