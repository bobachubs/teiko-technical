import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import mannwhitneyu

DB_PATH = "teiko.db"
CELL_POPULATIONS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]


# Part 2

def get_frequency_table(con: sqlite3.Connection) -> pd.DataFrame:
    """
    Returns a long-format frequency table with one row per population per sample.
    Columns: sample, total_count, population, count, percentage
    """
    query = """
        SELECT
            s.sample_id      AS sample,
            cc.population,
            cc.count,
            SUM(cc.count) OVER (PARTITION BY s.sample_id) AS total_count
        FROM samples s
        JOIN cell_counts cc ON s.sample_id = cc.sample_id
        ORDER BY s.sample_id, cc.population
    """
    df = pd.read_sql_query(query, con)
    df["percentage"] = (df["count"] / df["total_count"] * 100).round(4)
    return df[["sample", "total_count", "population", "count", "percentage"]]


# Part 3

def run_stats(freq_df: pd.DataFrame, con: sqlite3.Connection,
              output_plot: str = "boxplot_part3.png") -> pd.DataFrame:
    """
    Compares cell population frequencies between responders and non-responders
    for melanoma patients on miraclib using PBMC samples only.
    Runs Mann-Whitney U test per population and saves a boxplot.
    Returns a DataFrame of statistical results.
    """
    # pull sample metadata to filter correctly
    meta = pd.read_sql_query("""
        SELECT
            s.sample_id,
            s.sample_type,
            s.time_from_treatment_start,
            su.condition,
            su.treatment,
            su.response
        FROM samples s
        JOIN subjects su ON s.subject_id = su.subject_id
    """, con)

    filtered_meta = meta[
        (meta["condition"] == "melanoma") &
        (meta["treatment"] == "miraclib") &
        (meta["sample_type"] == "PBMC")
    ][["sample_id", "response"]].rename(columns={"sample_id": "sample"})

    df = freq_df.merge(filtered_meta, on="sample")

    results = []
    for pop in CELL_POPULATIONS:
        pop_df = df[df["population"] == pop]
        responders = pop_df[pop_df["response"] == "yes"]["percentage"]
        non_responders = pop_df[pop_df["response"] == "no"]["percentage"]
        stat, p = mannwhitneyu(responders, non_responders, alternative="two-sided")
        results.append({
            "population": pop,
            "responder_median": round(responders.median(), 4),
            "non_responder_median": round(non_responders.median(), 4),
            "p_value": round(p, 4),
            "significant": p < 0.05
        })

    results_df = pd.DataFrame(results)

    # boxplot
    fig, axes = plt.subplots(1, 5, figsize=(18, 5), sharey=False)
    palette = {"yes": "#51cf66", "no": "#ff6b6b"}

    for ax, pop in zip(axes, CELL_POPULATIONS):
        pop_df = df[df["population"] == pop]
        sns.boxplot(
            data=pop_df, x="response", y="percentage",
            hue="response", palette=palette, order=["yes", "no"],
            legend=False, width=0.5, ax=ax,
            flierprops=dict(marker="o", markersize=2, alpha=0.4)
        )
        p_val = results_df[results_df["population"] == pop]["p_value"].values[0]
        sig = "*" if p_val < 0.05 else "ns"
        ax.set_title(f"{pop.replace('_', ' ')}\np={p_val} {sig}", fontsize=9)
        ax.set_xlabel("response")
        ax.set_ylabel("% of total" if ax == axes[0] else "")

    plt.suptitle(
        "Cell population frequencies: responders vs non-responders\n"
        "(melanoma · miraclib · PBMC)",
        y=1.02, fontsize=11
    )
    plt.tight_layout()
    plt.savefig(output_plot, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"Boxplot saved to {output_plot}")

    print("\nStatistical results (Mann-Whitney U, two-sided):")
    print(results_df.to_string(index=False))
    return results_df


# Part 4

def run_subset(con: sqlite3.Connection) -> dict:
    """
    Filters melanoma PBMC samples at baseline (time=0) treated with miraclib.
    Returns counts per project, response, and sex, plus average B cells
    for melanoma male responders at time=0 across all sample/treatment types.
    """
    base_query = """
        SELECT
            s.sample_id,
            s.sample_type,
            s.time_from_treatment_start,
            su.subject_id,
            su.project_id,
            su.condition,
            su.treatment,
            su.response,
            su.sex
        FROM samples s
        JOIN subjects su ON s.subject_id = su.subject_id
        WHERE su.condition    = 'melanoma'
          AND s.sample_type   = 'PBMC'
          AND s.time_from_treatment_start = 0
          AND su.treatment    = 'miraclib'
    """
    baseline = pd.read_sql_query(base_query, con)

    samples_per_project = baseline.groupby("project_id")["sample_id"].count().reset_index()
    samples_per_project.columns = ["project", "sample_count"]

    subjects = baseline.drop_duplicates("subject_id")
    response_counts = subjects["response"].value_counts().reset_index()
    response_counts.columns = ["response", "subject_count"]

    sex_counts = subjects["sex"].value_counts().reset_index()
    sex_counts.columns = ["sex", "subject_count"]

    # average B cells: melanoma males, responders, time=0, ALL sample and treatment types
    # quintazide
    avg_b_query = """
        SELECT ROUND(AVG(cc.count), 2) AS avg_b_cell
        FROM cell_counts cc
        JOIN samples s   ON cc.sample_id   = s.sample_id
        JOIN subjects su ON s.subject_id   = su.subject_id
        WHERE cc.population              = 'b_cell'
          AND su.condition               = 'melanoma'
          AND su.sex                     = 'M'
          AND su.response                = 'yes'
          AND s.time_from_treatment_start = 0
    """
    avg_b_cell = pd.read_sql_query(avg_b_query, con)["avg_b_cell"].values[0]

    print("=== Part 4: Subset Analysis ===")
    print("\nSamples per project (melanoma · PBMC · baseline · miraclib):")
    print(samples_per_project.to_string(index=False))
    print("\nSubjects by response:")
    print(response_counts.to_string(index=False))
    print("\nSubjects by sex:")
    print(sex_counts.to_string(index=False))
    print(f"\nAvg B cells (melanoma · male · responder · time=0, all sample/treatment types): {avg_b_cell}")

    return {
        "baseline_samples": baseline,
        "samples_per_project": samples_per_project,
        "response_counts": response_counts,
        "sex_counts": sex_counts,
        "avg_b_cell": avg_b_cell
    }


# --- Pipeline entry point ---

if __name__ == "__main__":
    con = sqlite3.connect(DB_PATH)

    print("=== Part 2: Frequency Table ===")
    freq_df = get_frequency_table(con)
    print(freq_df.head(10).to_string(index=False))
    freq_df.to_csv("frequency_table.csv", index=False)
    print(f"\nFull table saved to frequency_table.csv ({len(freq_df):,} rows)")

    print("\n=== Part 3: Statistical Analysis ===")
    stats_df = run_stats(freq_df, con)

    print("\n")
    subset = run_subset(con)

    con.close()