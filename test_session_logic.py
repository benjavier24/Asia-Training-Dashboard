"""Regression tests for session-deduplication logic.

These tests validate that Training Volume charts use the same
session definition as the headline "Trainings Done" KPI.
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
    print("✓ Test A passed: 20 trainee rows → 1 session")


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
    print("✓ Test B passed: 3 sessions × 5 trainees → 3 in trend")


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
    print("✓ Test C passed: Training ID prioritized, 2 unique IDs → 2 sessions")


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
    print("✓ Test D passed: Composite key (Date+Name+Trainer) → 2 sessions")


# === TEST E: Market Split ===
def test_e_market_split():
    """Sessions across two markets should be counted correctly.
    
    Note: The headline KPI counts globally unique (Date, Training Name, Trainer) combos.
    If the same trainer does the same training on the same date in two countries, 
    the KPI counts it as 1 session. Per-market charts include Country in the dedup key
    so they can show it separately per market.
    """
    rows = []
    # 2 sessions in PH (different dates/trainings)
    for i in range(5):
        rows.append({"Date": "2026-03-01", "Training Name": "X", "Trainer": "A", "Country": "PH", "Trainee Code": f"P{i}", "Pass Flag": 1})
    for i in range(5):
        rows.append({"Date": "2026-03-02", "Training Name": "Y", "Trainer": "B", "Country": "PH", "Trainee Code": f"Q{i}", "Pass Flag": 1})
    # 1 session in MY (different training name to ensure it's unique globally)
    for i in range(5):
        rows.append({"Date": "2026-03-01", "Training Name": "Z", "Trainer": "C", "Country": "MY", "Trainee Code": f"M{i}", "Pass Flag": 1})

    df = make_df(rows)
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)

    # Overall: 3 globally unique sessions
    sessions_df = get_unique_sessions(df, metrics)
    assert kpis["Total Sessions"] == 3, f"Expected 3 total sessions, got {kpis['Total Sessions']}"
    assert len(sessions_df) == 3, f"Expected 3 session rows, got {len(sessions_df)}"

    # Per-market dedup (same logic as the chart uses — includes Country)
    session_cols = ["Country", "Date", "Training Name", "Trainer"]
    df_mkt_sessions = df.drop_duplicates(subset=session_cols)
    ph_sessions = df_mkt_sessions[df_mkt_sessions["Country"] == "PH"]
    my_sessions = df_mkt_sessions[df_mkt_sessions["Country"] == "MY"]

    assert len(ph_sessions) == 2, f"Expected 2 PH sessions, got {len(ph_sessions)}"
    assert len(my_sessions) == 1, f"Expected 1 MY session, got {len(my_sessions)}"
    assert len(ph_sessions) + len(my_sessions) == kpis["Total Sessions"]
    print("✓ Test E passed: 2 PH + 1 MY = 3 total, reconciles with headline")


if __name__ == "__main__":
    test_a_repeated_trainee_rows()
    test_b_multiple_sessions_same_week()
    test_c_training_id()
    test_d_composite_fallback()
    test_e_market_split()
    print("\n✓ All regression tests passed!")
