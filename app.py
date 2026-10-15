"""Student Performance Analytics - interactive dashboard.
Run:  streamlit run app.py
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from functions import (load_data, process_data, class_summary, subject_analysis, department_analysis,
                       top_performers, at_risk_students, grade_distribution, attendance_correlation,
                       SUBJECTS, PASS_MARK, MIN_ATTENDANCE)

st.set_page_config(page_title="Student Performance Analytics", page_icon="🎓", layout="wide")

st.markdown("""
<style>
.stApp {background: radial-gradient(circle at top left,#1b1f3b 0%,#0d1020 55%);}
.hero {padding:26px 30px;border-radius:18px;margin-bottom:18px;
  background:linear-gradient(120deg,#6c5ce7 0%,#00b4d8 100%);color:white;}
.hero h1 {margin:0;font-size:2rem;} .hero p {margin:4px 0 0;opacity:.9;}
.card {background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);
  border-radius:16px;padding:18px 20px;backdrop-filter:blur(8px);}
.card .label {font-size:.8rem;color:#aab;text-transform:uppercase;letter-spacing:.08em;}
.card .value {font-size:1.9rem;font-weight:700;color:#fff;}
.card .sub {font-size:.8rem;color:#7fe3c3;}
</style>""", unsafe_allow_html=True)

PALETTE = ["#6c5ce7", "#00b4d8", "#00cec9", "#fdcb6e", "#ff7675", "#a29bfe"]


def kpi(label, value, sub=""):
    return f'<div class="card"><div class="label">{label}</div><div class="value">{value}</div><div class="sub">{sub}</div></div>'


def style(fig, h=380):
    fig.update_layout(height=h, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font_color="#e8e8f0", margin=dict(l=10, r=10, t=40, b=10))
    return fig


@st.cache_data
def get_data(file):
    return process_data(load_data(file))


# ---------- Sidebar ----------
st.sidebar.title("🎓 Controls")
upload = st.sidebar.file_uploader("Upload your own CSV", type="csv")
try:
    full = get_data(upload if upload else "students.csv")
except Exception as e:
    st.error(f"Could not load data: {e}")
    st.stop()

depts = st.sidebar.multiselect("Department", sorted(full["Department"].unique()), default=sorted(full["Department"].unique()))
grades = st.sidebar.multiselect("Grade", ["A+", "A", "B", "C", "D", "F"], default=["A+", "A", "B", "C", "D", "F"])
top_n = st.sidebar.slider("Top performers to show", 3, 10, 5)
st.sidebar.caption(f"Pass rule: every subject ≥ {PASS_MARK} and attendance ≥ {MIN_ATTENDANCE}%")

df = full[full["Department"].isin(depts) & full["Grade"].isin(grades)].reset_index(drop=True)
if df.empty:
    st.warning("No students match the filters.")
    st.stop()
s = class_summary(df)

# ---------- Header + KPIs ----------
st.markdown('<div class="hero"><h1>Student Performance Analytics</h1>'
            '<p>Marks, grades, pass/fail and insights — powered by Python, NumPy &amp; Pandas</p></div>', unsafe_allow_html=True)
cols = st.columns(5)
items = [("Students", s["students"], f"Avg attendance {s['avg_attendance']}%"),
         ("Class Average", s["class_average"], f"Median {s['median']}"),
         ("Pass Rate", f"{s['pass_percentage']}%", f"{s['passed']} passed · {s['failed']} failed"),
         ("Highest", s["highest"], s["topper"]),
         ("Lowest", s["lowest"], s["lowest_student"])]
for c, (l, v, sub) in zip(cols, items):
    c.markdown(kpi(l, v, sub), unsafe_allow_html=True)
st.write("")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "📚 Subjects", "🏆 Leaderboard", "⚠️ At-Risk", "👤 Student Profile"])

with tab1:
    c1, c2 = st.columns(2)
    gd = grade_distribution(df).reset_index()
    gd.columns = ["Grade", "Students"]
    c1.plotly_chart(style(px.bar(gd, x="Grade", y="Students", color="Grade", title="Grade Distribution",
                                 color_discrete_sequence=PALETTE)), use_container_width=True)
    ps = df["Status"].value_counts().reset_index()
    ps.columns = ["Status", "Count"]
    c2.plotly_chart(style(px.pie(ps, names="Status", values="Count", hole=.55, title="Pass vs Fail",
                                 color="Status", color_discrete_map={"Pass": "#00cec9", "Fail": "#ff7675"})), use_container_width=True)
    c3, c4 = st.columns(2)
    c3.plotly_chart(style(px.scatter(df, x="Attendance", y="Average", color="Department", hover_name="Name", size="Total",
                                     title=f"Attendance vs Marks (correlation {attendance_correlation(df)})",
                                     color_discrete_sequence=PALETTE)), use_container_width=True)
    c4.plotly_chart(style(px.bar(department_analysis(df), x="Department", y="Avg_Marks", color="Department",
                                 title="Department Average", color_discrete_sequence=PALETTE)), use_container_width=True)

with tab2:
    sa = subject_analysis(df)
    st.plotly_chart(style(px.bar(sa, x="Subject", y="Average", color="Average", text="Average",
                                 color_continuous_scale="Tealgrn", title="Subject-wise Average")), use_container_width=True)
    st.plotly_chart(style(px.box(df.melt(id_vars="Name", value_vars=SUBJECTS, var_name="Subject", value_name="Marks"),
                                 x="Subject", y="Marks", color="Subject", title="Marks Spread per Subject",
                                 color_discrete_sequence=PALETTE)), use_container_width=True)
    st.dataframe(sa, use_container_width=True, hide_index=True)
    st.success(f"Best subject: **{sa.iloc[0]['Subject']}** ({sa.iloc[0]['Average']}) · Weakest: **{sa.iloc[-1]['Subject']}** ({sa.iloc[-1]['Average']})")

with tab3:
    medals = ["🥇", "🥈", "🥉"]
    top = top_performers(df, top_n)
    for c, (_, r) in zip(st.columns(min(3, len(top))), top.head(3).iterrows()):
        c.markdown(kpi(f"{medals[int(r['Rank'])-1] if r['Rank'] <= 3 else '🏅'} Rank {r['Rank']} · {r['Department']}",
                       r["Name"], f"Avg {r['Average']} · Grade {r['Grade']}"), unsafe_allow_html=True)
    st.write("")
    st.dataframe(top, use_container_width=True, hide_index=True)
    st.subheader("Full Results")
    st.dataframe(df[["Rank", "Student_ID", "Name", "Department", *SUBJECTS, "Total", "Average", "Grade", "Status", "Attendance"]],
                 use_container_width=True, hide_index=True)
    st.download_button("⬇ Download report (CSV)", df.to_csv(index=False).encode(), "student_report.csv", "text/csv")

with tab4:
    risk = at_risk_students(df)
    st.metric("Students needing attention", len(risk))
    st.dataframe(risk, use_container_width=True, hide_index=True)

with tab5:
    name = st.selectbox("Select student", df["Name"])
    stu = df[df["Name"] == name].iloc[0]
    avg_marks = df[SUBJECTS].mean()
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=[stu[x] for x in SUBJECTS] + [stu[SUBJECTS[0]]], theta=SUBJECTS + [SUBJECTS[0]],
                                  fill="toself", name=name, line_color="#6c5ce7"))
    fig.add_trace(go.Scatterpolar(r=list(avg_marks) + [avg_marks.iloc[0]], theta=SUBJECTS + [SUBJECTS[0]],
                                  name="Class average", line=dict(color="#00cec9", dash="dash")))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100])), title="Skill Radar")
    a, b = st.columns([1, 1])
    a.plotly_chart(style(fig, 420), use_container_width=True)
    b.markdown(kpi("Rank", f"#{stu['Rank']} of {len(df)}", f"Grade {stu['Grade']} · {stu['Status']}"), unsafe_allow_html=True)
    b.write("")
    b.markdown(kpi("Average / Total", f"{stu['Average']} / {stu['Total']}", f"Attendance {stu['Attendance']}%"), unsafe_allow_html=True)
    b.write("")
    b.markdown(kpi("Remarks", stu["Remarks"], stu["Department"]), unsafe_allow_html=True)