"""Student Performance Analytics System - console report.
Run:  python main.py
"""
import os
import pandas as pd
from functions import (load_data, process_data, class_summary, subject_analysis, department_analysis,
                       top_performers, at_risk_students, grade_distribution, attendance_correlation, SUBJECTS)

DATA_FILE = "students.csv"
pd.set_option("display.width", 200)


def banner(title):
    print("\n" + "=" * 70 + f"\n  {title}\n" + "=" * 70)


def show(df):
    print(df.to_string(index=False))


def main():
    # Step 2 - read data
    raw = load_data(DATA_FILE)
    banner("1. DATASET OVERVIEW")
    print(f"Records : {len(raw)}\nColumns : {list(raw.columns)}\n")
    show(raw.head())

    # Step 3 - process
    df = process_data(raw)
    banner("2. STUDENT RESULTS (ranked)")
    show(df[["Rank", "Student_ID", "Name", "Department", "Total", "Average", "Grade", "Status"]])

    # Step 4 - analysis
    s = class_summary(df)
    banner("3. CLASS SUMMARY")
    print(f"Highest average  : {s['highest']}  ({s['topper']})")
    print(f"Lowest average   : {s['lowest']}  ({s['lowest_student']})")
    print(f"Class average   : {s['class_average']}   | Median: {s['median']}  | Std Dev: {s['std_dev']}")
    print(f"Passed / Failed  : {s['passed']} / {s['failed']}  ({s['pass_percentage']}% pass)")
    print(f"Avg attendance   : {s['avg_attendance']}%")
    print(f"Attendance vs marks correlation: {attendance_correlation(df)}")

    subj = subject_analysis(df)
    banner("4. SUBJECT-WISE ANALYSIS")
    show(subj)
    print(f"\nBest subject  : {subj.iloc[0]['Subject']} ({subj.iloc[0]['Average']})")
    print(f"Weakest subject: {subj.iloc[-1]['Subject']} ({subj.iloc[-1]['Average']})")

    banner("5. DEPARTMENT ANALYSIS")
    show(department_analysis(df))

    banner("6. GRADE DISTRIBUTION")
    for grade, count in grade_distribution(df).items():   # loop for text bar chart
        print(f"{grade:>2} | {'█' * count} {count}")

    banner("7. TOP 5 PERFORMERS")
    show(top_performers(df, 5))

    banner("8. AT-RISK STUDENTS (need attention)")
    show(at_risk_students(df))

    # Save report
    os.makedirs("output", exist_ok=True)
    df.to_csv("output/student_report.csv", index=False)
    print("\n✔ Full report saved to output/student_report.csv")


if __name__ == "__main__":
    main()