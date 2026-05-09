"""
app.py — DVN Group 7 CPI Dashboard
Interactive Streamlit dashboard for Australia's Consumer Price Index.
Run: streamlit run src/app.py
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from data_loader import load_table9, load_table11, load_table17

# ──────────────────────────────────────────────────────────────────────
# Page Config & Theme
# ──────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="CPI Australia Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Color palette
CITY_COLORS = {
    "Sydney": "#636EFA", "Melbourne": "#EF553B", "Brisbane": "#00CC96",
    "Adelaide": "#AB63FA", "Perth": "#FFA15A", "Hobart": "#19D3F3",
    "Darwin": "#FF6692", "Canberra": "#B6E880",
    "Weighted average of eight capital cities": "#FECB52",
}

GROUP_COLORS = px.colors.qualitative.Set3

PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif"),
    margin=dict(l=40, r=20, t=50, b=40),
    legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
)

# ──────────────────────────────────────────────────────────────────────
# Custom CSS
# ──────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Global */
.stApp {
    background: linear-gradient(135deg, #0f0c29 0%, #1a1a2e 50%, #16213e 100%);
    font-family: 'Inter', sans-serif;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    border-right: 1px solid rgba(255,255,255,0.05);
}

/* Metric cards */
.metric-card {
    background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.03) 100%);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 20px 24px;
    text-align: center;
    backdrop-filter: blur(10px);
    transition: transform 0.2s, box-shadow 0.2s;
}
.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(99,110,250,0.2);
}
.metric-value {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(90deg, #636EFA, #00CC96);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 4px 0;
}
.metric-label {
    font-size: 0.85rem;
    color: rgba(255,255,255,0.5);
    text-transform: uppercase;
    letter-spacing: 1px;
}
.metric-delta {
    font-size: 0.95rem;
    font-weight: 600;
    margin-top: 4px;
}
.delta-up { color: #EF553B; }
.delta-down { color: #00CC96; }

/* Header */
.dashboard-header {
    text-align: center;
    padding: 30px 0 20px;
}
.dashboard-header h1 {
    font-size: 2.2rem;
    font-weight: 700;
    background: linear-gradient(90deg, #636EFA, #00CC96, #FECB52);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 5px;
}
.dashboard-header p {
    color: rgba(255,255,255,0.5);
    font-size: 1rem;
}

/* Section headers */
.section-header {
    font-size: 1.3rem;
    font-weight: 600;
    color: #e0e0e0;
    margin: 30px 0 15px;
    padding-bottom: 8px;
    border-bottom: 2px solid rgba(99,110,250,0.3);
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: rgba(255,255,255,0.03);
    border-radius: 12px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 8px 20px;
    color: rgba(255,255,255,0.6);
}
.stTabs [aria-selected="true"] {
    background: rgba(99,110,250,0.2);
    color: #636EFA;
}
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def metric_card(label, value, delta=None, delta_dir="up"):
    delta_html = ""
    if delta is not None:
        cls = "delta-up" if delta_dir == "up" else "delta-down"
        arrow = "▲" if delta_dir == "up" else "▼"
        delta_html = f'<div class="metric-delta {cls}">{arrow} {delta}</div>'
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """

def short_city(name):
    return name.replace("Weighted average of eight capital cities", "All Cities")

def short_group(name):
    mapping = {
        "All groups CPI": "All Groups",
        "Food and non-alcoholic beverages": "Food & Beverages",
        "Alcohol and tobacco": "Alcohol & Tobacco",
        "Clothing and footwear": "Clothing",
        "Housing": "Housing",
        "Furnishings, household equipment and services": "Furnishings",
        "Health": "Health",
        "Transport": "Transport",
        "Communication": "Communication",
        "Recreation and culture": "Recreation",
        "Education": "Education",
        "Insurance and financial services": "Insurance & Finance",
    }
    return mapping.get(name, name[:20])


# ──────────────────────────────────────────────────────────────────────
# Load Data
# ──────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def get_data():
    t9 = load_table9()
    t11 = load_table11()
    t17 = load_table17()
    return t9, t11, t17


