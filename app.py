import base64
import sqlite3
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
from analysis import get_frequency_table, run_stats, run_subset, compare_tests

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

:root {{
    --tb-bg: #F6F7F9;
    --tb-surface: #FFFFFF;
    --tb-surface-muted: #EEF2F5;
    --tb-nav: #151C24;
    --tb-text: #18212B;
    --tb-text-secondary: #566370;
    --tb-text-muted: #7B8794;
    --tb-border: #DDE3E8;
    --tb-grid: #E9EDF1;
    --tb-brand: #E12D39;
    --tb-brand-dark: #B81E2D;
    --tb-brand-soft: #FFF1F2;
    --tb-blue: #356BD6;
    --tb-radius: 12px;
}}

html, body, .stApp, [data-testid="stAppViewContainer"] {{
    font-family: 'Public Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--tb-bg) !important;
    color: var(--tb-text) !important;
    color-scheme: light;
}}

button, input, textarea, select {{
    font-family: inherit !important;
}}

#MainMenu,
footer,
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stStatusWidget"],
[data-testid="collapsedControl"] {{
    display: none !important;
}}

.block-container {{
    padding-top: 72px !important;
    padding-bottom: 3rem !important;
    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
    max-width: 1400px !important;
    margin: 0 auto !important;
}}

/* Scope the navbar to a keyed container. A global :first-of-type selector can
   accidentally style other st.columns rows and create dark chart backgrounds. */
.st-key-top_nav {{
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    z-index: 9999 !important;
    background: var(--tb-nav) !important;
    padding: 0 max(2.5rem, calc((100vw - 1400px) / 2 + 2.5rem)) !important;
    border-bottom: 1px solid #27313B !important;
    box-sizing: border-box !important;
    transform: translateY(0);
    transition: transform 0.22s ease !important;
}}

.st-key-top_nav.nav--hidden {{
    transform: translateY(-100%) !important;
}}

.st-key-top_nav [data-testid="stHorizontalBlock"] {{
    display: flex !important;
    align-items: center !important;
    gap: 0 !important;
    column-gap: 0 !important;
    min-height: 64px !important;
    background: transparent !important;
}}

/* Strip all padding/margin from every column so Streamlit's internal widths
   don't create uneven gutters. Flex rules below control sizing instead. */
.st-key-top_nav [data-testid="stColumn"],
.st-key-top_nav [data-testid="stColumn"] > div,
.st-key-top_nav [data-testid="stColumn"] > div > div {{
    padding: 0 !important;
    margin: 0 !important;
    box-sizing: border-box !important;
}}

/* Logo column: fixed width (just enough for the SVG, no extra gap before Home) */
.st-key-top_nav [data-testid="stColumn"]:first-child {{
    flex: 0 0 160px !important;
    width: 160px !important;
}}

/* Nav tab columns: auto basis so each tab starts at its natural content width,
   then grows equally → every tab gets the same extra padding on each side */
.st-key-top_nav [data-testid="stColumn"]:not(:first-child):not(:last-child) {{
    flex: 1 1 auto !important;
    width: auto !important;
    min-width: min-content !important;
    max-width: none !important;
}}

/* Trailing spacer: small fixed spacer so nav isn't flush-right */
.st-key-top_nav [data-testid="stColumn"]:last-child {{
    flex: 0 0 80px !important;
    width: 80px !important;
    min-width: 0 !important;
}}

/* stButton wrapper: fill the column completely */
.st-key-top_nav [data-testid="stButton"] {{
    width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
}}

/* stVerticalBlock: strip gap so no space is inserted between the stHorizontalBlock and its wrapper */
.st-key-top_nav [data-testid="stVerticalBlock"] {{
    gap: 0 !important;
}}

.st-key-top_nav [data-testid="stButton"] > button {{
    width: 100% !important;
    min-height: 64px !important;
    padding: 20px 12px 18px !important;
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    color: #8E9AA6 !important;
    font-size: 1.15rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.005em !important;
    white-space: nowrap !important;
    text-align: center !important;
    justify-content: center !important;
    transition: color 120ms ease, border-color 120ms ease, background 120ms ease !important;
}}

