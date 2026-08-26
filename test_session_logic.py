"""Regression tests for session-deduplication and metric semantics.

These tests validate that:
- Training Volume charts use the same session definition as the headline KPI
- Unique Learners Passed counts distinct people, not rows
- Labels adapt based on data availability
- Training Type uses session deduplication
"""
import pandas as pd
import numpy as np
import sys
sys.path.insert(0, ".")

# Import the functions under test
from app import get_unique_sessions, compute_kpis, detect_metrics


def make_df(rows):
    """Helper to create a DataFrame from a list of dicts."""
    df = pd.DataFrame(rows)
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
    if "Pass Flag" in df.columns:
        df["Pass Flag"] = pd.to_numeric(df["Pass Flag"], errors="coerce")
    if "Assessment Score" in df.columns:
        df["Assessment Score"] = pd.to_numeric(df["Assessment Score"], errors="coerce")
    return df


# === TEST A: Repeated Trainee Rows ===
def test_a_repeated_trainee_rows():
    """1 session with 20 trainees should count as 1 session, not 20."""
    rows = [
        {"Date": "2026-03-01", "Training Name": "Gadget Xchange", "Trainer": "Benj", "Trainee Code": f"EMP{i:04d}", "Pass Flag": 1}
        for i in range(20)
    ]
    df = make_df(rows)
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)

    sessions_df = get_unique_sessions(df, metrics)
    weekly = sessions_df.set_index("Date").resample("W").size()

    assert kpis["Total Sessions"] == 1, f"Expected 1 session, got {kpis['Total Sessions']}"
    assert weekly.sum() == 1, f"Expected 1 session in trend, got {weekly.sum()}"
    print("PASS Test A: 20 trainee rows = 1 session")


# === TEST B: Multiple Sessions Same Week ===
def test_b_multiple_sessions_same_week():
    """3 unique sessions with multiple trainees each should count as 3."""
    rows = []
    sessions = [
        ("2026-03-01", "Gadget Xchange", "Benj"),
        ("2026-03-02", "Device Protection", "Benj"),
        ("2026-03-03", "Gadget Xchange", "Andrea"),
    ]
    for date, name, trainer in sessions:
        for i in range(5):
            rows.append({"Date": date, "Training Name": name, "Trainer": trainer, "Trainee Code": f"EMP{i:04d}", "Pass Flag": 1})

    df = make_df(rows)
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)

    sessions_df = get_unique_sessions(df, metrics)
    weekly = sessions_df.set_index("Date").resample("W").size()

    assert kpis["Total Sessions"] == 3, f"Expected 3 sessions, got {kpis['Total Sessions']}"
    assert weekly.sum() == 3, f"Expected 3 sessions in trend, got {weekly.sum()}"
    print("PASS Test B: 3 sessions x 5 trainees = 3 in trend")


# === TEST C: Training ID Available ===
def test_c_training_id():
    """When Training ID exists, should use nunique on that field."""
    rows = [
        {"Date": "2026-03-01", "Training Name": "X", "Trainer": "A", "Training ID": "S001", "Trainee Code": f"E{i}", "Pass Flag": 1}
        for i in range(10)
    ] + [
        {"Date": "2026-03-01", "Training Name": "X", "Trainer": "A", "Training ID": "S002", "Trainee Code": f"F{i}", "Pass Flag": 1}
        for i in range(10)
    ]
    df = make_df(rows)
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)

    sessions_df = get_unique_sessions(df, metrics)

    assert kpis["Total Sessions"] == 2, f"Expected 2 sessions (by Training ID), got {kpis['Total Sessions']}"
    assert len(sessions_df) == 2, f"Expected 2 rows in sessions_df, got {len(sessions_df)}"
    print("PASS Test C: Training ID prioritized, 2 unique IDs = 2 sessions")


# === TEST D: Composite Fallback ===
def test_d_composite_fallback():
    """Without Training ID, uses Date+Name+Trainer composite."""
    rows = [
        {"Date": "2026-03-01", "Training Name": "X", "Trainer": "A", "Trainee Code": f"E{i}", "Pass Flag": 1}
        for i in range(8)
    ] + [
        {"Date": "2026-03-01", "Training Name": "Y", "Trainer": "A", "Trainee Code": f"F{i}", "Pass Flag": 1}
        for i in range(8)
    ]
    df = make_df(rows)
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)

    sessions_df = get_unique_sessions(df, metrics)

    assert kpis["Total Sessions"] == 2, f"Expected 2 sessions, got {kpis['Total Sessions']}"
    assert len(sessions_df) == 2, f"Expected 2 rows in sessions_df, got {len(sessions_df)}"
    print("PASS Test D: Composite key (Date+Name+Trainer) = 2 sessions")