# ──────────────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🇦🇺 CPI Dashboard")
    st.markdown("**DVN Group 7** — UTS 36104")
    st.divider()
    st.markdown("**Data Source:** ABS Cat. 6401.0")
    st.markdown("**Period:** Apr 2024 – Feb 2026")
    st.markdown("**Index Ref:** Sep 2025 = 100")
    st.divider()
    st.caption("© 2026 DVN Group 7 · CC BY 4.0")


# ──────────────────────────────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="dashboard-header">
    <h1>Consumer Price Index — Australia</h1>
    <p>Interactive exploration of CPI trends across expenditure groups and capital cities (2024–2026)</p>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────
# Load & validate
# ──────────────────────────────────────────────────────────────────────

with st.spinner("Loading ABS data..."):
    t9, t11, t17 = get_data()

if t9.empty:
    st.error("Could not load Table 9 data. Check the data/ folder.")
    st.stop()

# Determine the "All Cities" label used across all tabs
all_cities_label = [c for c in t9["city"].unique() if "eight capital" in c.lower() or "weighted" in c.lower()]
city_filter = all_cities_label[0] if all_cities_label else t9["city"].unique()[0]


# ──────────────────────────────────────────────────────────────────────
# Tabs
# ──────────────────────────────────────────────────────────────────────

tab_overview, tab_groups, tab_cities, tab_trends = st.tabs([
    "📊 Overview", "🛒 Expenditure Groups", "🏙️ City Comparison", "📈 Historical Trends"
])


# ═══════════════════════════════════════════════════════════════════════
# TAB 1 — Overview
# ═══════════════════════════════════════════════════════════════════════

with tab_overview:
    headline = t9[(t9["city"] == city_filter) & (t9["group"].str.contains("All groups", case=False, na=False))]
    headline = headline.sort_values("date")

    if not headline.empty:
        latest = headline.iloc[-1]
        prev = headline.iloc[-2] if len(headline) > 1 else None

        # Monthly change
        m_change = ((latest["index_value"] / prev["index_value"]) - 1) * 100 if prev is not None else 0

        # Annual change from Table 11
        ann_change = None
        if not t11.empty:
            t11_headline = t11[
                (t11["city"].str.contains("eight capital|weighted", case=False, na=False)) &
                (t11["group"].str.contains("All groups", case=False, na=False))
            ].sort_values("date")
            if not t11_headline.empty:
                ann_change = t11_headline.iloc[-1]["annual_change_pct"]

        # KPI Cards
        cols = st.columns(4)
        with cols[0]:
            st.markdown(metric_card("Latest CPI Index", f"{latest['index_value']:.1f}",
                                     f"{m_change:+.2f}% MoM",
                                     "up" if m_change > 0 else "down"), unsafe_allow_html=True)
        with cols[1]:
            st.markdown(metric_card("Latest Period",
                                     latest["date"].strftime("%b %Y")), unsafe_allow_html=True)
        with cols[2]:
            if ann_change is not None:
                st.markdown(metric_card("Annual Inflation", f"{ann_change:.1f}%",
                                         "Year-on-Year",
                                         "up" if ann_change > 0 else "down"), unsafe_allow_html=True)
            else:
                st.markdown(metric_card("Monthly Change", f"{m_change:+.2f}%"), unsafe_allow_html=True)
        with cols[3]:
            st.markdown(metric_card("Reference", "Sep 2025 = 100"), unsafe_allow_html=True)

    # Headline CPI trend
    st.markdown('<div class="section-header">Headline CPI Trend — All Cities</div>', unsafe_allow_html=True)
    if not headline.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=headline["date"], y=headline["index_value"],
            mode="lines+markers",
            line=dict(color="#636EFA", width=3),
            marker=dict(size=6),
            name="All Groups CPI",
        ))
        fig.add_hline(y=100, line_dash="dash", line_color="rgba(255,255,255,0.3)",
                      annotation_text="Sep 2025 = 100")
        fig.update_layout(**PLOTLY_LAYOUT, title="CPI Index — Weighted Average of Eight Capital Cities",
                          yaxis_title="Index (Sep 2025 = 100)", xaxis_title="", height=400)
        st.plotly_chart(fig, width="stretch")

    # Latest group breakdown
    st.markdown('<div class="section-header">Latest CPI by Expenditure Group</div>', unsafe_allow_html=True)
    latest_date = t9["date"].max()
    latest_groups = t9[
        (t9["date"] == latest_date) &
        (t9["city"] == city_filter) &
        (~t9["group"].str.contains("All groups", case=False, na=False))
    ].copy()
    latest_groups["short_group"] = latest_groups["group"].apply(short_group)

    if not latest_groups.empty:
        latest_groups = latest_groups.sort_values("index_value", ascending=True)
        fig = px.bar(
            latest_groups, x="index_value", y="short_group",
            orientation="h", color="index_value",
            color_continuous_scale=["#00CC96", "#FECB52", "#EF553B"],
            labels={"index_value": "Index Value", "short_group": ""},
        )
        fig.add_vline(x=100, line_dash="dash", line_color="rgba(255,255,255,0.3)")
        fig.update_layout(**PLOTLY_LAYOUT, title=f"CPI Index by Group — {latest_date.strftime('%b %Y')}",
                          showlegend=False, coloraxis_showscale=False, height=450)
        st.plotly_chart(fig, width="stretch")


