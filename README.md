# Teiko Bio — Clinical Trial Immune Cell Analysis

Interactive dashboard and analysis pipeline for Bob Loblaw's clinical trial immune cell profiling data.

**Live dashboard:** https://teiko-technical-sarah.streamlit.app/

---

## Quickstart

```bash
make setup      # install dependencies
make pipeline   # build database and run all analyses
make dashboard  # launch the Streamlit app at http://localhost:8501
```

Tested with Python 3.11. All three commands are designed to run in GitHub Codespaces without any manual steps.

---

## Project structure

```
.
├── load_data.py          # Part 1 — schema DDL + CSV → SQLite ETL
├── analysis.py           # Parts 2–4 — all analytical functions
├── app.py                # Streamlit dashboard
├── testing.ipynb         # Exploratory analysis notebook
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

**Why this structure?**

The raw CSV has one row per sample, with subject-level fields (`condition`, `sex`, `treatment`, `response`) repeated across every sample for that subject. Storing this flat would mean updating a subject's response status requires touching every one of their sample rows — a consistency risk. Splitting into `subjects` and `samples` normalizes that away.

Cell counts are stored in **long format** (one row per population per sample) rather than five separate columns. This means adding a new cell population — NK subsets, regulatory T cells, etc. — requires no schema change, only new rows.

`treatment` and `response` live on `subjects` rather than `samples` because they are constant per patient (confirmed in EDA: no subject ever has conflicting values across their samples).

**Indexes** are created on all foreign key columns (`project_id`, `subject_id`, `sample_id`) and on `cell_counts.population`, so common filter patterns (e.g., "all CD4 T cells from melanoma PBMC samples") hit indexes rather than full scans.

**How this scales**

With hundreds of projects, thousands of subjects, and millions of cell count rows, the design holds well for several reasons:

- The `cell_counts` table grows linearly with samples × populations. At 5 populations per sample, a dataset with 1 million samples produces 5 million rows — well within SQLite's practical range, and straightforward to migrate to PostgreSQL if needed.
- Analytical queries that group by `population` and join to `subjects` for filtering are fully covered by the existing indexes.
- Adding new metadata (e.g., tissue site, batch ID) means adding a column to `subjects` or `samples` without touching `cell_counts`.
- If query performance becomes a bottleneck, a pre-aggregated `frequencies` view (or materialized table) caching `percentage` per sample can be added without changing the base schema — this is essentially what `get_frequency_table()` computes on demand today.
- For a true analytics-at-scale scenario (many concurrent users, sub-second dashboards), the normalized schema translates directly to a star schema in a columnar warehouse (BigQuery, Snowflake): `cell_counts` becomes the fact table; `projects`, `subjects`, and `samples` become dimension tables.

---

## Code structure

**`load_data.py`** — self-contained ETL script. Defines the schema as a DDL string, creates the tables, then loads `cell-count.csv` into the four normalized tables using pandas. Idempotent when called via `make pipeline` (the Makefile deletes `teiko.db` first).

**`analysis.py`** — all analytical logic, organized by part:

- `get_frequency_table(con)` — Part 2: SQL window function computes total count per sample, then calculates each population's percentage.
- `check_groups(freq_df, con)` — Part 3 support: prints group sizes and plots per-population distributions to assess statistical test assumptions.
- `run_stats(freq_df, con)` — Part 3: Mann-Whitney U test (two-sided, α = 0.05) for each population; saves `boxplot_part3.png`.
- `compare_tests(freq_df, con)` — Part 3 validation: runs Welch's t-test alongside Mann-Whitney to confirm findings are not an artefact of test choice.
- `run_subset(con)` — Part 4: baseline melanoma/miraclib/PBMC subset queries.

Functions are kept stateless (they take a connection and/or dataframe, return results) so they compose cleanly and are independently testable. The `if __name__ == "__main__"` block runs the full pipeline and saves all outputs.

**`app.py`** — Streamlit dashboard with four pages mirroring the four parts of the analysis. Uses `@st.cache_data` throughout to avoid redundant computation on navigation. Chart colors follow a consistent semantic palette (red = responders / active, gray = non-responders / healthy) defined once and reused across all plots.

**`testing.ipynb`** — exploratory notebook used to understand the data structure, validate schema design decisions, and develop the statistical approach before formalizing into `analysis.py`.

---

## Key findings

Only **CD4 T cell frequency** is significantly different between responders and non-responders in melanoma patients treated with miraclib (PBMC samples, all timepoints):

- **CD4 T cells**: p = 0.0133 (Mann-Whitney U, two-sided) — higher in responders
- **B cells**: p = 0.056 — borderline, lower in responders, warrants further investigation
- All other populations (CD8 T cells, NK cells, monocytes): no significant difference

Results are consistent across both Mann-Whitney U and Welch's t-test for all five populations, confirming the finding is not driven by distributional assumptions or variance differences between groups.
