import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import mannwhitneyu, ttest_ind

DB_PATH = "teiko.db"
cell_pops = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]


# Part 2 - frequency table

def get_frequency_table(con):
    # compute total cell count per sample, then get % per population
    query = """
        SELECT
            s.sample_id AS sample,
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


# Part 3 - compare responders vs non-responders in melanoma/miraclib/PBMC

def get_filtered_df(freq_df, con):
    # returns freq_df filtered to melanoma + miraclib + PBMC with response labels attached
    samples = pd.read_sql_query("""
        SELECT s.sample_id AS sample, su.response
        FROM samples s
        JOIN subjects su ON s.subject_id = su.subject_id
        WHERE su.condition = 'melanoma'
          AND su.treatment = 'miraclib'
          AND s.sample_type = 'PBMC'
    """, con)
    return freq_df.merge(samples, on="sample")


def check_groups(freq_df, con):
    # print group sizes and show distribution of each population by response
    df = get_filtered_df(freq_df, con)

    # all populations share the same set of samples, so count on any one is representative
    sample_counts = df[df["population"] == cell_pops[0]]["response"].value_counts()
    print("Samples per group (each subject contributes 3 rows — one per timepoint):")
    print(sample_counts.to_string())

    # subject counts — unique patients per response group
    subj = pd.read_sql_query("""
        SELECT DISTINCT s.sample_id, su.subject_id, su.response
        FROM samples s
        JOIN subjects su ON s.subject_id = su.subject_id
        WHERE su.condition = 'melanoma'
          AND su.treatment = 'miraclib'
          AND s.sample_type = 'PBMC'
    """, con)
    subj_counts = subj.drop_duplicates("subject_id")["response"].value_counts()
    print("\nSubjects per group (unique patients):")
    print(subj_counts.to_string())
    print(f"\nNote: test runs on {sample_counts.sum()} samples from {subj_counts.sum()} subjects")

    fig, axes = plt.subplots(2, 5, figsize=(18, 7))
    for i, pop in enumerate(cell_pops):
        tmp = df[df["population"] == pop]
        # top row: histogram
        for resp, grp in tmp.groupby("response"):
            axes[0][i].hist(grp["percentage"], bins=25, alpha=0.6,
                            label=resp, color="#51cf66" if resp == "yes" else "#ff6b6b",
                            edgecolor="none")
        axes[0][i].set_title(pop.replace("_", " "), fontsize=9)
        axes[0][i].set_xlabel("% of total")
        axes[0][i].set_ylabel("count" if i == 0 else "")
        if i == 0:
            axes[0][i].legend(title="response", fontsize=7)

        # bottom row: KDE (smoothed distribution)
        for resp, grp in tmp.groupby("response"):
            grp["percentage"].plot.kde(ax=axes[1][i], label=resp,
                                       color="#51cf66" if resp == "yes" else "#ff6b6b")
        axes[1][i].set_xlabel("% of total")
        axes[1][i].set_ylabel("density" if i == 0 else "")

    plt.suptitle("Distribution of cell population frequencies by response\n(melanoma, miraclib, PBMC)",
                 y=1.02, fontsize=11)
    plt.tight_layout()
    plt.show()


def run_stats(freq_df, con, plot_path="boxplot_part3.png"):
    df = get_filtered_df(freq_df, con)

    # Mann-Whitney U for each population
    rows = []
    for pop in cell_pops:
        tmp = df[df["population"] == pop]
        yes = tmp[tmp["response"] == "yes"]["percentage"]
        no = tmp[tmp["response"] == "no"]["percentage"]
        _, p = mannwhitneyu(yes, no, alternative="two-sided")
        rows.append({
            "population": pop,
            "responder_median": round(yes.median(), 4),
            "non_responder_median": round(no.median(), 4),
            "p_value": round(p, 4),
            "significant": p < 0.05
        })

    stats = pd.DataFrame(rows)

    fig, axes = plt.subplots(1, 5, figsize=(18, 5))
    colors = {"yes": "#51cf66", "no": "#ff6b6b"}

    for ax, pop in zip(axes, cell_pops):
        tmp = df[df["population"] == pop]
        sns.boxplot(
            data=tmp, x="response", y="percentage",
            hue="response", palette=colors, order=["yes", "no"],
            legend=False, width=0.5, ax=ax,
            flierprops=dict(marker="o", markersize=2, alpha=0.4)
        )
        p_val = stats[stats["population"] == pop]["p_value"].values[0]
        label = "*" if p_val < 0.05 else "ns"
        ax.set_title(f"{pop.replace('_', ' ')}\np={p_val} {label}", fontsize=9)
        ax.set_xlabel("response")
        ax.set_ylabel("% of total" if ax == axes[0] else "")

    plt.suptitle(
        "Cell population frequencies: responders vs non-responders (melanoma, miraclib, PBMC)",
        y=1.02, fontsize=11
    )
    plt.tight_layout()
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.show()

    print("\nMann-Whitney U results:")
    print(stats.to_string(index=False))
    return stats


def compare_tests(freq_df, con):
    # run both Mann-Whitney and Welch's t-test side by side to check consistency
    df = get_filtered_df(freq_df, con)

    rows = []
    for pop in cell_pops:
        tmp = df[df["population"] == pop]
        yes = tmp[tmp["response"] == "yes"]["percentage"]
        no  = tmp[tmp["response"] == "no"]["percentage"]

        _, p_mw  = mannwhitneyu(yes, no, alternative="two-sided")
        _, p_t   = ttest_ind(yes, no, equal_var=False)  # equal_var=False = Welch's

        rows.append({
            "population":   pop,
            "responder_median":     round(yes.median(), 4),
            "non_responder_median": round(no.median(), 4),
            "p_mannwhitney": round(p_mw, 4),
            "p_welch":       round(p_t, 4),
            "sig_mw":  p_mw < 0.05,
            "sig_welch": p_t < 0.05,
            "consistent": (p_mw < 0.05) == (p_t < 0.05)
        })

    result = pd.DataFrame(rows)
    print("Mann-Whitney vs Welch's t-test comparison:")
    print(result.to_string(index=False))
    return result


# Part 4 - subset queries

def run_subset(con):
    # melanoma PBMC samples at baseline treated with miraclib
    baseline = pd.read_sql_query("""
        SELECT s.sample_id, su.subject_id, su.project_id, su.response, su.sex
        FROM samples s
        JOIN subjects su ON s.subject_id = su.subject_id
        WHERE su.condition = 'melanoma'
          AND s.sample_type = 'PBMC'
          AND s.time_from_treatment_start = 0
          AND su.treatment = 'miraclib'
    """, con)

    proj_counts = baseline.groupby("project_id")["sample_id"].count().reset_index()
    proj_counts.columns = ["project", "n_samples"]

    subj = baseline.drop_duplicates("subject_id")
    resp_counts = subj["response"].value_counts().reset_index()
    resp_counts.columns = ["response", "n_subjects"]

    sex_counts = subj["sex"].value_counts().reset_index()
    sex_counts.columns = ["sex", "n_subjects"]

    # avg b cells for melanoma male responders at time=0, all sample/treatment types
    avg_b = pd.read_sql_query("""
        SELECT ROUND(AVG(cc.count), 2) AS avg_b_cell
        FROM cell_counts cc
        JOIN samples s ON cc.sample_id = s.sample_id
        JOIN subjects su ON s.subject_id = su.subject_id
        WHERE cc.population = 'b_cell'
          AND su.condition = 'melanoma'
          AND su.sex = 'M'
          AND su.response = 'yes'
          AND s.time_from_treatment_start = 0
    """, con)["avg_b_cell"].values[0]

    print("Samples per project:")
    print(proj_counts.to_string(index=False))
    print("\nSubjects by response:")
    print(resp_counts.to_string(index=False))
    print("\nSubjects by sex:")
    print(sex_counts.to_string(index=False))
    print(f"\nAvg B cells (melanoma male responders, time=0, all samples/treatments): {avg_b}")

    return {
        "baseline": baseline,
        "proj_counts": proj_counts,
        "resp_counts": resp_counts,
        "sex_counts": sex_counts,
        "avg_b_cell": avg_b
    }


if __name__ == "__main__":
    con = sqlite3.connect(DB_PATH)

    print("Part 2 - Frequency Table")
    freq_df = get_frequency_table(con)
    print(freq_df.head(10).to_string(index=False))
    freq_df.to_csv("frequency_table.csv", index=False)
    print(f"\nSaved frequency_table.csv ({len(freq_df):,} rows)")

    print("\nPart 3 - Statistical Analysis")
    stats_df = run_stats(freq_df, con)

    print("\nPart 4 - Subset Analysis")
    subset = run_subset(con)

    con.close()