# ═══════════════════════════════════════════════════════════════════════
# TAB 2 — Expenditure Groups
# ═══════════════════════════════════════════════════════════════════════

with tab_groups:
    st.markdown('<div class="section-header">Expenditure Group Analysis</div>', unsafe_allow_html=True)

    available_groups = sorted([g for g in t9["group"].unique() if "All groups" not in g])
    selected_groups = st.multiselect(
        "Select expenditure groups", available_groups,
        default=available_groups[:5],
        key="group_select"
    )

    if selected_groups:
        # Index trend by group
        grp_data = t9[
            (t9["city"] == city_filter) &
            (t9["group"].isin(selected_groups))
        ].copy()
        grp_data["short_group"] = grp_data["group"].apply(short_group)

        fig = px.line(
            grp_data, x="date", y="index_value", color="short_group",
            color_discrete_sequence=GROUP_COLORS,
            labels={"index_value": "Index (Sep 2025=100)", "date": "", "short_group": "Group"},
        )
        fig.add_hline(y=100, line_dash="dash", line_color="rgba(255,255,255,0.2)")
        fig.update_traces(line_width=2.5)
        fig.update_layout(**PLOTLY_LAYOUT, title="CPI Index Trend by Expenditure Group", height=500)
        st.plotly_chart(fig, width="stretch")

        # Annual % change by group (if available)
        if not t11.empty:
            st.markdown('<div class="section-header">Annual % Change by Group</div>', unsafe_allow_html=True)
            t11_latest = t11[
                (t11["date"] == t11["date"].max()) &
                (t11["city"].str.contains("eight capital|weighted", case=False, na=False)) &
                (~t11["group"].str.contains("All groups", case=False, na=False))
            ].copy()
            t11_latest["short_group"] = t11_latest["group"].apply(short_group)

            if not t11_latest.empty:
                t11_latest = t11_latest.sort_values("annual_change_pct", ascending=True)
                colors = ["#00CC96" if v < 2 else "#FECB52" if v < 4 else "#EF553B"
                          for v in t11_latest["annual_change_pct"]]
                fig = go.Figure(go.Bar(
                    x=t11_latest["annual_change_pct"], y=t11_latest["short_group"],
                    orientation="h", marker_color=colors,
                    text=[f"{v:.1f}%" for v in t11_latest["annual_change_pct"]],
                    textposition="outside",
                ))
                fig.add_vline(x=0, line_color="rgba(255,255,255,0.3)")
                fig.update_layout(
                    **PLOTLY_LAYOUT,
                    title=f"Annual CPI Change by Group — {t11['date'].max().strftime('%b %Y')}",
                    xaxis_title="Annual % Change", height=450,
                )
                st.plotly_chart(fig, width="stretch")

        # Heatmap: Groups × Time
        st.markdown('<div class="section-header">CPI Heatmap — Groups Over Time</div>', unsafe_allow_html=True)
        heat_data = t9[
            (t9["city"] == city_filter) &
            (~t9["group"].str.contains("All groups", case=False, na=False))
        ].copy()
        heat_data["short_group"] = heat_data["group"].apply(short_group)
        heat_data["month"] = heat_data["date"].dt.strftime("%Y-%m")

        pivot = heat_data.pivot_table(index="short_group", columns="month", values="index_value")
        if not pivot.empty:
            fig = px.imshow(
                pivot, color_continuous_scale="RdYlGn_r", aspect="auto",
                labels=dict(x="Month", y="Group", color="Index"),
            )
            fig.update_layout(**PLOTLY_LAYOUT, title="CPI Heatmap", height=450)
            st.plotly_chart(fig, width="stretch")