.st-key-top_nav [data-testid="stButton"] > button p {{
    margin: 0 !important;
    color: inherit !important;
    font-size: 1.15rem !important;
    font-weight: 600 !important;
}}

.st-key-top_nav [data-testid="stButton"] > button:hover {{
    color: #FFFFFF !important;
    background: rgba(255, 255, 255, 0.04) !important;
    border-bottom-color: #56616D !important;
}}

.st-key-top_nav [data-testid="stButton"] > button:focus,
.st-key-top_nav [data-testid="stButton"] > button:active {{
    outline: none !important;
    box-shadow: none !important;
}}

.st-key-top_nav [data-testid="stColumn"]:nth-child({_active_col})
[data-testid="stButton"] > button {{
    color: #FFFFFF !important;
    background: transparent !important;
    border-bottom-color: #FF4B55 !important;
}}

.st-key-top_nav [data-testid="stColumn"]:first-child,
.st-key-top_nav [data-testid="stColumn"]:first-child > div,
.st-key-top_nav [data-testid="stColumn"]:first-child > div > div {{
    display: flex !important;
    align-items: center !important;
    padding: 0 !important;
    margin: 0 !important;
}}

.st-key-top_nav [data-testid="stColumn"]:first-child p,
.st-key-top_nav [data-testid="stColumn"]:first-child img {{
    display: block !important;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 0 !important;
}}

/* Type hierarchy:
   page-title  → all-caps Barlow 800, dark-gray (#454F5B), 3rem — dominant page label
   section-title → all-caps Barlow 700, mid-gray (#637381), 1.25rem — section marker
   page-sub    → Public Sans 400, mid-gray (#637381), 1rem — ambient descriptor
   chart-title → Public Sans 600, muted-gray (#919EAB), 0.875rem — soft graph label */
   
.page-title {{
    margin: 0 0 0.55rem;
    color: #454F5B;
    font-family: 'Barlow', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 3rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    line-height: 1.2;
    text-transform: uppercase;
}}

.page-sub {{
    margin: 0 0 1.8rem;
    color: #637381;
    font-family: 'Public Sans', -apple-system, sans-serif;
    font-size: 1rem;
    font-weight: 400;
    line-height: 1.5;
}}

.section-title {{
    margin: 0 0 0.9rem;
    color: #637381;
    font-family: 'Barlow', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 1.25rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    line-height: 1.5;
    text-transform: uppercase;
}}

.chart-title {{
    margin: 0 0 0.45rem;
    color: #919EAB;
    font-family: 'Public Sans', -apple-system, sans-serif;
    font-size: 0.875rem;
    font-weight: 600;
    letter-spacing: 0.01em;
    line-height: 1.5714;
}}

.obs-note {{
    margin: 0.55rem 0 0;
    padding: 0.3rem 0 0.1rem;
    color: var(--tb-text-secondary);
    font-size: 0.8125rem;
    line-height: 1.6;
}}

.row-count {{
    padding-top: 31px;
    color: var(--tb-text-muted);
    font-size: 0.8rem;
    font-weight: 500;
}}

/* Summary cards */
.stat-card {{
    position: relative;
    min-height: 112px;
    padding: 18px 20px 16px;
    overflow: hidden;
    background: var(--tb-surface);
    border: 1px solid var(--tb-border);
    border-radius: var(--tb-radius);
    box-shadow: 0 1px 2px rgba(24, 33, 43, 0.05), 0 8px 22px rgba(24, 33, 43, 0.04);
}}

.stat-card::before {{
    display: block;
    width: 28px;
    height: 3px;
    margin-bottom: 16px;
    background: var(--tb-brand);
    border-radius: 999px;
    content: '';
}}

.stat-val {{
    color: var(--tb-text);
    font-family: 'Barlow', 'Public Sans', sans-serif;
    font-size: 1.75rem;
    font-weight: 800;
    letter-spacing: -0.025em;
    line-height: 1;
}}

.stat-label {{
    margin-top: 7px;
    color: var(--tb-text-secondary);
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.075em;
    line-height: 1.35;
    text-transform: uppercase;
}}

