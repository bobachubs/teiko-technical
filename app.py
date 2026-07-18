import sqlite3
import streamlit as st
from analysis import get_frequency_table, run_stats, run_subset

st.set_page_config(
    page_title="Teiko Bio — Immune Cell Analysis",
    layout="wide",
    initial_sidebar_state="expanded"
)

# custom css
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #0f172a; }
    [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    .metric-card {
        background: #f0f7fa;
        border-left: 4px solid #0891b2;
        border-radius: 6px;
        padding: 16px 20px;
        margin-bottom: 12px;
    }
    .section-header {
        color: #0891b2;
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

con = sqlite3.connect("teiko.db")
freq_df = get_frequency_table(con)

# sidebar
with st.sidebar:
    st.markdown("### Teiko Bio")
    st.markdown("**Immune Cell Population Analysis**")
    st.divider()
    st.markdown("**Trial overview**")
    st.markdown("- 3 projects")
    st.markdown("- 3,500 subjects")
    st.markdown("- 10,500 samples")
    st.markdown("- 5 cell populations")
    st.divider()
    page = st.radio("Navigate", ["Frequency Table", "Statistical Analysis", "Subset Analysis"])

# Part 2
if page == "Frequency Table":
    st.markdown('<p class="section-header">Part 2 — Initial Analysis</p>', unsafe_allow_html=True)
    st.markdown("### Cell population frequencies per sample")
    st.markdown("Relative frequency of each immune cell population as a percentage of total cells per sample.")

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        pop_filter = st.multiselect("Population", options=sorted(freq_df["population"].unique()),
                                    default=sorted(freq_df["population"].unique()))
    with col2:
        sample_search = st.text_input("Search sample ID", "")
    with col3:
        st.metric("Total rows", f"{len(freq_df):,}")

    filtered = freq_df[freq_df["population"].isin(pop_filter)]
    if sample_search:
        filtered = filtered[filtered["sample"].str.contains(sample_search, case=False)]

    st.dataframe(
        filtered.style.format({"percentage": "{:.2f}%", "count": "{:,}", "total_count": "{:,}"}),
        use_container_width=True,
        height=520
    )
    st.caption(f"Showing {len(filtered):,} of {len(freq_df):,} rows")

# Part 3
elif page == "Statistical Analysis":
    st.markdown('<p class="section-header">Part 3 — Statistical Analysis</p>', unsafe_allow_html=True)
    st.markdown("### Responders vs non-responders")
    st.markdown("Melanoma patients on **miraclib**, PBMC samples only. Mann-Whitney U test (two-sided, α = 0.05).")

    with st.spinner("Running analysis..."):
        stats_df = run_stats(freq_df, con)

    sig = stats_df[stats_df["significant"]]["population"].tolist()
    not_sig = stats_df[~stats_df["significant"]]["population"].tolist()

    col1, col2 = st.columns(2)
    with col1:
        if sig:
            st.success(f"Significant (p < 0.05): **{', '.join(sig)}**")
        else:
            st.info("No populations significant at p < 0.05")
    with col2:
        st.info(f"Not significant: {', '.join(not_sig)}")

    st.image("boxplot_part3.png", use_container_width=True)

    st.markdown("#### Statistical results")
    st.dataframe(
        stats_df.style.format({
            "responder_median": "{:.4f}",
            "non_responder_median": "{:.4f}",
            "p_value": "{:.4f}"
        }).apply(lambda x: ["background-color: #dcfce7" if v else "" for v in x], subset=["significant"]),
        use_container_width=True,
        hide_index=True
    )

# Part 4
elif page == "Subset Analysis":
    st.markdown('<p class="section-header">Part 4 — Subset Analysis</p>', unsafe_allow_html=True)
    st.markdown("### Melanoma · PBMC · baseline (day 0) · miraclib")

    subset = run_subset(con)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Samples per project**")
        st.dataframe(subset["proj_counts"], use_container_width=True, hide_index=True)
    with col2:
        st.markdown("**Subjects by response**")
        st.dataframe(subset["resp_counts"], use_container_width=True, hide_index=True)
    with col3:
        st.markdown("**Subjects by sex**")
        st.dataframe(subset["sex_counts"], use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("**Average B cell count — melanoma male responders, time = 0 (all sample & treatment types)**")
    st.markdown(
        f'<div class="metric-card"><span style="font-size:2rem;font-weight:700;color:#0891b2;">'
        f'{subset["avg_b_cell"]:,.2f}</span><br>'
        f'<span style="color:#64748b;font-size:0.85rem;">cells per sample</span></div>',
        unsafe_allow_html=True
    )

con.close()