# ═══════════════════════════════════════════════════════════════════════
# TAB 3 — City Comparison
# ═══════════════════════════════════════════════════════════════════════

with tab_cities:
    st.markdown('<div class="section-header">Capital City Comparison</div>', unsafe_allow_html=True)

    actual_cities = [c for c in t9["city"].unique() if "weighted" not in c.lower() and "eight" not in c.lower()]

    # Latest All Groups CPI by city
    city_latest = t9[
        (t9["date"] == t9["date"].max()) &
        (t9["group"].str.contains("All groups", case=False, na=False)) &
        (t9["city"].isin(actual_cities))
    ].copy()
    city_latest["short_city"] = city_latest["city"].apply(short_city)

    if not city_latest.empty:
        city_latest = city_latest.sort_values("index_value", ascending=False)

        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(
                city_latest, x="short_city", y="index_value",
                color="short_city",
                color_discrete_map={short_city(k): v for k, v in CITY_COLORS.items()},
                labels={"index_value": "CPI Index", "short_city": ""},
            )
            fig.add_hline(y=100, line_dash="dash", line_color="rgba(255,255,255,0.3)",
                          annotation_text="Baseline")
            fig.update_layout(**PLOTLY_LAYOUT, title="Latest CPI by City", showlegend=False, height=400)
            st.plotly_chart(fig, width="stretch")

        with col2:
            # Radar chart
            cats = city_latest["short_city"].tolist()
            vals = city_latest["index_value"].tolist()
            fig = go.Figure(go.Scatterpolar(
                r=vals + [vals[0]], theta=cats + [cats[0]],
                fill="toself", fillcolor="rgba(99,110,250,0.2)",
                line=dict(color="#636EFA", width=2),
            ))
            fig.update_layout(
                **PLOTLY_LAYOUT,
                polar=dict(
                    bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(gridcolor="rgba(255,255,255,0.1)", showticklabels=True),
                    angularaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
                ),
                title="CPI Distribution Across Cities", height=400,
            )
            st.plotly_chart(fig, width="stretch")

    # CPI Trend by City
    st.markdown('<div class="section-header">CPI Trend by City</div>', unsafe_allow_html=True)

    selected_cities = st.multiselect(
        "Select cities", actual_cities, default=actual_cities[:4], key="city_select"
    )

    if selected_cities:
        city_trend = t9[
            (t9["city"].isin(selected_cities)) &
            (t9["group"].str.contains("All groups", case=False, na=False))
        ].copy()
        city_trend["short_city"] = city_trend["city"].apply(short_city)

        fig = px.line(
            city_trend, x="date", y="index_value", color="short_city",
            color_discrete_map={short_city(k): v for k, v in CITY_COLORS.items()},
            labels={"index_value": "CPI Index", "date": "", "short_city": "City"},
        )
        fig.add_hline(y=100, line_dash="dash", line_color="rgba(255,255,255,0.2)")
        fig.update_traces(line_width=2.5)
        fig.update_layout(**PLOTLY_LAYOUT, title="All Groups CPI — City Comparison", height=450)
        st.plotly_chart(fig, width="stretch")

    # City × Group heatmap
    st.markdown('<div class="section-header">City × Group Matrix</div>', unsafe_allow_html=True)
    matrix = t9[
        (t9["date"] == t9["date"].max()) &
        (~t9["group"].str.contains("All groups", case=False, na=False)) &
        (t9["city"].isin(actual_cities))
    ].copy()
    matrix["short_city"] = matrix["city"].apply(short_city)
    matrix["short_group"] = matrix["group"].apply(short_group)

    pivot_m = matrix.pivot_table(index="short_group", columns="short_city", values="index_value")
    if not pivot_m.empty:
        fig = px.imshow(
            pivot_m, color_continuous_scale="Viridis", aspect="auto",
            labels=dict(x="City", y="Group", color="Index"),
        )
        fig.update_layout(**PLOTLY_LAYOUT, title="Latest CPI: Group × City", height=500)
        st.plotly_chart(fig, width="stretch")