/* Metadata chips */
.tag {{
    display: inline-block;
    margin: 0 5px 4px 0;
    padding: 3px 9px;
    background: var(--tb-surface-muted);
    border: 1px solid var(--tb-border);
    border-radius: 999px;
    color: #45515E;
    font-size: 0.72rem;
    font-weight: 600;
    line-height: 1.35;
}}

/* Findings */
.finding-card {{
    margin-bottom: 9px;
    padding: 14px 16px;
    background: var(--tb-surface);
    border: 1px solid var(--tb-border);
    border-left: 3px solid var(--tb-brand);
    border-radius: 0 10px 10px 0;
    box-shadow: 0 1px 2px rgba(24, 33, 43, 0.04);
    color: var(--tb-text-secondary);
    font-size: 0.875rem;
    line-height: 1.6;
}}

.finding-card.muted {{
    border-left-color: #AAB4BE;
}}

.finding-card .pop {{
    color: var(--tb-text);
    font-weight: 700;
}}

.finding-card .pval {{
    color: var(--tb-brand-dark);
    font-weight: 700;
}}

.divider {{
    margin: 2.25rem 0 1.8rem;
    border: 0;
    border-top: 1px solid var(--tb-border);
}}

.big-metric {{
    display: inline-block;
    min-width: 260px;
    padding: 22px 26px;
    background: var(--tb-surface);
    border: 1px solid var(--tb-border);
    border-left: 4px solid var(--tb-brand);
    border-radius: var(--tb-radius);
    box-shadow: 0 1px 2px rgba(24, 33, 43, 0.05), 0 8px 22px rgba(24, 33, 43, 0.04);
}}

.big-metric .val {{
    color: var(--tb-brand-dark);
    font-family: 'Barlow', 'Public Sans', sans-serif;
    font-size: 2.5rem;
    font-weight: 800;
    letter-spacing: -0.035em;
    line-height: 1;
}}

.big-metric .lbl {{
    margin-top: 8px;
    color: var(--tb-text-secondary);
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.075em;
    line-height: 1.4;
    text-transform: uppercase;
}}

/* Plotly: style only Streamlit's outer chart surface. Do not override Plotly's
   internal .plotly/.plot-container nodes; the figure layout owns those colors. */
[data-testid="stPlotlyChart"] {{
    overflow: visible;
    padding: 0.35rem 0.5rem 0.15rem;
    background: var(--tb-surface) !important;
    border: 1px solid var(--tb-border);
    border-radius: var(--tb-radius);
    box-shadow: 0 1px 2px rgba(24, 33, 43, 0.04);
}}

[data-testid="stPlotlyChart"] > div {{
    background: transparent !important;
}}

/* Tables and controls */
[data-testid="stDataFrame"] {{
    overflow: hidden;
    background: var(--tb-surface);
    border: 1px solid var(--tb-border);
    border-radius: var(--tb-radius);
}}

[data-testid="stWidgetLabel"] p {{
    color: var(--tb-text-secondary) !important;
    font-size: 0.8125rem !important;
    font-weight: 600 !important;
}}

[data-baseweb="select"] > div,
[data-baseweb="input"] > div,
[data-testid="stTextInput"] input {{
    background: var(--tb-surface) !important;
    border-color: var(--tb-border) !important;
    color: var(--tb-text) !important;
}}

[data-testid="stCaptionContainer"] p {{
    color: var(--tb-text-muted) !important;
    font-size: 0.78rem !important;
}}

