import base64
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
from analysis import get_frequency_table, run_stats, run_subset

pd.set_option("styler.render.max_elements", 500000)

st.set_page_config(page_title="Teiko Bio", layout="wide", initial_sidebar_state="collapsed")

pages = ["Home", "Frequency Table", "Statistical Analysis", "Subset Analysis"]
if "page" not in st.session_state:
    st.session_state.page = "Home"

_active_col = pages.index(st.session_state.page) + 2  # 1-based; col1=logo, cols2-5=nav

with open("teiko_logo_inverted.svg", "r") as _f:
    _svg = _f.read()
    _svg = _svg.replace("fill:#020202", "fill:#ffffff")
    # crop extra top whitespace so visual center aligns with img geometric center
    _svg = _svg.replace('viewBox="0 0 961.20837 218.29204"', 'viewBox="0 8 961.20837 212"')
    _svg = _svg.replace('height="218.29202"', 'height="212"')
_logo_b64 = base64.b64encode(_svg.encode()).decode()
_logo_mime = "image/svg+xml"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@700;800&family=Public+Sans:wght@400;500;600;700&display=swap');

*, html, body, [class*="css"] {{
    font-family: 'Public Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}}

#MainMenu, header, footer, [data-testid="collapsedControl"] {{ display: none !important; }}

.block-container {{
    padding-top: 0 !important;
    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
    max-width: 1400px !important;
    margin: 0 auto !important;
}}

/* ── NAV BAR — Teiko grey-900 ── */
[data-testid="stHorizontalBlock"]:first-of-type {{
    background: #141A21 !important;
    margin-left: -2.5rem !important;
    margin-right: -2.5rem !important;
    padding: 0 2.5rem !important;
    border-bottom: 1px solid #1C252E !important;
    min-height: 64px !important;
    align-items: center !important;
}}

/* nav buttons — no chrome */
[data-testid="stHorizontalBlock"]:first-of-type [data-testid="stButton"] > button {{
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    box-shadow: none !important;
    border-radius: 0 !important;
    font-family: 'Public Sans', sans-serif !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    color: #637381 !important;
    padding: 22px 14px 20px !important;
    width: 100% !important;
    letter-spacing: 0.02em !important;
    transition: color 0.15s !important;
}}
[data-testid="stHorizontalBlock"]:first-of-type [data-testid="stButton"] > button p {{
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    color: inherit !important;
    margin: 0 !important;
}}
[data-testid="stHorizontalBlock"]:first-of-type [data-testid="stButton"] > button:hover {{
    color: #ffffff !important;
    background: transparent !important;
    border-bottom-color: #454F5B !important;
}}
[data-testid="stHorizontalBlock"]:first-of-type [data-testid="stButton"] > button:focus,
[data-testid="stHorizontalBlock"]:first-of-type [data-testid="stButton"] > button:active {{
    box-shadow: none !important;
    outline: none !important;
    background: transparent !important;
}}

/* active nav item */
[data-testid="stHorizontalBlock"]:first-of-type
[data-testid="stColumn"]:nth-child({_active_col})
[data-testid="stButton"] > button {{
    color: #ffffff !important;
    border-bottom: 2px solid #FF3030 !important;
    background: rgba(255,48,48,0.1) !important;
}}

/* override Streamlit's emotion-generated CSS variables at root */
:root {{
    --secondary-background-color: #F4F6F8 !important;
    --background-color: #F4F6F8 !important;
}}
/* strip every layer of the plotly chart container */
[data-testid="stPlotlyChart"],
[data-testid="stPlotlyChart"] > div,
[data-testid="stPlotlyChart"] > div > div,
.js-plotly-plot,
.js-plotly-plot .plotly,
.plot-container {{
    background: #F4F6F8 !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}}
/* transparent wrappers — page bg shows through */
[data-testid="stElementContainer"],
[data-testid="element-container"] {{
    background: transparent !important;
}}

/* logo column — flex chain all the way down to the img */
[data-testid="stHorizontalBlock"]:first-of-type
[data-testid="stColumn"]:first-child,
[data-testid="stHorizontalBlock"]:first-of-type
[data-testid="stColumn"]:first-child > div,
[data-testid="stHorizontalBlock"]:first-of-type
[data-testid="stColumn"]:first-child > div > div {{
    display: flex !important;
    align-items: center !important;
    padding: 0 !important;
    margin: 0 !important;
}}
[data-testid="stHorizontalBlock"]:first-of-type
[data-testid="stColumn"]:first-child p,
[data-testid="stHorizontalBlock"]:first-of-type
[data-testid="stColumn"]:first-child img {{
    margin: 0 !important;
    padding: 0 !important;
    display: block !important;
    line-height: 0 !important;
}}

/* ── CHART TITLE ── */
.chart-title {{
    font-size: 0.875rem;
    font-weight: 700;
    color: #1C252E;
    margin: 0 0 6px;
    line-height: 1.4;
}}

/* ── TYPOGRAPHY ── */
.page-title {{
    font-size: 1.9rem;
    font-weight: 800;
    color: #1C252E;
    letter-spacing: -0.03em;
    margin: 0 0 6px;
    line-height: 1.15;
}}
.page-sub {{
    font-size: 0.875rem;
    font-weight: 400;
    color: #637381;
    margin: 0 0 1.6rem;
    line-height: 1.57;
}}
.section-label {{
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #919EAB;
    margin-bottom: 12px;
}}
.obs-note {{
    font-size: 0.775rem;
    color: #919EAB;
    line-height: 1.55;
    padding: 10px 0 2px;
    border-top: 1px solid #DFE3E8;
    margin-top: 4px;
}}

/* ── STAT CARDS ── */
.stat-card {{
    background: #ffffff;
    border-radius: 8px;
    padding: 20px 22px 16px;
    box-shadow: 0 0 2px 0 rgba(145,158,171,0.20), 0 12px 24px -4px rgba(145,158,171,0.12);
    border-top: 3px solid #FF3030;
}}
.stat-val {{
    font-size: 1.5rem;
    font-weight: 800;
    color: #1C252E;
    line-height: 1;
}}
.stat-label {{
    font-size: 0.68rem;
    font-weight: 700;
    color: #919EAB;
    margin-top: 6px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}}

/* ── TAG PILLS ── */
.tag {{
    display: inline-block;
    background: #1C252E;
    color: #919EAB;
    font-size: 0.68rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    margin-right: 4px;
}}

/* ── FINDING CARDS ── */
.finding-card {{
    background: #ffffff;
    border-left: 3px solid #FF3030;
    border-radius: 0 8px 8px 0;
    padding: 13px 16px;
    margin-bottom: 8px;
    font-size: 0.875rem;
    color: #1C252E;
    line-height: 1.57;
    box-shadow: 0 1px 2px 0 rgba(145,158,171,0.16);
}}
.finding-card.muted {{ border-color: #DFE3E8; color: #637381; }}
.finding-card .pop {{ font-weight: 700; color: #1C252E; }}
.finding-card .pval {{ color: #FF3030; font-weight: 700; }}

/* ── DIVIDER ── */
.divider {{
    border: none;
    border-top: 1px solid #DFE3E8;
    margin: 2rem 0 1.8rem;
}}

/* ── BIG METRIC ── */
.big-metric {{
    background: #1C252E;
    border-radius: 8px;
    padding: 24px 30px;
    display: inline-block;
    box-shadow: 0 8px 16px 0 rgba(255,48,48,0.24);
}}
.big-metric .val {{
    font-size: 2.2rem;
    font-weight: 800;
    color: #FF3030;
    letter-spacing: -0.03em;
    line-height: 1;
}}
.big-metric .lbl {{
    font-size: 0.68rem;
    font-weight: 700;
    color: #637381;
    margin-top: 8px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_connection():
    return sqlite3.connect("teiko.db", check_same_thread=False)

@st.cache_data
def load_freq():
    return get_frequency_table(get_connection())

@st.cache_data
def load_stats(_con):
    return run_stats(load_freq(), _con)

@st.cache_data
def load_subset(_con):
    return run_subset(_con)


con = get_connection()
freq_df = load_freq()

# ── NAV ──
nav_cols = st.columns([1.6] + [1] * len(pages) + [2.5])
with nav_cols[0]:
    st.markdown(
        f'<img src="data:image/svg+xml;base64,{_logo_b64}" '
        f'style="height:32px;display:block;margin:0;"/>',
        unsafe_allow_html=True
    )
for i, p in enumerate(pages):
    with nav_cols[i + 1]:
        if st.button(p, key=f"nav_{p}", use_container_width=True):
            st.session_state.page = p
            st.rerun()

st.markdown('<div style="height:1.4rem;"></div>', unsafe_allow_html=True)
page = st.session_state.page


# ── CHART PALETTE — Teiko tokens ──
# treatment groups = shades of primary red; control/healthy = grey-400/500
COND_COLORS = {
    "melanoma":  "rgba(255,48,48,0.85)",
    "carcinoma": "rgba(183,24,51,0.85)",
    "healthy":   "rgba(196,205,213,0.85)",
}
RESP_COLORS = {
    "yes": "rgba(56,109,217,0.85)",
    "no":  "rgba(196,205,213,0.85)",
}

_FONT = "Public Sans, sans-serif"
_TEXT = "#1C252E"
_GRID = "#F4F6F8"
_LINE = "#DFE3E8"

def blayout(height=290, show_legend=True):
    return dict(
        plot_bgcolor="#F4F6F8", paper_bgcolor="#F4F6F8",
        font_family=_FONT, font_color=_TEXT,
        height=height,
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis=dict(showgrid=False, linecolor=_LINE,
                   tickfont=dict(size=11, color="#637381"),
                   title_font=dict(size=11, color="#637381")),
        yaxis=dict(gridcolor="#DFE3E8", linecolor=_LINE,
                   tickfont=dict(size=11, color="#637381"),
                   title_font=dict(size=11, color="#637381")),
        showlegend=show_legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.05,
                    xanchor="left", x=0, font=dict(size=11, color="#637381"),
                    bgcolor="rgba(0,0,0,0)", borderwidth=0),
    )

def playout(height=250):
    return dict(
        height=height, font_family=_FONT, font_color=_TEXT,
        paper_bgcolor="#F4F6F8",
        margin=dict(l=0, r=0, t=10, b=65),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.28,
                    xanchor="center", x=0.5,
                    font=dict(size=11, color="#637381"),
                    bgcolor="rgba(0,0,0,0)", borderwidth=0),
    )


# ── HOME ─────────────────────────────────────────────────────────────────────

if page == "Home":
    st.markdown('<p class="page-title">Clinical Trial Overview</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="page-sub">Immune cell population profiling across three clinical projects. '
        'Five populations measured from peripheral blood at three timepoints per subject.</p>',
        unsafe_allow_html=True
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    for col, (val, lbl) in zip([c1,c2,c3,c4,c5], [
        ("3","Projects"), ("3,500","Subjects"), ("10,500","Samples"),
        ("5","Cell populations"), ("3","Timepoints")
    ]):
        with col:
            st.markdown(
                f'<div class="stat-card"><div class="stat-val">{val}</div>'
                f'<div class="stat-label">{lbl}</div></div>',
                unsafe_allow_html=True
            )

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    subj = pd.read_sql_query(
        "SELECT project_id, condition, sex, treatment, response, age FROM subjects", con
    )

    st.markdown('<p class="section-label">Study composition</p>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<p class="chart-title">Subjects by condition per project</p>', unsafe_allow_html=True)
        fig1 = px.bar(
            subj.groupby(["project_id", "condition"]).size().reset_index(name="n"),
            x="project_id", y="n", color="condition", barmode="group",
            color_discrete_map=COND_COLORS,
            labels={"project_id": "", "n": "subjects", "condition": ""},
        )
        fig1.update_layout(**blayout(280))
        st.plotly_chart(fig1, use_container_width=True, theme=None)

    with col_b:
        st.markdown('<p class="chart-title">Treatment arms — responder breakdown</p>', unsafe_allow_html=True)
        tc = subj[subj["treatment"] != "none"].groupby(["treatment","response"]).size().reset_index(name="n")
        fig2 = px.bar(
            tc, x="treatment", y="n", color="response", barmode="stack",
            color_discrete_map=RESP_COLORS,
            labels={"treatment": "", "n": "subjects", "response": ""},
        )
        fig2.update_layout(**blayout(280))
        st.plotly_chart(fig2, use_container_width=True, theme=None)

    st.markdown(
        '<p class="obs-note">Melanoma dominates across all three projects. '
        'Both active treatments show a majority of responders; response rates appear '
        'comparable between arms at face value.</p>',
        unsafe_allow_html=True
    )

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    st.markdown('<p class="section-label">Demographics &amp; sample quality</p>', unsafe_allow_html=True)
    col_c, col_d = st.columns(2)

    with col_c:
        st.markdown('<p class="chart-title">Age distribution by condition</p>', unsafe_allow_html=True)
        fig3 = px.box(
            subj, x="condition", y="age", color="condition",
            color_discrete_map=COND_COLORS,
            labels={"condition": "", "age": "age (years)"},
        )
        fig3.update_layout(**blayout(260, show_legend=False))
        st.plotly_chart(fig3, use_container_width=True, theme=None)

    with col_d:
        st.markdown('<p class="chart-title">Sample type breakdown</p>', unsafe_allow_html=True)
        samp = pd.read_sql_query(
            "SELECT sample_type, COUNT(*) as n FROM samples GROUP BY sample_type", con
        )
        fig4 = px.pie(
            samp, names="sample_type", values="n",
            color_discrete_sequence=["rgba(56,109,217,0.85)", "rgba(196,205,213,0.85)"],
            hole=0.5,
        )
        fig4.update_layout(**playout(260))
        st.plotly_chart(fig4, use_container_width=True, theme=None)

    st.markdown(
        '<p class="obs-note">Age distributions overlap substantially across conditions — '
        'age is unlikely to be a major confound. PBMC is the dominant sample matrix, '
        'consistent with standard immune profiling practice.</p>',
        unsafe_allow_html=True
    )

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    st.markdown('<p class="section-label">Key findings</p>', unsafe_allow_html=True)
    st.markdown(
        '<div class="finding-card">'
        '<span class="pop">CD4 T cells</span> — statistically significant difference in relative '
        'frequency between responders and non-responders in melanoma patients on miraclib (PBMC). '
        '<span class="pval">p = 0.0133</span>, Mann-Whitney U, two-sided.'
        '</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="finding-card muted">'
        '<span class="pop">B cells</span> — borderline trend toward lower frequency in responders; '
        'does not reach α = 0.05. '
        '<span style="color:#999;font-weight:600;">p = 0.056</span>. '
        'Warrants further investigation.'
        '</div>',
        unsafe_allow_html=True
    )


# ── FREQUENCY TABLE ───────────────────────────────────────────────────────────

elif page == "Frequency Table":
    st.markdown('<p class="page-title">Cell Population Frequencies</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="page-sub">Relative frequency of each immune cell population as a '
        'percentage of total cells per sample.</p>',
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        pop_filter = st.multiselect(
            "Population", sorted(freq_df["population"].unique()),
            default=sorted(freq_df["population"].unique())
        )
    with c2:
        sample_search = st.text_input("Search sample ID", "")
    with c3:
        st.markdown(
            f'<div style="padding-top:30px;font-size:0.78rem;color:#888;">'
            f'{len(freq_df):,} rows</div>',
            unsafe_allow_html=True
        )

    filtered = freq_df[freq_df["population"].isin(pop_filter)]
    if sample_search:
        filtered = filtered[filtered["sample"].str.contains(sample_search, case=False)]

    st.dataframe(filtered, use_container_width=True, height=520, hide_index=True)
    st.caption(f"{len(filtered):,} rows shown")


# ── STATISTICAL ANALYSIS ──────────────────────────────────────────────────────

elif page == "Statistical Analysis":
    st.markdown('<p class="page-title">Responders vs Non-Responders</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="page-sub">'
        '<span class="tag">melanoma</span><span class="tag">miraclib</span>'
        '<span class="tag">PBMC</span>'
        '&nbsp; Cell population frequencies compared between response groups. '
        'Mann-Whitney U, two-sided, α = 0.05.</p>',
        unsafe_allow_html=True
    )

    stats_df = load_stats(con)

    plot_df = freq_df.merge(
        pd.read_sql_query("""
            SELECT s.sample_id AS sample, su.response
            FROM samples s JOIN subjects su ON s.subject_id = su.subject_id
            WHERE su.condition='melanoma' AND su.treatment='miraclib' AND s.sample_type='PBMC'
        """, con), on="sample"
    )

    st.markdown('<p class="chart-title">Cell population frequency by response group</p>', unsafe_allow_html=True)
    fig = px.box(
        plot_df, x="population", y="percentage", color="response",
        color_discrete_map=RESP_COLORS,
        labels={"population": "", "percentage": "% of total cells", "response": ""},
        category_orders={"population": ["b_cell","cd8_t_cell","cd4_t_cell","nk_cell","monocyte"]},
        points=False,
    )
    fig.update_layout(**blayout(400))
    st.plotly_chart(fig, use_container_width=True, theme=None)

    st.markdown(
        '<p class="obs-note">Distributions are approximately normal but slightly leptokurtic. '
        'Mann-Whitney U was chosen for robustness to non-normality and outliers. '
        'Welch\'s t-test gives consistent significance conclusions across all five populations.</p>',
        unsafe_allow_html=True
    )

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<p class="section-label">Mann-Whitney U results</p>', unsafe_allow_html=True)

    left, right = st.columns([3, 1])
    with left:
        st.dataframe(stats_df, use_container_width=True, hide_index=True)
    with right:
        for _, row in stats_df.iterrows():
            if row["significant"]:
                st.markdown(
                    f'<div class="finding-card">'
                    f'<span class="pop">{row["population"].replace("_"," ")}</span><br>'
                    f'<span class="pval">p = {row["p_value"]}</span>&nbsp;· significant'
                    f'</div>',
                    unsafe_allow_html=True
                )


# ── SUBSET ANALYSIS ───────────────────────────────────────────────────────────

elif page == "Subset Analysis":
    st.markdown('<p class="page-title">Baseline Subset Analysis</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="page-sub">'
        '<span class="tag">melanoma</span><span class="tag">PBMC</span>'
        '<span class="tag">time = 0</span><span class="tag">miraclib</span>'
        '&nbsp; Samples and subjects at pre-treatment baseline.</p>',
        unsafe_allow_html=True
    )

    subset = load_subset(con)

    st.markdown('<p class="section-label">Cohort breakdown at baseline</p>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown('<p class="chart-title">Samples per project</p>', unsafe_allow_html=True)
        fp = px.bar(
            subset["proj_counts"], x="project", y="n_samples",
            color="project",
            color_discrete_sequence=["rgba(56,109,217,0.85)", "rgba(34,160,185,0.85)", "rgba(99,115,129,0.85)"],
            labels={"project": "", "n_samples": "samples"},
        )
        fp.update_layout(**blayout(240, show_legend=False))
        st.plotly_chart(fp, use_container_width=True, theme=None)

    with c2:
        st.markdown('<p class="chart-title">Subjects by response</p>', unsafe_allow_html=True)
        fr = px.pie(
            subset["resp_counts"], names="response", values="n_subjects",
            hole=0.52, color_discrete_map=RESP_COLORS,
        )
        fr.update_layout(**playout(240))
        st.plotly_chart(fr, use_container_width=True, theme=None)

    with c3:
        st.markdown('<p class="chart-title">Subjects by sex</p>', unsafe_allow_html=True)
        fs = px.pie(
            subset["sex_counts"], names="sex", values="n_subjects",
            hole=0.52, color_discrete_map={"M": "rgba(99,115,129,0.85)", "F": "rgba(56,109,217,0.85)"},
        )
        fs.update_layout(**playout(240))
        st.plotly_chart(fs, use_container_width=True, theme=None)

    st.markdown(
        '<p class="obs-note">Cohort is relatively balanced by response and sex at baseline. '
        'Sample counts vary across projects. These counts reflect time = 0 only, '
        'not the full longitudinal dataset used in Part 3.</p>',
        unsafe_allow_html=True
    )

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown(
        '<p class="section-label">Avg B cell count — melanoma · male · responders · time = 0</p>',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<div class="big-metric">'
        f'<div class="val">{subset["avg_b_cell"]:,.2f}</div>'
        f'<div class="lbl">mean B cell count per sample</div>'
        f'</div>',
        unsafe_allow_html=True
    )