# ═══════════════════════════════════════════════════════════════════════
# TAB 4 — Historical Trends
# ═══════════════════════════════════════════════════════════════════════

with tab_trends:
    st.markdown('<div class="section-header">Historical Quarterly CPI</div>', unsafe_allow_html=True)

    if not t17.empty:
        # Filter for index numbers
        idx_data = t17[t17["measure"].str.contains("Index", case=False, na=False)]

        if not idx_data.empty:
            # Get unique descriptions for selection
            descs = idx_data["description"].unique().tolist()
            # Try to find "Weighted average" or "All groups"
            default_descs = [d for d in descs if "weighted" in d.lower() or "eight capital" in d.lower()]
            if not default_descs:
                default_descs = descs[:1]

            year_range = st.slider(
                "Year range",
                min_value=int(idx_data["date"].dt.year.min()),
                max_value=int(idx_data["date"].dt.year.max()),
                value=(1990, int(idx_data["date"].dt.year.max())),
                key="year_slider",
            )

            filtered = idx_data[
                (idx_data["date"].dt.year >= year_range[0]) &
                (idx_data["date"].dt.year <= year_range[1])
            ]

            # Plot all city series
            cities_in_data = filtered["city"].unique()
            selected_hist = st.multiselect(
                "Select series", list(cities_in_data),
                default=list(cities_in_data)[:3],
                key="hist_select",
            )

            if selected_hist:
                plot_data = filtered[filtered["city"].isin(selected_hist)]
                fig = px.line(
                    plot_data, x="date", y="value", color="city",
                    labels={"value": "CPI Index", "date": "", "city": "Series"},
                )
                fig.update_traces(line_width=2)
                fig.update_layout(**PLOTLY_LAYOUT,
                                  title=f"Quarterly CPI — {year_range[0]} to {year_range[1]}",
                                  height=500)
                st.plotly_chart(fig, width="stretch")

        # Percentage change series
        pct_data = t17[t17["measure"].str.contains("Percentage|Percent", case=False, na=False)]
        if not pct_data.empty:
            st.markdown('<div class="section-header">Quarterly % Change</div>', unsafe_allow_html=True)
            pct_filtered = pct_data[
                (pct_data["date"].dt.year >= year_range[0]) &
                (pct_data["date"].dt.year <= year_range[1])
            ]
            pct_cities = pct_filtered["city"].unique()
            sel_pct = st.multiselect(
                "Select series", list(pct_cities),
                default=list(pct_cities)[:2],
                key="pct_select",
            )
            if sel_pct:
                pct_plot = pct_filtered[pct_filtered["city"].isin(sel_pct)]
                fig = px.line(
                    pct_plot, x="date", y="value", color="city",
                    labels={"value": "% Change", "date": "", "city": "Series"},
                )
                fig.add_hline(y=0, line_color="rgba(255,255,255,0.3)")
                fig.update_traces(line_width=1.5)
                fig.update_layout(**PLOTLY_LAYOUT, title="Quarterly CPI % Change", height=400)
                st.plotly_chart(fig, width="stretch")
    else:
        st.info("Quarterly historical data not available.")


# ──────────────────────────────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────────────────────────────

st.divider()
st.markdown("""
<div style="text-align:center; color:rgba(255,255,255,0.3); font-size:0.8rem; padding:15px 0;">
    Data: Australian Bureau of Statistics · Cat. No. 6401.0 · CC BY 4.0<br>
    DVN Group 7 — 36104 Data Visualisation · UTS 2026
</div>
""", unsafe_allow_html=True)