# === TEST E: Country-Aware Session Key ===
def test_e_country_aware():
    """Same Date+Name+Trainer in two countries = 2 sessions (Country-aware)."""
    rows = []
    for i in range(5):
        rows.append({"Date": "2026-03-01", "Training Name": "X", "Trainer": "A", "Country": "PH", "Trainee Code": f"P{i}", "Pass Flag": 1})
    for i in range(5):
        rows.append({"Date": "2026-03-01", "Training Name": "X", "Trainer": "A", "Country": "MY", "Trainee Code": f"M{i}", "Pass Flag": 1})

    df = make_df(rows)
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)

    sessions_df = get_unique_sessions(df, metrics)

    # Country-aware: same session key in 2 countries = 2 distinct sessions
    assert kpis["Total Sessions"] == 2, f"Expected 2 sessions (Country-aware), got {kpis['Total Sessions']}"
    assert len(sessions_df) == 2, f"Expected 2 session rows, got {len(sessions_df)}"
    print("PASS Test E: Country-aware key, PH + MY = 2 sessions")


# === TEST F: Unique Learners Passed ===
def test_f_unique_learners_passed():
    """One learner with 3 passing records should count as 1 unique learner passed."""
    rows = [
        {"Date": "2026-03-01", "Training Name": "X", "Trainer": "A", "Trainee Code": "EMP001", "Pass Flag": 1},
        {"Date": "2026-03-02", "Training Name": "Y", "Trainer": "A", "Trainee Code": "EMP001", "Pass Flag": 1},
        {"Date": "2026-03-03", "Training Name": "Z", "Trainer": "A", "Trainee Code": "EMP001", "Pass Flag": 1},
        {"Date": "2026-03-01", "Training Name": "X", "Trainer": "A", "Trainee Code": "EMP002", "Pass Flag": 0},
    ]
    df = make_df(rows)
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)

    assert kpis["Unique Learners Passed"] == 1, f"Expected 1 unique learner passed, got {kpis['Unique Learners Passed']}"
    assert kpis["Total Passed"] == 3, f"Expected 3 total passed rows, got {kpis['Total Passed']}"
    print("PASS Test F: 1 learner x 3 passes = 1 unique learner passed")


# === TEST G: No Trainee ID Fallback ===
def test_g_no_trainee_fallback():
    """Without Trainee Code/Name, _has_unique_learner should be False."""
    rows = [
        {"Date": "2026-03-01", "Training Name": "X", "Trainer": "A", "Pass Flag": 1},
        {"Date": "2026-03-02", "Training Name": "Y", "Trainer": "A", "Pass Flag": 1},
    ]
    df = make_df(rows)
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)

    assert kpis["_has_unique_learner"] == False, "Expected no unique learner identification"
    assert "Unique Learners Passed" not in kpis, "Should not have Unique Learners Passed without trainee data"
    assert kpis["Total Participants"] == 2, f"Expected 2 total participants (rows), got {kpis['Total Participants']}"
    print("PASS Test G: No trainee data = _has_unique_learner False, no unique passed count")


# === TEST H: Training Type Sessions ===
def test_h_training_type_sessions():
    """Training Type breakdown should count unique sessions, not rows."""
    rows = []
    # 1 Virtual session with 50 attendees
    for i in range(50):
        rows.append({"Date": "2026-03-01", "Training Name": "X", "Trainer": "A", "Training Type": "Virtual/Online", "Trainee Code": f"E{i}", "Pass Flag": 1})
    # 1 Face to Face session with 10 attendees
    for i in range(10):
        rows.append({"Date": "2026-03-02", "Training Name": "Y", "Trainer": "B", "Training Type": "Face to Face", "Trainee Code": f"F{i}", "Pass Flag": 1})

    df = make_df(rows)
    metrics = detect_metrics(df)

    df_sessions = get_unique_sessions(df, metrics)
    type_counts = df_sessions["Training Type"].value_counts()

    assert type_counts.get("Virtual/Online", 0) == 1, f"Expected 1 Virtual session, got {type_counts.get('Virtual/Online', 0)}"
    assert type_counts.get("Face to Face", 0) == 1, f"Expected 1 F2F session, got {type_counts.get('Face to Face', 0)}"
    print("PASS Test H: Training Type counts unique sessions (1 Virtual, 1 F2F)")


if __name__ == "__main__":
    test_a_repeated_trainee_rows()
    test_b_multiple_sessions_same_week()
    test_c_training_id()
    test_d_composite_fallback()
    test_e_country_aware()
    test_f_unique_learners_passed()
    test_g_no_trainee_fallback()
    test_h_training_type_sessions()
    print("\nAll regression tests passed!")
