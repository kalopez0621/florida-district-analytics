import streamlit as st
import pandas as pd
import plotly.express as px

# Page configuration - must be set before any other Streamlit commands
st.set_page_config(
    page_title="Florida District Assessment Dashboard",
    page_icon="\U0001F4CA",
    layout="wide"
)

# --- Custom CSS for brand styling ---
st.markdown("""
<style>
    /* Brand colors */
    :root {
        --navy: #1A2332;
        --rust: #B8542A;
        --cream: #F4F1EA;
        --sage: #6B8F71;
    }

    /* Main background */
    .stApp {
        background-color: #F4F1EA;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #1A2332;
    }
    section[data-testid="stSidebar"] * {
        color: #F4F1EA !important;
    }
    section[data-testid="stSidebar"] .stMultiSelect label {
        font-weight: 600;
        font-size: 0.95rem;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: white;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        font-weight: 600;
        color: #1A2332;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1A2332 !important;
        color: #F4F1EA !important;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background-color: white;
        border-radius: 8px;
        padding: 12px 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    div[data-testid="stMetric"] label {
        color: #1A2332 !important;
        font-weight: 600;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #B8542A !important;
    }

    /* Headers */
    h1 {
        color: #1A2332 !important;
    }
    h2, h3 {
        color: #1A2332 !important;
        border-bottom: 2px solid #B8542A;
        padding-bottom: 6px;
    }

    /* Dividers */
    hr {
        border-color: #B8542A !important;
        opacity: 0.3;
    }

    /* Dataframe styling */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("district_data_v4.csv", dtype=str)
    num_cols = ["GRADE", "2526 Absences", "Exc Abs", "Unexc Abs",
                "FAST_ELA_PM3.SS", "FAST_ELA_PM2.SS", "FAST_ELA_PM1.SS",
                "FAST_Math_PM3.SS", "FAST_Math_PM2.SS", "FAST_Math_PM1.SS",
                "2425 ELA_SS", "2425 MATH_SS",
                "ELA Pts4LG", "Math.Pts4LG"]
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df
df = load_data()

st.markdown("""
<h1 style="margin-bottom: 0; font-size: 2rem;">Florida District Assessment Dashboard</h1>
<p style="color: #B8542A; font-size: 1.1rem; margin-top: 4px; margin-bottom: 24px;">
    Miami-Dade Middle Schools &nbsp;&middot;&nbsp; 2025&ndash;2026 FAST Assessment Data &nbsp;&middot;&nbsp; Synthetic Dataset
</p>
""", unsafe_allow_html=True)

# Sidebar filters
st.sidebar.markdown("""
<div style="text-align: center; padding: 8px 0 16px 0;">
    <span style="font-size: 1.4rem; font-weight: 700; letter-spacing: 1px;">&#128202; FILTERS</span>
</div>
""", unsafe_allow_html=True)
school_name_map = {
    "6128": "Somerset Academy Bay",
    "6161": "Lawton Chiles Middle",
    "6171": "Henry H. Filer Middle"
}
school_options = list(school_name_map.values())
selected_schools = st.sidebar.multiselect(
    "School", school_options, default=school_options)
loc_from_name = {v: k for k, v in school_name_map.items()}
selected_locs = [loc_from_name[name] for name in selected_schools]

grades = st.sidebar.multiselect(
    "Grade", sorted(df["GRADE"].dropna().unique()),
    default=sorted(df["GRADE"].dropna().unique()))

filtered = df[(df["LOC"].isin(selected_locs)) & (df["GRADE"].isin(grades))]

st.caption(f"Showing **{len(filtered):,}** students across **{len(selected_schools)}** schools")

tab1, tab2, tab3, tab4 = st.tabs(["School Performance", "Subgroup Equity", "Learning Gains", "PM3 Predictor"])

with tab1:
    st.header("School Performance Overview")

    school_names = {
        "6128": "Somerset Academy Bay",
        "6161": "Lawton Chiles Middle",
        "6171": "Henry H. Filer Middle"}

    metrics = []
    for loc in filtered["LOC"].unique():
        s = filtered[filtered["LOC"] == loc]
        n = len(s)

        ela_pm3 = pd.to_numeric(s["FAST_ELA_PM3.Level"], errors="coerce")
        ela_ach = (ela_pm3 >= 3).sum() / n * 100

        ela_pm3_ss = s["FAST_ELA_PM3.SS"].dropna()
        ela_prior = s.loc[ela_pm3_ss.index, "2425 ELA_SS"]
        ela_pts = s.loc[ela_pm3_ss.index, "ELA Pts4LG"]
        ela_met = (ela_pm3_ss.astype(float) >= ela_prior.astype(float) + ela_pts.astype(float))
        ela_lg = ela_met.sum() / len(ela_met) * 100 if len(ela_met) > 0 else 0

        l25_ela = s[s["ELA L25/35"] == "L25"]
        if len(l25_ela) > 0:
            l25_met = (l25_ela["FAST_ELA_PM3.SS"].astype(float) >=
                       l25_ela["2425 ELA_SS"].astype(float) +
                       l25_ela["ELA Pts4LG"].astype(float))
            ela_lg_l25 = l25_met.sum() / len(l25_met) * 100
        else:
            ela_lg_l25 = 0

        non_alg = s[s["COURSE_TITLE"] != "Algebra 1 Hon"]
        if len(non_alg) > 0:
            math_pm3 = pd.to_numeric(non_alg["FAST_Math_PM3.Level"], errors="coerce")
            math_ach = (math_pm3 >= 3).sum() / len(non_alg) * 100
        else:
            math_ach = 0

        math_pm3_ss = s["FAST_Math_PM3.SS"].dropna()
        math_prior = s.loc[math_pm3_ss.index, "2425 MATH_SS"]
        math_pts = s.loc[math_pm3_ss.index, "Math.Pts4LG"]
        math_met = (math_pm3_ss.astype(float) >= math_prior.astype(float) + math_pts.astype(float))
        math_lg = math_met.sum() / len(math_met) * 100 if len(math_met) > 0 else 0

        l25_math = s[s["MATH L25/35"] == "L25"]
        if len(l25_math) > 0:
            l25m_met = (l25_math["FAST_Math_PM3.SS"].astype(float) >=
                        l25_math["2425 MATH_SS"].astype(float) +
                        l25_math["Math.Pts4LG"].astype(float))
            math_lg_l25 = l25m_met.sum() / len(l25m_met) * 100
        else:
            math_lg_l25 = 0

        alg1 = s[s["COURSE_TITLE"] == "Algebra 1 Hon"]
        if len(alg1) > 0:
            alg1_pm3 = pd.to_numeric(alg1["FAST_Math_PM3.Level"], errors="coerce")
            ms_accel = (alg1_pm3 >= 3).sum() / len(alg1) * 100
        else:
            ms_accel = 0

        metrics.append({
            "School": school_names.get(loc, loc),
            "Students": n,
            "ELA Achievement": round(ela_ach, 1),
            "ELA Learning Gains": round(ela_lg, 1),
            "ELA LG L25": round(ela_lg_l25, 1),
            "Math Achievement": round(math_ach, 1),
            "Math Learning Gains": round(math_lg, 1),
            "Math LG L25": round(math_lg_l25, 1),
            "MS Acceleration": round(ms_accel, 1)
        })

    metrics_df = pd.DataFrame(metrics)

    for _, row in metrics_df.iterrows():
        st.subheader(row["School"])

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Students", int(row["Students"]))
        c2.metric("ELA Proficiency", f"{row['ELA Achievement']}%")
        c3.metric("ELA Learning Gains", f"{row['ELA Learning Gains']}%")
        c4.metric("ELA LG Lowest 25%", f"{row['ELA LG L25']}%")

        c5, c6, c7, c8 = st.columns(4)
        c5.metric("MS Acceleration", f"{row['MS Acceleration']}%")
        c6.metric("Math Proficiency", f"{row['Math Achievement']}%")
        c7.metric("Math Learning Gains", f"{row['Math Learning Gains']}%")
        c8.metric("Math LG Lowest 25%", f"{row['Math LG L25']}%")

        st.divider()

    st.subheader("Proficiency Comparison by School")
    chart_data = metrics_df.melt(
        id_vars=["School"],
        value_vars=["ELA Achievement", "Math Achievement", "MS Acceleration"],
        var_name="Metric", value_name="Percent"
    )
    fig = px.bar(
        chart_data, x="School", y="Percent", color="Metric",
        barmode="group", text="Percent",
        color_discrete_sequence=["#1A2332", "#B8542A", "#6B8F71"]
    )
    fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
    fig.update_layout(yaxis_title="% Proficient", yaxis_range=[0, 105])
    st.plotly_chart(fig, width="stretch")


with tab2:
    st.header("Subgroup Equity Analysis")

    school_names = {
        "6128": "Somerset Academy Bay",
        "6161": "Lawton Chiles Middle",
        "6171": "Henry H. Filer Middle"
    }

    metric_choice = st.selectbox(
        "Select Metric",
        ["ELA Proficiency", "Math Proficiency", "ELA Learning Gains", "Math Learning Gains"]
    )

    def calc_metric(group, metric):
        if metric == "ELA Proficiency":
            vals = pd.to_numeric(group["FAST_ELA_PM3.Level"], errors="coerce")
            return (vals >= 3).mean() * 100 if len(vals) > 0 else 0
        elif metric == "Math Proficiency":
            non_alg = group[group["COURSE_TITLE"] != "Algebra 1 Hon"]
            if len(non_alg) == 0:
                return 0
            vals = pd.to_numeric(non_alg["FAST_Math_PM3.Level"], errors="coerce")
            return (vals >= 3).mean() * 100
        elif metric == "ELA Learning Gains":
            pm3 = pd.to_numeric(group["FAST_ELA_PM3.SS"], errors="coerce")
            prior = pd.to_numeric(group["2425 ELA_SS"], errors="coerce")
            pts = pd.to_numeric(group["ELA Pts4LG"], errors="coerce")
            valid = pm3.notna() & prior.notna() & pts.notna()
            if valid.sum() == 0:
                return 0
            return (pm3[valid] >= prior[valid] + pts[valid]).mean() * 100
        elif metric == "Math Learning Gains":
            pm3 = pd.to_numeric(group["FAST_Math_PM3.SS"], errors="coerce")
            prior = pd.to_numeric(group["2425 MATH_SS"], errors="coerce")
            pts = pd.to_numeric(group["Math.Pts4LG"], errors="coerce")
            valid = pm3.notna() & prior.notna() & pts.notna()
            if valid.sum() == 0:
                return 0
            return (pm3[valid] >= prior[valid] + pts[valid]).mean() * 100

    st.subheader("ELL vs Non-ELL")
    ell_data = []
    for loc in filtered["LOC"].unique():
        s = filtered[filtered["LOC"] == loc]
        for status in ["Y", "N"]:
            group = s[s["ELL"] == status]
            if len(group) > 0:
                ell_data.append({
                    "School": school_names.get(loc, loc),
                    "ELL Status": "ELL" if status == "Y" else "Non-ELL",
                    "Percent": round(calc_metric(group, metric_choice), 1),
                    "Count": len(group)
                })

    ell_df = pd.DataFrame(ell_data)
    fig_ell = px.bar(
        ell_df, x="School", y="Percent", color="ELL Status",
        barmode="group", text="Percent",
        color_discrete_sequence=["#B8542A", "#1A2332"]
    )
    fig_ell.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
    fig_ell.update_layout(yaxis_title=f"% {metric_choice}", yaxis_range=[0, 105])
    st.plotly_chart(fig_ell, width="stretch")

    st.subheader("ESE vs Non-ESE")
    ese_data = []
    for loc in filtered["LOC"].unique():
        s = filtered[filtered["LOC"] == loc]
        for status in ["Y", "N"]:
            group = s[s["ESE"] == status]
            if len(group) > 0:
                ese_data.append({
                    "School": school_names.get(loc, loc),
                    "ESE Status": "ESE" if status == "Y" else "Non-ESE",
                    "Percent": round(calc_metric(group, metric_choice), 1),
                    "Count": len(group)
                })

    ese_df = pd.DataFrame(ese_data)
    fig_ese = px.bar(
        ese_df, x="School", y="Percent", color="ESE Status",
        barmode="group", text="Percent",
        color_discrete_sequence=["#B8542A", "#1A2332"]
    )
    fig_ese.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
    fig_ese.update_layout(yaxis_title=f"% {metric_choice}", yaxis_range=[0, 105])
    st.plotly_chart(fig_ese, width="stretch")

    st.subheader("By Ethnicity")
    eth_labels = {"H": "Hispanic", "B": "Black", "W": "White", "A": "Asian", "M": "Multi"}
    eth_data = []
    for loc in filtered["LOC"].unique():
        s = filtered[filtered["LOC"] == loc]
        for code, label in eth_labels.items():
            group = s[s["ETHN"] == code]
            if len(group) >= 5:
                eth_data.append({
                    "School": school_names.get(loc, loc),
                    "Ethnicity": label,
                    "Percent": round(calc_metric(group, metric_choice), 1),
                    "Count": len(group)
                })

    if len(eth_data) > 0:
        eth_df = pd.DataFrame(eth_data)
        fig_eth = px.bar(
            eth_df, x="School", y="Percent", color="Ethnicity",
            barmode="group", text="Percent",
            color_discrete_sequence=["#1A2332", "#B8542A", "#6B8F71", "#D4A574", "#7A9BBF"]
        )
        fig_eth.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
        fig_eth.update_layout(yaxis_title=f"% {metric_choice}", yaxis_range=[0, 105])
        st.plotly_chart(fig_eth, width="stretch")
    else:
        st.write("Not enough students per ethnicity group to display.")

with tab3:
    st.header("Learning Gains & Growth")

    school_names = {
        "6128": "Somerset Academy Bay",
        "6161": "Lawton Chiles Middle",
        "6171": "Henry H. Filer Middle"
    }

    subject = st.radio("Subject", ["ELA", "Math"], horizontal=True)

    if subject == "ELA":
        pm3_col = "FAST_ELA_PM3.SS"
        pm2_col = "FAST_ELA_PM2.SS"
        pm1_col = "FAST_ELA_PM1.SS"
        prior_col = "2425 ELA_SS"
        pts_col = "ELA Pts4LG"
        l25_col = "ELA L25/35"
        lvl_col = "FAST_ELA_PM3.Level"
    else:
        pm3_col = "FAST_Math_PM3.SS"
        pm2_col = "FAST_Math_PM2.SS"
        pm1_col = "FAST_Math_PM1.SS"
        prior_col = "2425 MATH_SS"
        pts_col = "Math.Pts4LG"
        l25_col = "MATH L25/35"
        lvl_col = "FAST_Math_PM3.Level"

    filt = filtered.copy()
    filt["_pm3"] = pd.to_numeric(filt[pm3_col], errors="coerce")
    filt["_prior"] = pd.to_numeric(filt[prior_col], errors="coerce")
    filt["_pts4lg"] = pd.to_numeric(filt[pts_col], errors="coerce")
    filt["_met_lg"] = filt["_pm3"] >= filt["_prior"] + filt["_pts4lg"]
    filt["_is_l25"] = filt[l25_col] == "L25"

    filt = filt[filt["_pm3"].notna()]

    st.subheader("Learning Gains by School")
    lg_summary = []
    for loc in filt["LOC"].unique():
        s = filt[filt["LOC"] == loc]
        total = len(s)
        met = s["_met_lg"].sum()
        l25 = s[s["_is_l25"]]
        l25_met = l25["_met_lg"].sum() if len(l25) > 0 else 0

        lg_summary.append({
            "School": school_names.get(loc, loc),
            "Total Students": total,
            "Met LG": int(met),
            "LG Rate": round(met / total * 100, 1) if total > 0 else 0,
            "L25 Students": len(l25),
            "L25 Met": int(l25_met),
            "L25 Rate": round(l25_met / len(l25) * 100, 1) if len(l25) > 0 else 0
        })

    lg_df = pd.DataFrame(lg_summary)

    for _, row in lg_df.iterrows():
        st.subheader(row["School"])
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Met Learning Gains", f"{row['Met LG']} / {row['Total Students']}")
        c2.metric("LG Rate", f"{row['LG Rate']}%")
        c3.metric("L25 Met LG", f"{row['L25 Met']} / {row['L25 Students']}")
        c4.metric("L25 Rate", f"{row['L25 Rate']}%")

    st.subheader("Met vs Not Met Learning Gains")
    met_data = []
    for loc in filt["LOC"].unique():
        s = filt[filt["LOC"] == loc]
        met_data.append({"School": school_names.get(loc, loc), "Status": "Met", "Count": int(s["_met_lg"].sum())})
        met_data.append({"School": school_names.get(loc, loc), "Status": "Not Met", "Count": int((~s["_met_lg"]).sum())})

    met_df = pd.DataFrame(met_data)
    fig_met = px.bar(
        met_df, x="School", y="Count", color="Status",
        barmode="stack", text="Count",
        color_discrete_sequence=["#6B8F71", "#B8542A"]
    )
    fig_met.update_layout(yaxis_title="Students")
    st.plotly_chart(fig_met, width="stretch")

    st.subheader("Score Trajectory: PM1 > PM2 > PM3")
    filt["_pm1"] = pd.to_numeric(filt[pm1_col], errors="coerce")
    filt["_pm2"] = pd.to_numeric(filt[pm2_col], errors="coerce")

    trajectory = []
    for loc in filt["LOC"].unique():
        s = filt[filt["LOC"] == loc]
        valid = s[s["_pm1"].notna() & s["_pm2"].notna() & s["_pm3"].notna()]
        if len(valid) > 0:
            trajectory.append({"School": school_names.get(loc, loc), "Window": "PM1", "Avg SS": round(valid["_pm1"].mean(), 1)})
            trajectory.append({"School": school_names.get(loc, loc), "Window": "PM2", "Avg SS": round(valid["_pm2"].mean(), 1)})
            trajectory.append({"School": school_names.get(loc, loc), "Window": "PM3", "Avg SS": round(valid["_pm3"].mean(), 1)})

    if len(trajectory) > 0:
        traj_df = pd.DataFrame(trajectory)
        fig_traj = px.line(
            traj_df, x="Window", y="Avg SS", color="School",
            markers=True, text="Avg SS",
            color_discrete_sequence=["#1A2332", "#B8542A", "#6B8F71"]
        )
        fig_traj.update_traces(textposition="top center")
        fig_traj.update_layout(yaxis_title="Average Scale Score")
        st.plotly_chart(fig_traj, width="stretch")

    st.subheader("Students Who Did Not Meet Learning Gains")
    at_risk = filt[~filt["_met_lg"]].copy()
    at_risk["Gap"] = (at_risk["_prior"] + at_risk["_pts4lg"] - at_risk["_pm3"]).astype(int)
    at_risk = at_risk.sort_values("Gap", ascending=False)

    display_cols = {
        "LOC": "School", "NAME": "Student", "GRADE": "Grade",
        "ELL": "ELL", "ESE": "ESE", "COURSE_TITLE": "Course",
        "_prior": "Prior SS", "_pts4lg": "Pts4LG", "_pm3": "PM3 SS", "Gap": "Gap"
    }

    st.dataframe(
        at_risk[list(display_cols.keys())].rename(columns=display_cols).head(25),
        width="stretch",
        hide_index=True
    )

with tab4:
    st.header("PM3 Predictor & Bubble Students")

    school_names = {
        "6128": "Somerset Academy Bay",
        "6161": "Lawton Chiles Middle",
        "6171": "Henry H. Filer Middle"
    }

    subject = st.radio("Subject", ["ELA", "Math"], horizontal=True, key="pred_subject")

    if subject == "ELA":
        pm1_col = "FAST_ELA_PM1.SS"
        pm2_col = "FAST_ELA_PM2.SS"
        pm3_col = "FAST_ELA_PM3.SS"
        lvl_col = "FAST_ELA_PM3.Level"
        prof_cuts = {6: 225, 7: 232, 8: 238}
    else:
        pm1_col = "FAST_Math_PM1.SS"
        pm2_col = "FAST_Math_PM2.SS"
        pm3_col = "FAST_Math_PM3.SS"
        lvl_col = "FAST_Math_PM3.Level"
        prof_cuts = {6: 229, 7: 235, 8: 244}

    pred = filtered.copy()
    pred["_pm1"] = pd.to_numeric(pred[pm1_col], errors="coerce")
    pred["_pm2"] = pd.to_numeric(pred[pm2_col], errors="coerce")
    pred["_pm3_actual"] = pd.to_numeric(pred[pm3_col], errors="coerce")
    pred["_grade"] = pred["GRADE"].astype(int)

    pred = pred[pred["_pm1"].notna() & pred["_pm2"].notna()].copy()

    pred["_growth"] = pred["_pm2"] - pred["_pm1"]
    pred["_predicted_pm3"] = pred["_pm2"] + pred["_growth"]

    pred["_prof_cut"] = pred["_grade"].map(prof_cuts)
    pred["_distance"] = pred["_predicted_pm3"] - pred["_prof_cut"]
    pred["_pred_proficient"] = pred["_predicted_pm3"] >= pred["_prof_cut"]

    st.subheader("Predicted vs Actual Proficiency")

    compare_data = []
    for loc in pred["LOC"].unique():
        s = pred[pred["LOC"] == loc]
        if len(s) == 0:
            continue
        pred_rate = s["_pred_proficient"].mean() * 100
        actual_pm3 = pd.to_numeric(s[lvl_col], errors="coerce")
        actual_rate = (actual_pm3 >= 3).mean() * 100 if actual_pm3.notna().sum() > 0 else 0

        compare_data.append({"School": school_names.get(loc, loc), "Type": "Predicted (from PM1>PM2)", "Rate": round(pred_rate, 1)})
        compare_data.append({"School": school_names.get(loc, loc), "Type": "Actual PM3", "Rate": round(actual_rate, 1)})

    if len(compare_data) > 0:
        comp_df = pd.DataFrame(compare_data)
        fig_comp = px.bar(
            comp_df, x="School", y="Rate", color="Type",
            barmode="group", text="Rate",
            color_discrete_sequence=["#7A9BBF", "#1A2332"]
        )
        fig_comp.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
        fig_comp.update_layout(yaxis_title="% Proficient", yaxis_range=[0, 105])
        st.plotly_chart(fig_comp, width="stretch")

    st.subheader("Bubble Students - Close to Proficiency")
    st.write("Students whose projected PM3 is within range of the proficiency cut. "
             "These are your highest-ROI intervention targets.")

    bubble_range = st.slider(
        "Points from proficiency cut",
        min_value=5, max_value=30, value=15,
        help="Show students whose predicted PM3 is within this many points of Level 3"
    )

    bubble = pred[
        (~pred["_pred_proficient"]) &
        (pred["_distance"] >= -bubble_range)
    ].copy()
    bubble = bubble.sort_values("_distance", ascending=False)

    for loc in pred["LOC"].unique():
        s_bubble = bubble[bubble["LOC"] == loc]
        s_total = pred[pred["LOC"] == loc]
        st.metric(
            school_names.get(loc, loc),
            f"{len(s_bubble)} bubble students",
            f"out of {(~s_total['_pred_proficient']).sum()} projected not proficient"
        )

    if len(bubble) > 0:
        bubble["Points Needed"] = (-bubble["_distance"]).astype(int)
        display = bubble[[
            "LOC", "NAME", "GRADE", "ELL", "ESE", "COURSE_TITLE",
            "_pm1", "_pm2", "_predicted_pm3", "_prof_cut", "Points Needed"
        ]].rename(columns={
            "LOC": "School", "NAME": "Student", "GRADE": "Grade",
            "COURSE_TITLE": "Course", "_pm1": "PM1", "_pm2": "PM2",
            "_predicted_pm3": "Predicted PM3", "_prof_cut": "Prof Cut",
        })

        st.dataframe(display, width="stretch", hide_index=True)
    else:
        st.write("No bubble students in the selected range.")

    st.subheader("Impact Analysis")
    st.write("If all bubble students reached proficiency, here's the impact:")

    for loc in pred["LOC"].unique():
        s = pred[pred["LOC"] == loc]
        s_bubble = bubble[bubble["LOC"] == loc]
        current_prof = s["_pred_proficient"].sum()
        new_prof = current_prof + len(s_bubble)
        current_rate = current_prof / len(s) * 100
        new_rate = new_prof / len(s) * 100

        c1, c2, c3 = st.columns(3)
        c1.metric(school_names.get(loc, loc), f"{current_rate:.0f}% > {new_rate:.0f}%")
        c2.metric("Students to Move", len(s_bubble))
        c3.metric("Proficiency Gain", f"+{new_rate - current_rate:.1f}%")