@media (max-width: 900px) {{
    .block-container {{
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }}

    .st-key-top_nav {{
        padding: 0 1rem !important;
    }}

    .st-key-top_nav [data-testid="stVerticalBlock"] {{
        overflow-x: auto;
    }}

    .st-key-top_nav [data-testid="stHorizontalBlock"] {{
        min-width: 760px;
    }}

    .page-title {{
        font-size: 2.25rem;
        letter-spacing: 0.04em;
    }}
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

@st.cache_data
def load_group_sizes(_con):
    return pd.read_sql_query("""
        SELECT su.response,
               COUNT(DISTINCT su.subject_id) AS n_subjects,
               COUNT(s.sample_id)            AS n_samples
        FROM samples s JOIN subjects su ON s.subject_id = su.subject_id
        WHERE su.condition='melanoma' AND su.treatment='miraclib' AND s.sample_type='PBMC'
        GROUP BY su.response
    """, _con)

@st.cache_data
def load_time_trend(_con, _freq_df):
    meta = pd.read_sql_query("""
        SELECT s.sample_id AS sample, s.time_from_treatment_start AS timepoint,
               su.response
        FROM samples s JOIN subjects su ON s.subject_id = su.subject_id
        WHERE su.condition='melanoma' AND su.treatment='miraclib' AND s.sample_type='PBMC'
    """, _con)
    trend = (
        _freq_df.merge(meta, on="sample")
        .groupby(["timepoint", "response", "population"])["percentage"]
        .mean()
        .reset_index(name="mean_pct")
    )
    trend["day"] = trend["timepoint"].astype(str)
    return trend

@st.cache_data
def load_compare(_con, _freq_df):
    return compare_tests(_freq_df, _con)


con = get_connection()
freq_df = load_freq()

# ── NAV ──
# The key gives the navbar a stable CSS scope (`.st-key-top_nav`).
with st.container(key="top_nav"):
    nav_cols = st.columns([1.0] + [1] * len(pages) + [2.0])
    with nav_cols[0]:
        st.markdown(
            f'<img src="data:image/svg+xml;base64,{_logo_b64}" '
            f'style="height:32px;display:block;margin:0;"/>',
            unsafe_allow_html=True,
        )
    for i, p in enumerate(pages):
        with nav_cols[i + 1]:
            nav_key = f"nav_{p.lower().replace(' ', '_')}"
            if st.button(p, key=nav_key, use_container_width=True):
                st.session_state.page = p
                st.rerun()

st.markdown('<div style="height:1.15rem;"></div>', unsafe_allow_html=True)
page = st.session_state.page

# Inject scroll-hide logic via components.html (executes in an iframe that can
# reach the Streamlit scroll container — [data-testid="stMain"] — via window.parent).
components.html("""
<script>
(function () {
    var win = window.parent;
    if (win._teikoNavScroll) return;
    win._teikoNavScroll = true;
    var lastY = 0, ticking = false;
    function update(container) {
        var nav = win.document.querySelector('.st-key-top_nav');
        if (!nav) { ticking = false; return; }
        var y = (container === win) ? (win.scrollY || win.pageYOffset) : container.scrollTop;
        if (y > lastY && y > 80) nav.classList.add('nav--hidden');
        else nav.classList.remove('nav--hidden');
        lastY = y; ticking = false;
    }
    function attach() {
        var container = win.document.querySelector('[data-testid="stMain"]') || win;
        container.addEventListener('scroll', function () {
            if (!ticking) {
                var self = this;
                win.requestAnimationFrame(function () { update(self); });
                ticking = true;
            }
        }, { passive: true });
    }
    if (win.document.readyState === 'complete') { attach(); }
    else { win.addEventListener('load', attach); }
})();
</script>
""", height=0)


# ── CHART PALETTE — Teiko tokens ──
# Keep the semantic mapping stable across every page.
COND_COLORS = {
    "melanoma":  "rgba(225,45,57,0.82)",
    "carcinoma": "rgba(142,59,104,0.82)",
    "healthy":   "rgba(170,180,190,0.82)",
}
RESP_COLORS = {
    "yes": "rgba(225,45,57,0.82)",
    "no":  "rgba(170,180,190,0.82)",
}
SAMPLE_COLORS  = ["#356BD6", "#C4CDD5"]
PROJECT_COLORS = ["rgba(53,107,214,0.82)", "rgba(58,154,157,0.82)", "rgba(119,131,144,0.82)"]
# Solid hex for pie-only charts — rgba doesn't render reliably in px.pie color_discrete_map
SEX_COLORS  = {"M": "#356BD6", "F": "#8E3B68"}
RESP_PIE_COLORS = {"yes": "#E12D39", "no": "#C4CDD5"}

_FONT = "Public Sans, Arial, sans-serif"
_SURFACE = "#FFFFFF"
_TEXT = "#18212B"
_TEXT_SECONDARY = "#566370"
_GRID = "#E9EDF1"
_LINE = "#DDE3E8"

PLOTLY_CONFIG = {
    "displayModeBar": False,
    "displaylogo": False,
    "responsive": True,
    "scrollZoom": False,
}


def _hover_label():
    return dict(
        bgcolor=_SURFACE,
        bordercolor=_LINE,
        font=dict(family=_FONT, size=12, color=_TEXT),
    )


def blayout(height=290, show_legend=True):
    """Shared Cartesian chart layout with an explicit light surface."""
    return dict(
        template="plotly_white",
        plot_bgcolor=_SURFACE,
        paper_bgcolor=_SURFACE,
        font=dict(family=_FONT, size=12, color=_TEXT),
        height=height,
        margin=dict(l=52, r=18, t=50 if show_legend else 24, b=44),
        xaxis=dict(
            showgrid=False,
            showline=True,
            linecolor=_LINE,
            linewidth=1,
            zeroline=False,
            ticks="outside",
            ticklen=4,
            tickcolor=_LINE,
            tickfont=dict(size=11, color=_TEXT_SECONDARY),
            title_font=dict(size=11, color=_TEXT_SECONDARY),
            automargin=True,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=_GRID,
            gridwidth=1,
            showline=False,
            zeroline=False,
            tickfont=dict(size=11, color=_TEXT_SECONDARY),
            title_font=dict(size=11, color=_TEXT_SECONDARY),
            automargin=True,
        ),
        showlegend=show_legend,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.08,
            xanchor="left",
            x=0,
            font=dict(size=11, color=_TEXT_SECONDARY),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            itemclick=False,
            itemdoubleclick=False,
        ),
        hoverlabel=_hover_label(),
        bargap=0.24,
    )


def playout(height=250):
    """Shared donut/pie layout with the same light surface and typography."""
    return dict(
        template="plotly_white",
        height=height,
        font=dict(family=_FONT, size=12, color=_TEXT),
        paper_bgcolor=_SURFACE,
        plot_bgcolor=_SURFACE,
        margin=dict(l=8, r=8, t=12, b=58),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.10,
            xanchor="center",
            x=0.5,
            font=dict(size=11, color=_TEXT_SECONDARY),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            itemclick=False,
            itemdoubleclick=False,
        ),
        hoverlabel=_hover_label(),
        uniformtext_minsize=11,
        uniformtext_mode="hide",
    )


