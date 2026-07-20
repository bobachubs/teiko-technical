# Teiko Bio — Clinical Trial Immune Cell Analysis

Analysis pipeline and interactive dashboard for Bob Loblaw's clinical trial immune cell profiling data.

**Live dashboard:** https://teiko-technical-sarah.streamlit.app/

---

## Quickstart

```bash
make setup      # install dependencies
make pipeline   # build database and run all analyses
make dashboard  # launch the Streamlit app at http://localhost:8501
```

Tested with Python 3.11. Works in GitHub Codespaces with no additional setup.

---

## Project structure

```
.
├── load_data.py          # Part 1 — schema DDL + CSV → SQLite ETL
├── analysis.py           # Parts 2–4 — all analytical functions
├── app.py                # Streamlit dashboard
├── EDA.ipynb             # Exploratory data analysis notebook
├── cell-count.csv        # Source data
├── frequency_table.csv   # Output: per-sample cell population frequencies
├── boxplot_part3.png     # Output: responder vs non-responder boxplot
├── requirements.txt
├── Makefile
└── README.md
```

---

## Running in GitHub Codespaces

Open the repository in a Codespace, then in the terminal:

```bash
make setup
make pipeline
make dashboard
```

Codespaces will prompt you to open the forwarded port (8501) in a browser tab. If it does not appear automatically, go to the **Ports** tab and click the link next to port 8501.

---

## Database schema

`load_data.py` creates `teiko.db` with four tables:

```
projects  ──< subjects  ──< samples  ──< cell_counts
```

| Table | Primary key | Key columns |
|---|---|---|
| `projects` | `project_id` | — |
| `subjects` | `subject_id` | `project_id`, `condition`, `age`, `sex`, `treatment`, `response` |
| `samples` | `sample_id` | `subject_id`, `sample_type`, `time_from_treatment_start` |
| `cell_counts` | `id` (autoincrement) | `sample_id`, `population`, `count` |

**Design rationale**

The raw CSV stores one row per sample, so subject-level fields (`condition`, `sex`, `treatment`, `response`) repeat across every sample for that subject. Keeping it flat means a single update to a subject's response status requires touching every one of their rows. Splitting into `subjects` and `samples` eliminates that redundancy.

Cell counts are stored in **long format** (one row per population per sample) rather than five separate columns — adding a new cell population requires no schema change, only new rows.

`treatment` and `response` live on `subjects` rather than `samples` because they're constant per patient, which I confirmed in EDA (no subject has conflicting values across their samples).

**Indexes** are on all foreign key columns (`project_id`, `subject_id`, `sample_id`) and on `cell_counts.population`, so common filters (e.g., "all CD4 T cells from melanoma PBMC samples") hit indexes rather than full scans.

**Scaling**

The `cell_counts` table grows linearly with samples × populations — at 5 populations per sample, a million-sample dataset produces 5 million rows, which is well within SQLite's range and straightforward to migrate to PostgreSQL. Adding new metadata fields (tissue site, batch ID, etc.) means a column on `subjects` or `samples` with no changes to `cell_counts`. If query latency becomes a bottleneck, a pre-aggregated `frequencies` view can be layered on top without touching the base schema. For a full analytics-at-scale setup, the normalized schema maps directly to a star schema in BigQuery or Snowflake: `cell_counts` as the fact table, everything else as dimensions.

---

## Code structure

**`load_data.py`** — ETL script. Defines the schema as a DDL string, creates the tables, then loads `cell-count.csv` into the four normalized tables using pandas. Running `make pipeline` deletes `teiko.db` first, so it's always a clean rebuild.

**`analysis.py`** — all analytical logic, organized by part:

- `get_frequency_table(con)` — Part 2: SQL window function computes total count per sample, then calculates each population's percentage.
- `check_groups(freq_df, con)` — Part 3 support: prints group sizes and plots per-population distributions to assess statistical test assumptions.
- `run_stats(freq_df, con)` — Part 3: Mann-Whitney U test (two-sided, α = 0.05) for each population; saves `boxplot_part3.png`.
- `compare_tests(freq_df, con)` — Part 3 validation: runs Welch's t-test alongside Mann-Whitney to confirm the results hold regardless of test choice.
- `run_subset(con)` — Part 4: baseline melanoma/miraclib/PBMC subset queries.

Functions are stateless (connection and/or dataframe in, results out) so they're easy to test independently. The `if __name__ == "__main__"` block runs the full pipeline and saves all outputs.

**`app.py`** — Streamlit dashboard with four pages mirroring the four parts of the analysis. Uses `@st.cache_data` throughout to avoid redundant computation on navigation. Chart colors follow a consistent semantic palette (red = responders / active, gray = non-responders / healthy) defined once and reused across all plots.

**`EDA.ipynb`** — exploratory notebook walking through the full analysis from raw data to results. Covers data structure validation, schema design decisions, EDA visualizations, and the reasoning behind the statistical test selection. Good to read alongside the dashboard.

---

## Key findings

Only **CD4 T cell frequency** is significantly different between responders and non-responders in melanoma patients treated with miraclib (PBMC samples, all timepoints):

- **CD4 T cells**: p = 0.0133 (Mann-Whitney U, two-sided) — higher in responders
- **B cells**: p = 0.056 — borderline, lower in responders, warrants further investigation
- All other populations (CD8 T cells, NK cells, monocytes): no significant difference

Results are consistent across both Mann-Whitney U and Welch's t-test for all five populations, so the finding holds regardless of which test is used.
