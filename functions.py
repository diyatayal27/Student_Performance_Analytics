"""Reusable calculation & processing functions for the Student Performance Analytics System."""
import numpy as np
import pandas as pd

SUBJECTS = ["Maths", "Physics", "Chemistry", "English", "Computer_Science"]
REQUIRED_COLUMNS = ["Student_ID", "Name", "Department", *SUBJECTS, "Attendance"]
PASS_MARK = 40          # minimum marks needed in EVERY subject
MIN_ATTENDANCE = 75     # minimum attendance % required to pass
GRADE_RULES = [(90, "A+"), (80, "A"), (70, "B"), (60, "C"), (50, "D")]  # else "F"


def load_data(path):
    """Read CSV with Pandas, validate columns and clean bad rows."""
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in CSV: {missing}")
    df = df.drop_duplicates(subset="Student_ID")
    numeric_cols = SUBJECTS + ["Attendance"]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    return df.dropna(subset=numeric_cols).reset_index(drop=True)


def get_grade(average):
    """Grading rule: 90+ A+, 80+ A, 70+ B, 60+ C, 50+ D, otherwise F."""
    for cutoff, grade in GRADE_RULES:
        if average >= cutoff:
            return grade
    return "F"


def calculate_totals(df):
    """Total & average per student using NumPy on the marks matrix."""
    marks = df[SUBJECTS].to_numpy()
    df["Total"] = marks.sum(axis=1)
    df["Average"] = np.round(marks.mean(axis=1), 2)
    return df


def assign_grades(df):
    """Loop over every student's average and assign a grade."""
    grades = []
    for avg in df["Average"]:
        grades.append(get_grade(avg))
    df["Grade"] = grades
    return df


def check_pass_fail(df):
    """Pass = every subject >= PASS_MARK and attendance >= MIN_ATTENDANCE."""
    status, remarks = [], []
    for _, row in df.iterrows():
        failed = [s for s in SUBJECTS if row[s] < PASS_MARK]
        notes = []
        if failed:
            notes.append("Failed: " + ", ".join(failed))
        if row["Attendance"] < MIN_ATTENDANCE:
            notes.append("Low attendance")
        status.append("Fail" if notes else "Pass")
        remarks.append("; ".join(notes) if notes else "-")
    df["Status"] = status
    df["Remarks"] = remarks
    return df


def add_rank(df):
    df["Rank"] = df["Average"].rank(ascending=False, method="min").astype(int)
    return df


def process_data(df):
    """Full pipeline: totals -> grades -> pass/fail -> rank."""
    df = df.copy()
    for step in (calculate_totals, assign_grades, check_pass_fail, add_rank):
        df = step(df)
    return df.sort_values("Rank").reset_index(drop=True)


def class_summary(df):
    """Highest / lowest / average performance and pass-fail statistics."""
    avg = df["Average"].to_numpy()
    passed = int((df["Status"] == "Pass").sum())
    return {
        "students": len(df),
        "topper": df.loc[df["Average"].idxmax(), "Name"],
        "highest": float(avg.max()),
        "lowest_student": df.loc[df["Average"].idxmin(), "Name"],
        "lowest": float(avg.min()),
        "class_average": round(float(avg.mean()), 2),
        "median": round(float(np.median(avg)), 2),
        "std_dev": round(float(avg.std()), 2),
        "passed": passed,
        "failed": len(df) - passed,
        "pass_percentage": round(passed / len(df) * 100, 1),
        "avg_attendance": round(float(df["Attendance"].mean()), 1),
    }


def subject_analysis(df):
    """Subject-wise average, highest, lowest, spread, pass % and topper."""
    rows = []
    for subject in SUBJECTS:
        col = df[subject].to_numpy()
        rows.append({
            "Subject": subject,
            "Average": round(float(col.mean()), 2),
            "Highest": int(col.max()),
            "Lowest": int(col.min()),
            "Std_Dev": round(float(col.std()), 2),
            "Pass_%": round(float((col >= PASS_MARK).mean() * 100), 1),
            "Topper": df.loc[df[subject].idxmax(), "Name"],
        })
    return pd.DataFrame(rows).sort_values("Average", ascending=False).reset_index(drop=True)


def department_analysis(df):
    out = df.groupby("Department").agg(
        Students=("Student_ID", "count"),
        Avg_Marks=("Average", "mean"),
        Avg_Attendance=("Attendance", "mean"),
        Passed=("Status", lambda s: (s == "Pass").sum()),
    ).round(2)
    return out.sort_values("Avg_Marks", ascending=False).reset_index()


def top_performers(df, n=5):
    return df.nlargest(n, "Average")[["Rank", "Student_ID", "Name", "Department", "Total", "Average", "Grade"]]


def at_risk_students(df, threshold=55):
    """Students who failed or whose average is below the threshold."""
    mask = (df["Status"] == "Fail") | (df["Average"] < threshold)
    return df[mask][["Student_ID", "Name", "Department", "Average", "Attendance", "Status", "Remarks"]]


def grade_distribution(df):
    order = ["A+", "A", "B", "C", "D", "F"]
    return df["Grade"].value_counts().reindex(order, fill_value=0)


def attendance_correlation(df):
    """Pearson correlation between attendance and average marks (NumPy)."""
    return round(float(np.corrcoef(df["Attendance"], df["Average"])[0, 1]), 3)