def fix_box_opacity(fig, color_map):
    """Plotly auto-reduces box fill to ~50% of line color. Override to keep rgba opacity intact."""
    for trace in fig.data:
        c = color_map.get(trace.name)
        if c:
            trace.update(fillcolor=c, line=dict(color=c))


def fix_pie_colors(fig, color_map):
    """update_layout(template=...) can reset pie trace colors set by color_discrete_map.
    Re-apply colors directly on marker after layout is applied."""
    for trace in fig.data:
        if hasattr(trace, "labels") and trace.labels is not None:
            trace.marker.colors = [color_map.get(lbl, "#AAAAAA") for lbl in trace.labels]


def render_plotly(fig):
    """Render Plotly consistently and suppress the dark floating modebar."""
    st.plotly_chart(
        fig,
        use_container_width=True,
        theme=None,
        config=PLOTLY_CONFIG,
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

    st.markdown('<p class="section-title">Study composition</p>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<p class="chart-title">Subjects by condition per project</p>', unsafe_allow_html=True)
        fig1 = px.bar(
            subj.groupby(["project_id", "condition"]).size().reset_index(name="n"),
            x="project_id", y="n", color="condition", barmode="group",
            color_discrete_map=COND_COLORS,
            category_orders={"condition": ["carcinoma", "melanoma", "healthy"]},
            labels={"project_id": "", "n": "subjects", "condition": ""},
        )
        fig1.update_layout(**blayout(280))
        render_plotly(fig1)

    with col_b:
        st.markdown('<p class="chart-title">Treatment arms — responder breakdown</p>', unsafe_allow_html=True)
        tc = subj[subj["treatment"] != "none"].groupby(["treatment","response"]).size().reset_index(name="n")
        fig2 = px.bar(
            tc, x="treatment", y="n", color="response", barmode="stack",
            color_discrete_map=RESP_COLORS,
            labels={"treatment": "", "n": "subjects", "response": ""},
        )
        fig2.update_layout(**blayout(280))
        render_plotly(fig2)

    st.markdown(
        '<p class="obs-note">Melanoma dominates across all three projects. '
        'Both active treatments show a majority of responders; response rates appear '
        'comparable between arms at face value.</p>',
        unsafe_allow_html=True
    )

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    st.markdown('<p class="section-title">Demographics &amp; sample quality</p>', unsafe_allow_html=True)
    col_c, col_d = st.columns(2)

    with col_c:
        st.markdown('<p class="chart-title">Age distribution by condition</p>', unsafe_allow_html=True)
        fig3 = px.box(
            subj, x="condition", y="age", color="condition",
            color_discrete_map=COND_COLORS,
            category_orders={"condition": ["carcinoma", "melanoma", "healthy"]},
            labels={"condition": "", "age": "age (years)"},
        )
        fig3.update_layout(**blayout(260, show_legend=False))
        fix_box_opacity(fig3, COND_COLORS)
        render_plotly(fig3)

    with col_d:
        st.markdown('<p class="chart-title">Sample type breakdown</p>', unsafe_allow_html=True)
        samp = pd.read_sql_query(
            "SELECT sample_type, COUNT(*) as n FROM samples GROUP BY sample_type", con
        )
        fig4 = px.pie(
            samp, names="sample_type", values="n",
            color_discrete_sequence=SAMPLE_COLORS,
            hole=0.5,
        )
        fig4.update_layout(**playout(260))
        # Build a label→color map from the sequence and data order
        _samp_color_map = dict(zip(samp["sample_type"].tolist(), SAMPLE_COLORS))
        fix_pie_colors(fig4, _samp_color_map)
        render_plotly(fig4)

    st.markdown(
        '<p class="obs-note">Age distributions overlap substantially across conditions — '
        'age is unlikely to be a major confound. PBMC is the dominant sample matrix, '
        'consistent with standard immune profiling practice.</p>',
        unsafe_allow_html=True
    )

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    st.markdown('<p class="section-title">Key findings</p>', unsafe_allow_html=True)
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
        '<span style="color:#566370;font-weight:600;">p = 0.056</span>. '
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
            f'<div class="row-count">{len(freq_df):,} rows</div>',
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
        '<span class="tag">PBMC</span><span class="tag">days 0 · 7 · 14</span>'
        '&nbsp; Immune cell population frequencies compared between response groups '
        'using Mann-Whitney U (two-sided, α = 0.05).</p>',
        unsafe_allow_html=True
    )

    stats_df  = load_stats(con)
    cmp_df    = load_compare(con, freq_df)
    trend_df  = load_time_trend(con, freq_df)
    grp       = load_group_sizes(con)
    g_yes     = grp[grp["response"] == "yes"].iloc[0]
    g_no      = grp[grp["response"] == "no"].iloc[0]

    # ── cohort overview cards ─────────────────────────────────────────────────
    gc1, gc2, gc3, gc4, gc5 = st.columns(5)
    for col, (val, lbl) in zip([gc1, gc2, gc3, gc4, gc5], [
        (f'{int(g_yes["n_subjects"])}', "Responders"),
        (f'{int(g_no["n_subjects"])}',  "Non-responders"),
        (f'{int(g_yes["n_samples"])}',  "Responder samples"),
        (f'{int(g_no["n_samples"])}',   "Non-resp. samples"),
        ("3",                            "Timepoints (d 0·7·14)"),
    ]):
        with col:
            st.markdown(
                f'<div class="stat-card"><div class="stat-val">{val}</div>'
                f'<div class="stat-label">{lbl}</div></div>',
                unsafe_allow_html=True
            )

    # ── distribution overview ─────────────────────────────────────────────────
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<p class="section-title">Distribution overview</p>', unsafe_allow_html=True)

    plot_df = freq_df.merge(
        pd.read_sql_query("""
            SELECT s.sample_id AS sample, su.response
            FROM samples s JOIN subjects su ON s.subject_id = su.subject_id
            WHERE su.condition='melanoma' AND su.treatment='miraclib' AND s.sample_type='PBMC'
        """, con), on="sample"
    )
    st.markdown('<p class="chart-title">Cell population frequency by response group — all timepoints</p>', unsafe_allow_html=True)
    fig = px.box(
        plot_df, x="population", y="percentage", color="response",
        color_discrete_map=RESP_COLORS,
        labels={"population": "", "percentage": "% of total cells", "response": ""},
        category_orders={"population": ["b_cell","cd8_t_cell","cd4_t_cell","nk_cell","monocyte"]},
        points=False,
    )
    fig.update_layout(**blayout(380))
    fix_box_opacity(fig, RESP_COLORS)
    render_plotly(fig)
    st.markdown(
        '<p class="obs-note">Distributions are approximately normal but slightly leptokurtic across all populations. '
        'Groups are well-balanced — '
        f'{int(g_yes["n_subjects"])} responders ({int(g_yes["n_samples"])} samples) vs '
        f'{int(g_no["n_subjects"])} non-responders ({int(g_no["n_samples"])} samples) — '
        'so statistical power is not a concern. CD4 T cells show the clearest separation between groups; '
        'B cells trend lower in responders but fall just short of significance (p = 0.056).</p>',
        unsafe_allow_html=True
    )

    # ── cell counts over time ─────────────────────────────────────────────────
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<p class="section-title">Cell counts over time</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="chart-title">Mean % per population · days 0, 7, 14 · responders vs non-responders</p>',
        unsafe_allow_html=True
    )
    pop_order = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]
    fig_trend = px.line(
        trend_df,
        x="day", y="mean_pct",
        color="response",
        facet_col="population",
        color_discrete_map=RESP_COLORS,
        markers=True,
        category_orders={
            "response":   ["yes", "no"],
            "day":        ["0", "7", "14"],
            "population": pop_order,
        },
        labels={"day": "day", "mean_pct": "mean %", "response": "", "population": ""},
    )
    fig_trend.update_layout(**blayout(300))
    fig_trend.for_each_annotation(lambda a: a.update(
        text=a.text.split("=")[-1].replace("_", " ")
    ))
    fig_trend.update_yaxes(matches=None, showticklabels=True)
    render_plotly(fig_trend)
    st.markdown(
        '<p class="obs-note">Most populations are stable across the three weekly draw timepoints. '
        'CD4 T cell frequency remains consistently higher in responders from day 0 onward, '
        'indicating this is a pre-existing characteristic rather than a treatment-induced change '
        'within the 14-day observation window. No population shows a clear directional trajectory '
        'that would suggest the 14-day window is insufficient to capture the relevant biology.</p>',
        unsafe_allow_html=True
    )

    # ── statistical results ────────────────────────────────────────────────────
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<p class="section-title">Mann-Whitney U results</p>', unsafe_allow_html=True)

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

    # ── test selection rationale ──────────────────────────────────────────────
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<p class="section-title">Test selection rationale</p>', unsafe_allow_html=True)

    st.markdown(
        '<p class="chart-title">Frequency distributions by response — overlaid histograms, all timepoints</p>',
        unsafe_allow_html=True
    )
    fig_hist = px.histogram(
        plot_df,
        x="percentage", color="response",
        facet_col="population", nbins=25,
        barmode="overlay", opacity=0.6,
        color_discrete_map=RESP_COLORS,
        histnorm="probability density",
        category_orders={
            "response":   ["yes", "no"],
            "population": ["b_cell","cd8_t_cell","cd4_t_cell","nk_cell","monocyte"],
        },
        labels={"percentage": "% of total", "response": "", "population": ""},
    )
    fig_hist.update_layout(**blayout(290))
    fig_hist.for_each_annotation(lambda a: a.update(
        text=a.text.split("=")[-1].replace("_", " ")
    ))
    fig_hist.update_yaxes(matches=None, showticklabels=True)
    fig_hist.update_xaxes(showticklabels=True)
    render_plotly(fig_hist)

    st.markdown(
        '<p class="obs-note" style="margin-bottom:1.1rem;">'
        '<strong>Normality</strong> — Histograms show approximately bell-shaped distributions for '
        'most populations, but with moderately heavier tails than a normal distribution '
        '(leptokurtosis), and slight right-skew in B cells and NK cells. '
        'CD4 T cells show the clearest separation between groups, with the responder distribution '
        'shifted notably higher. '
        'These deviations from normality favour a rank-based test over a parametric one.<br><br>'
        '<strong>Independence</strong> — Each data point is one sample from one subject at one '
        'timepoint. Three timepoints per subject introduce within-subject correlation, but the '
        'time-series analysis shows stable trajectories with no systematic trend, so treating '
        'measurements as independent observations is a reasonable approximation for this dataset size.<br><br>'
        '<strong>Equal variance</strong> — No equality-of-variance assumption is made: '
        'Mann-Whitney tests for stochastic dominance rather than mean differences, and the '
        'Welch\'s t-test comparison (which explicitly corrects for unequal variances) reaches '
        'identical significance conclusions across all five populations — confirming the inference '
        'is not driven by heteroscedasticity. Mann-Whitney p-values are slightly smaller for '
        'B cells (0.056 vs 0.171 for Welch\'s), consistent with its better power when tail '
        'shapes differ between groups.</p>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<p class="chart-title">Mann-Whitney vs Welch\'s t-test — p-value comparison</p>',
        unsafe_allow_html=True
    )
    cmp_display = cmp_df[[
        "population", "responder_median", "non_responder_median",
        "p_mannwhitney", "p_welch", "consistent"
    ]].copy()
    cmp_display.columns = [
        "Population", "Responder median", "Non-resp. median",
        "p (Mann-Whitney)", "p (Welch's)", "Consistent"
    ]
    st.dataframe(cmp_display, use_container_width=True, hide_index=True)


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

    st.markdown('<p class="section-title">Cohort breakdown at baseline</p>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown('<p class="chart-title">Samples per project</p>', unsafe_allow_html=True)
        fp = px.bar(
            subset["proj_counts"], x="project", y="n_samples",
            color="project",
            color_discrete_sequence=PROJECT_COLORS,
            labels={"project": "", "n_samples": "samples"},
        )
        fp.update_layout(**blayout(240, show_legend=False))
        render_plotly(fp)

    with c2:
        st.markdown('<p class="chart-title">Subjects by response</p>', unsafe_allow_html=True)
        fr = px.pie(
            subset["resp_counts"], names="response", values="n_subjects",
            hole=0.52, color_discrete_map=RESP_PIE_COLORS,
        )
        fr.update_layout(**playout(240))
        fix_pie_colors(fr, RESP_PIE_COLORS)
        render_plotly(fr)

    with c3:
        st.markdown('<p class="chart-title">Subjects by sex</p>', unsafe_allow_html=True)
        fs = px.pie(
            subset["sex_counts"], names="sex", values="n_subjects",
            hole=0.52, color_discrete_map=SEX_COLORS,
        )
        fs.update_layout(**playout(240))
        fix_pie_colors(fs, SEX_COLORS)
        render_plotly(fs)

    st.markdown(
        '<p class="obs-note">Cohort is relatively balanced by response and sex at baseline. '
        'Sample counts vary across projects. These counts reflect time = 0 only, '
        'not the full longitudinal dataset used in Part 3.</p>',
        unsafe_allow_html=True
    )

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown(
        '<p class="section-title">Avg B cell count — melanoma · male · responders · time = 0</p>',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<div class="big-metric">'
        f'<div class="val">{subset["avg_b_cell"]:,.2f}</div>'
        f'<div class="lbl">mean B cell count per sample</div>'
        f'</div>',
        unsafe_allow_html=True
    )