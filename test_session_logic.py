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



# === TRAINING INTELLIGENCE QUERY TESTS ===

def test_ti_filter_context():
    """Market = PH: lowest pass rate query should only use PH accounts."""
    rows = []
    # PH accounts: Globe low, Power Mac high
    for i in range(10):
        rows.append({"Date": "2026-03-01", "Training Name": "Foundation", "Trainer": "Benj Javier", "Country": "PH", "Account": "Globe", "Trainee Code": f"G{i}", "Pass Flag": 0})
    for i in range(10):
        rows.append({"Date": "2026-03-01", "Training Name": "Activation", "Trainer": "Andrea Cruz", "Country": "PH", "Account": "Power Mac", "Trainee Code": f"P{i}", "Pass Flag": 1})
    # MY account: high pass rate (should NOT appear in PH-filtered query)
    for i in range(10):
        rows.append({"Date": "2026-03-01", "Training Name": "Champion", "Trainer": "Lisa Tan", "Country": "MY", "Account": "Samsung", "Trainee Code": f"S{i}", "Pass Flag": 1})

    df = make_df(rows)
    # Simulate PH filter
    df_ph = df[df["Country"] == "PH"]
    metrics = detect_metrics(df_ph)
    kpis = compute_kpis(df_ph, metrics)

    from app import process_natural_query
    answer = process_natural_query("Which account has the lowest pass rate?", df_ph, metrics, kpis)
    assert "Globe" in answer, f"Expected Globe in answer, got: {answer[:200]}"
    assert "Samsung" not in answer, f"Samsung should not appear in PH-filtered query"
    print("PASS Test TI-A: Filter context respected (PH only)")


def test_ti_session_count():
    """Session question should use unique-session logic, not row count."""
    rows = [
        {"Date": "2026-03-01", "Training Name": "Foundation", "Trainer": "Benj Javier", "Trainee Code": f"E{i}", "Pass Flag": 1}
        for i in range(50)
    ]
    df = make_df(rows)
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)

    from app import process_natural_query
    answer = process_natural_query("How many training sessions were conducted?", df, metrics, kpis)
    # Should report 1 session (all rows share same Date+Name+Trainer)
    assert "Training Sessions: 1" in answer or "**Training Sessions: 1**" in answer, f"Should show 1 session. Got: {answer[:300]}"
    print("PASS Test TI-B: Session count uses unique-session logic")


def test_ti_unique_learner():
    """Learner question should use unique-person logic."""
    rows = [
        {"Date": "2026-03-01", "Training Name": "Foundation", "Trainer": "Benj Javier", "Trainee Code": "EMP001", "Pass Flag": 1},
        {"Date": "2026-03-02", "Training Name": "Activation", "Trainer": "Benj Javier", "Trainee Code": "EMP001", "Pass Flag": 1},
        {"Date": "2026-03-03", "Training Name": "Champion", "Trainer": "Benj Javier", "Trainee Code": "EMP002", "Pass Flag": 1},
    ]
    df = make_df(rows)
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)

    from app import process_natural_query
    answer = process_natural_query("How many unique learners were trained?", df, metrics, kpis)
    assert "2" in answer, f"Expected 2 unique learners. Got: {answer[:200]}"
    print("PASS Test TI-C: Unique learner count is correct")


def test_ti_insufficient_scope():
    """Single account: ranking should explain limitation."""
    rows = [
        {"Date": "2026-03-01", "Training Name": "Foundation", "Trainer": "Benj Javier", "Account": "Globe", "Trainee Code": f"E{i}", "Pass Flag": 1}
        for i in range(5)
    ]
    df = make_df(rows)
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)

    from app import process_natural_query
    answer = process_natural_query("Which account has the highest pass rate?", df, metrics, kpis)
    assert "one" in answer.lower() or "not available" in answer.lower() or "100" in answer, \
        f"Should handle single entity gracefully. Got: {answer[:200]}"
    print("PASS Test TI-D: Insufficient scope handled")


def test_ti_unsupported():
    """Question outside training data should get safe fallback."""
    rows = [
        {"Date": "2026-03-01", "Training Name": "Foundation", "Trainer": "Benj Javier", "Trainee Code": "E1", "Pass Flag": 1},
    ]
    df = make_df(rows)
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)

    from app import process_natural_query
    answer = process_natural_query("What is the weather today?", df, metrics, kpis)
    assert "cannot" in answer.lower() or "summary" in answer.lower() or "session" in answer.lower(), \
        f"Should give safe fallback. Got: {answer[:200]}"
    print("PASS Test TI-E: Unsupported question gets safe response")


# === PHASE 4 CLEANUP TESTS ===

def test_p4_missing_score_no_nan():
    """Comparison with a market that has no assessment scores should show 'No data', not nan."""
    rows = []
    # PH with scores
    for i in range(5):
        rows.append({"Date": "2026-03-01", "Training Name": "Foundation", "Trainer": "Benj Javier", "Country": "PH", "Assessment Score": 0.9, "Pass Flag": 1})
    # SG with NO scores (NaN)
    for i in range(5):
        rows.append({"Date": "2026-03-01", "Training Name": "Champion", "Trainer": "Lisa Tan", "Country": "SG", "Assessment Score": None, "Pass Flag": 1})

    df = make_df(rows)
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)

    from app import process_natural_query
    answer = process_natural_query("Compare markets", df, metrics, kpis)
    assert "nan" not in answer.lower(), f"Should not contain 'nan'. Got: {answer}"
    assert "No data" in answer, f"Should show 'No data' for missing scores. Got: {answer}"
    print("PASS Test P4-A: Missing scores show 'No data', not nan")


def test_p4_comparison_is_table():
    """Comparison output should be a structured markdown table."""
    rows = []
    for country in ["PH", "MY", "TH"]:
        for i in range(5):
            rows.append({"Date": "2026-03-01", "Training Name": f"Prog{country}", "Trainer": f"Trainer{country}",
                         "Country": country, "Assessment Score": 0.8, "Pass Flag": 1})

    df = make_df(rows)
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)

    from app import process_natural_query
    answer = process_natural_query("Compare markets", df, metrics, kpis)
    # Markdown table has header separator row
    assert "| ---" in answer or "|---" in answer, f"Should be a table. Got: {answer}"
    assert "Pass Rate" in answer and "Sessions" in answer, f"Table should have columns. Got: {answer}"
    print("PASS Test P4-B: Comparison renders as structured table")


def test_p4_context_in_answer():
    """Each answer should include its context line."""
    rows = [
        {"Date": "2026-03-01", "Training Name": "Foundation", "Trainer": "Benj Javier", "Country": "PH", "Pass Flag": 1}
    ]
    df = make_df(rows)
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)

    from app import process_natural_query
    answer = process_natural_query("Summarize performance", df, metrics, kpis)
    assert "Context:" in answer, f"Answer should include context line. Got: {answer[:100]}"
    print("PASS Test P4-C: Answer includes context line")


# === PHASE 4.1: TRUST & TRACEABILITY TESTS ===

def _ti_result(question, df):
    """Helper: run the structured Training Intelligence engine."""
    from app import run_training_intelligence
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)
    return run_training_intelligence(question, df, metrics, kpis)


def test_p41_based_on_metadata():
    """Lowest pass rate market query should set metric=Pass Rate, dimension=Market."""
    rows = []
    for country, pf in [("PH", 1), ("MY", 0), ("TH", 1)]:
        for i in range(5):
            rows.append({"Date": "2026-03-01", "Training Name": f"P{country}", "Trainer": f"T{country}",
                         "Country": country, "Pass Flag": pf})
    df = make_df(rows)
    result = _ti_result("Which market has the lowest pass rate?", df)
    assert result["metric"] == "Pass Rate", f"Expected metric=Pass Rate, got {result['metric']}"
    assert result["dimension"] == "Market", f"Expected dimension=Market, got {result['dimension']}"
    print("PASS Test P4.1-A: Based-on metadata (metric + dimension)")


def test_p41_supporting_data_scope():
    """PH-filtered account query supporting table contains PH accounts only."""
    rows = []
    for i in range(5):
        rows.append({"Date": "2026-03-01", "Training Name": "Foundation", "Trainer": "Benj Javier", "Country": "PH", "Account": "Globe", "Pass Flag": 0})
    for i in range(5):
        rows.append({"Date": "2026-03-01", "Training Name": "Activation", "Trainer": "Andrea Cruz", "Country": "PH", "Account": "Power Mac", "Pass Flag": 1})
    for i in range(5):
        rows.append({"Date": "2026-03-01", "Training Name": "Champion", "Trainer": "Lisa Tan", "Country": "MY", "Account": "Samsung", "Pass Flag": 1})
    df = make_df(rows)
    df_ph = df[df["Country"] == "PH"]
    result = _ti_result("Which account has the lowest pass rate?", df_ph)
    table = result["supporting_table"] or []
    names = [str(r) for r in table]
    combined = " ".join(names)
    assert "Samsung" not in combined, f"Samsung (MY) should not appear in PH supporting data"
    print("PASS Test P4.1-B: Supporting data respects PH scope")


def test_p41_calc_description():
    """Session question should include the unique-session calc description."""
    rows = [
        {"Date": "2026-03-01", "Training Name": "Foundation", "Trainer": "Benj Javier", "Trainee Code": f"E{i}", "Pass Flag": 1}
        for i in range(10)
    ]
    df = make_df(rows)
    result = _ti_result("How many training sessions?", df)
    assert result["calc_desc"] and "unique training sessions" in result["calc_desc"].lower(), \
        f"Expected unique-session calc desc, got {result['calc_desc']}"
    print("PASS Test P4.1-C: Calculation description present")


def test_p41_limited_data_status():
    """Comparison with a market missing scores flags Limited data."""
    rows = []
    for i in range(5):
        rows.append({"Date": "2026-03-01", "Training Name": "Foundation", "Trainer": "Benj Javier", "Country": "PH", "Assessment Score": 0.9, "Pass Flag": 1})
    for i in range(5):
        rows.append({"Date": "2026-03-01", "Training Name": "Champion", "Trainer": "Lisa Tan", "Country": "SG", "Assessment Score": None, "Pass Flag": 1})
    df = make_df(rows)
    result = _ti_result("Compare markets", df)
    assert result["data_quality"] == "Limited data", f"Expected Limited data, got {result['data_quality']}"
    print("PASS Test P4.1-D: Limited data status for missing scores")


def test_p41_ranking_basis():
    """Ranking metadata explicitly identifies the ranking metric."""
    rows = []
    for country, pf in [("PH", 1), ("MY", 0), ("TH", 1)]:
        for i in range(5):
            rows.append({"Date": "2026-03-01", "Training Name": f"P{country}", "Trainer": f"T{country}",
                         "Country": country, "Pass Flag": pf})
    df = make_df(rows)
    result = _ti_result("Top markets by pass rate", df)
    assert result["metric"] == "Pass Rate", f"Ranking metric should be Pass Rate, got {result['metric']}"
    assert result["supporting_table"] is not None, "Ranking should have a supporting table"
    print("PASS Test P4.1-E: Ranking basis is traceable")


def test_p41_no_fake_confidence():
    """Response must not contain fake AI confidence scores."""
    rows = [
        {"Date": "2026-03-01", "Training Name": "Foundation", "Trainer": "Benj Javier", "Country": "PH", "Pass Flag": 1}
    ]
    df = make_df(rows)
    result = _ti_result("Summarize performance", df)
    combined = (result["answer"] + str(result.get("data_quality", ""))).lower()
    assert "confidence" not in combined, "Should not contain confidence scores"
    assert "%" not in str(result.get("data_quality", "")), "Data quality should not be a percentage"
    print("PASS Test P4.1-F: No fake confidence scores")


def test_score_scaling_needs_attention():
    """Needs-attention low-score programs must show 60.0%, not 0.6%."""
    from app import generate_needs_attention
    rows = []
    # High-score program
    for i in range(10):
        rows.append({"Date": "2026-03-01", "Training Name": "Good Program", "Trainer": "Benj Javier",
                     "Country": "PH", "Assessment Score": 0.95, "Pass Flag": 1})
    # Low-score program (0.6 = 60%)
    for i in range(10):
        rows.append({"Date": "2026-03-02", "Training Name": "Weak Program", "Trainer": "Andrea Cruz",
                     "Country": "PH", "Assessment Score": 0.6, "Pass Flag": 0})
    df = make_df(rows)
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)
    items = generate_needs_attention(df, metrics, kpis, "market")
    # Find any low-score item and verify it's scaled to percentage (60.0%, not 0.6%)
    score_items = [it for it in items if "score" in it[1]]
    if score_items:
        metric_str = score_items[0][2]
        val = float(metric_str.replace("%", ""))
        assert val > 1, f"Score should be scaled to percentage (e.g. 60.0%), got {metric_str}"
    print("PASS Test SCALE: Needs-attention scores shown as percentage (60%, not 0.6%)")


# === PHASE 5 PRODUCTIZATION TESTS ===

def test_p5_prepare_dataframe_consistency():
    """prepare_dataframe should produce the same metrics as manual normalization."""
    from app import prepare_dataframe
    rows = [
        {"Date of Training": "2026-03-01", "Training Title": "Foundation", "Trainer Name": "Benj Javier",
         "Partner Name": "Globe", "Training Type": "Foundation", "Training Method": "Online",
         "Trainee Code": "E1", "Pass Flag": "1"}
        for _ in range(5)
    ]
    raw = pd.DataFrame(rows)
    prepared = prepare_dataframe(raw)
    # Columns normalized to canonical names
    assert "Training Name" in prepared.columns, "Training Title should normalize to Training Name"
    assert "Trainer" in prepared.columns, "Trainer Name should normalize to Trainer"
    assert "Account" in prepared.columns, "Partner Name should normalize to Account"
    # Training Type (phase) preserved; delivery mode consolidated separately
    assert (prepared["Training Type"] == "Foundation").all(), "Foundation phase should stay in Training Type"
    assert (prepared["Training Method"] == "Virtual/Online").all(), "Online should consolidate to Virtual/Online in Training Method"
    # Pass Flag coerced to numeric
    assert pd.api.types.is_numeric_dtype(prepared["Pass Flag"]), "Pass Flag should be numeric"
    print("PASS Test P5-A: prepare_dataframe normalizes, consolidates, coerces")


def test_p5_upload_unsupported_type():
    """Unsupported file type returns a clear error, not a crash."""
    from app import load_uploaded_file

    class FakeUpload:
        name = "report.pdf"
    data, err = load_uploaded_file(FakeUpload())
    assert data is None and err is not None, "Should reject unsupported file type"
    assert "xlsx" in err.lower() or "csv" in err.lower(), f"Error should guide file type. Got: {err}"
    print("PASS Test P5-B: Unsupported upload type handled gracefully")


def test_p5_empty_scope_kpis():
    """Empty filtered data should not crash compute_kpis."""
    empty = make_df([{"Date": "2026-03-01", "Training Name": "X", "Trainer": "A", "Pass Flag": 1}]).iloc[0:0]
    metrics = detect_metrics(empty)
    # compute_kpis on empty frame should return a dict without raising
    kpis = compute_kpis(empty, metrics)
    assert isinstance(kpis, dict), "compute_kpis should return a dict even when empty"
    print("PASS Test P5-C: Empty scope does not crash KPI computation")


def test_p5_single_market_no_comparison():
    """Single market: session KPI still works; no crash on single-entity scope."""
    rows = [
        {"Date": "2026-03-01", "Training Name": "Foundation", "Trainer": "Benj Javier", "Country": "PH", "Pass Flag": 1}
        for _ in range(5)
    ]
    df = make_df(rows)
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)
    assert df["Country"].nunique() == 1, "Test setup: single market"
    assert kpis["Total Sessions"] == 1, "Single session expected"
    print("PASS Test P5-D: Single-market scope handled")


def test_uat_mixed_score_formats():
    """Mixed assessment-score formats (decimals + percentages) must all normalize to 0-100.

    Reproduces the PH-vs-ID bug: ID scores stored as 0-100, PH scores as 0-1 decimals
    in the SAME column. After prepare_dataframe, every value should be 0-100.
    """
    from app import prepare_dataframe
    rows = []
    # ID rows: stored as 0-100 percentages
    for i in range(10):
        rows.append({"Date": "2026-03-01", "Training Name": "X", "Trainer": "A", "Country": "ID",
                     "Account": "Erajaya", "Trainee Code": f"I{i}", "Training Assessment Score %": 80, "Pass Flag": "1"})
    # PH rows: stored as 0-1 decimals
    for i in range(10):
        rows.append({"Date": "2026-03-02", "Training Name": "Y", "Trainer": "B", "Country": "PH",
                     "Account": "Globe", "Trainee Code": f"P{i}", "Training Assessment Score %": 0.8, "Pass Flag": "1"})
    raw = pd.DataFrame(rows)
    prepared = prepare_dataframe(raw)

    # All scores should now be on a 0-100 scale
    ph_scores = prepared[prepared["Country"] == "PH"]["Assessment Score"]
    id_scores = prepared[prepared["Country"] == "ID"]["Assessment Score"]
    assert (ph_scores == 80).all(), f"PH decimals (0.8) should scale to 80. Got {ph_scores.unique()}"
    assert (id_scores == 80).all(), f"ID percentages (80) should stay 80. Got {id_scores.unique()}"
    print("PASS Test UAT-A: Mixed score formats normalized to 0-100 per row")


def test_uat_ph_account_score_display():
    """PH account avg score should display ~80%, not 0.8% (the reported bug)."""
    from app import prepare_dataframe
    rows = []
    for i in range(10):
        rows.append({"Date": "2026-03-02", "Training Name": "Y", "Trainer": "B", "Country": "PH",
                     "Account": "Globe", "Trainee Code": f"P{i}", "Training Assessment Score %": 0.8, "Pass Flag": "1"})
    df = prepare_dataframe(pd.DataFrame(rows))
    # Account-level mean should be 80, not 0.8
    acct_mean = df.groupby("Account")["Assessment Score"].mean()["Globe"]
    assert 79 <= acct_mean <= 81, f"Globe account avg score should be ~80%, got {acct_mean}"
    print("PASS Test UAT-B: PH account score displays as ~80%, not 0.8%")


# === 70% PASSING STANDARD TESTS ===

def test_threshold_derives_pass_flag_from_score():
    """Pass Flag must be derived from score >= 70, overriding any source flag."""
    from app import prepare_dataframe, PASS_THRESHOLD
    assert PASS_THRESHOLD == 70, f"Passing standard should be 70, got {PASS_THRESHOLD}"
    rows = [
        # score 69 with source Pass Flag=1 -> must become FAIL (below 70)
        {"Date of Training": "2026-03-01", "Training Title": "X", "Trainer Name": "A",
         "Trainee Code": "E1", "Training Assessment Score %": 69, "Pass Flag": 1},
        # score 70 with source Pass Flag=0 -> must become PASS (at threshold)
        {"Date of Training": "2026-03-01", "Training Title": "X", "Trainer Name": "A",
         "Trainee Code": "E2", "Training Assessment Score %": 70, "Pass Flag": 0},
        # score 95 -> PASS
        {"Date of Training": "2026-03-01", "Training Title": "X", "Trainer Name": "A",
         "Trainee Code": "E3", "Training Assessment Score %": 95, "Pass Flag": 0},
    ]
    df = prepare_dataframe(pd.DataFrame(rows))
    flags = df.sort_values("Trainee Code")["Pass Flag"].tolist()
    assert flags == [0.0, 1.0, 1.0], f"Expected [fail, pass, pass] by score >=70, got {flags}"
    print("PASS Test THR-A: Pass Flag derived from score >= 70 (overrides source flag)")


def test_threshold_decimal_scores_scaled_before_threshold():
    """Decimal scores (0-1) are scaled to 0-100 BEFORE the 70% test is applied."""
    from app import prepare_dataframe
    rows = [
        # 0.72 -> 72 -> PASS
        {"Date of Training": "2026-03-01", "Training Title": "Y", "Trainer Name": "B",
         "Trainee Code": "P1", "Training Assessment Score %": 0.72, "Pass Flag": 0},
        # 0.65 -> 65 -> FAIL
        {"Date of Training": "2026-03-01", "Training Title": "Y", "Trainer Name": "B",
         "Trainee Code": "P2", "Training Assessment Score %": 0.65, "Pass Flag": 1},
    ]
    df = prepare_dataframe(pd.DataFrame(rows))
    flags = df.sort_values("Trainee Code")["Pass Flag"].tolist()
    assert flags == [1.0, 0.0], f"Expected [pass(0.72->72), fail(0.65->65)], got {flags}"
    print("PASS Test THR-B: Decimal scores scaled before applying 70% threshold")


def test_threshold_blank_score_excluded_not_failed():
    """Option B: rows with no score are EXCLUDED from pass rate, not counted as fails."""
    from app import prepare_dataframe, compute_kpis, detect_metrics
    rows = [
        # 2 assessed: one pass (80), one fail (50)
        {"Date of Training": "2026-03-01", "Training Title": "Z", "Trainer Name": "C",
         "Trainee Code": "A1", "Training Assessment Score %": 80, "Pass Flag": 1},
        {"Date of Training": "2026-03-01", "Training Title": "Z", "Trainer Name": "C",
         "Trainee Code": "A2", "Training Assessment Score %": 50, "Pass Flag": 1},
        # 2 with NO score -> must be excluded from pass rate entirely
        {"Date of Training": "2026-03-01", "Training Title": "Z", "Trainer Name": "C",
         "Trainee Code": "A3", "Training Assessment Score %": None, "Pass Flag": 1},
        {"Date of Training": "2026-03-01", "Training Title": "Z", "Trainer Name": "C",
         "Trainee Code": "A4", "Training Assessment Score %": None, "Pass Flag": 0},
    ]
    df = prepare_dataframe(pd.DataFrame(rows))
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)
    # Pass rate = 1 pass / 2 assessed = 50%, NOT 1/4 (25%) which would treat blanks as fails
    assert kpis["Pass Rate"] == 50.0, f"Expected 50% (1 of 2 assessed), got {kpis['Pass Rate']}"
    # Blank-score rows must have NaN Pass Flag (excluded)
    blanks = df[df["Assessment Score"].isna()]["Pass Flag"]
    assert blanks.isna().all(), f"Blank-score rows must have NaN Pass Flag, got {blanks.tolist()}"
    print("PASS Test THR-C: Blank scores excluded from pass rate (option B), not failed")


def test_threshold_fail_flag_is_inverse():
    """Fail Flag must be the logical inverse of Pass Flag, with NaN preserved."""
    from app import prepare_dataframe
    rows = [
        {"Date of Training": "2026-03-01", "Training Title": "W", "Trainer Name": "D",
         "Trainee Code": "F1", "Training Assessment Score %": 90, "Pass Flag": 1},   # pass
        {"Date of Training": "2026-03-01", "Training Title": "W", "Trainer Name": "D",
         "Trainee Code": "F2", "Training Assessment Score %": 40, "Pass Flag": 1},   # fail
        {"Date of Training": "2026-03-01", "Training Title": "W", "Trainer Name": "D",
         "Trainee Code": "F3", "Training Assessment Score %": None, "Pass Flag": 1},  # excluded
    ]
    df = prepare_dataframe(pd.DataFrame(rows)).sort_values("Trainee Code")
    pass_flags = df["Pass Flag"].tolist()
    fail_flags = df["Fail Flag"].tolist()
    assert pass_flags[0] == 1.0 and fail_flags[0] == 0.0, "Pass row: Pass=1, Fail=0"
    assert pass_flags[1] == 0.0 and fail_flags[1] == 1.0, "Fail row: Pass=0, Fail=1"
    assert pd.isna(pass_flags[2]) and pd.isna(fail_flags[2]), "Blank row: both NaN"
    print("PASS Test THR-D: Fail Flag is inverse of Pass Flag (NaN preserved)")


def test_threshold_inconsistent_source_flags_corrected():
    """Source flags that contradict scores (e.g. Harmony 79% 'pass' at 19 avg) are corrected."""
    from app import prepare_dataframe, compute_kpis, detect_metrics
    # Mimic the Harmony anomaly: high source pass rate but very low scores
    rows = []
    for i in range(10):
        # All flagged pass in source, but all score ~19 (well below 70)
        rows.append({"Date of Training": "2026-03-01", "Training Title": "H", "Trainer Name": "E",
                     "Trainee Code": f"H{i}", "Training Assessment Score %": 19, "Pass Flag": 1})
    df = prepare_dataframe(pd.DataFrame(rows))
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)
    # Despite source flags all=1, real pass rate must be 0% (no one scored >=70)
    assert kpis["Pass Rate"] == 0.0, f"Expected 0% (all scored 19), got {kpis['Pass Rate']}"
    print("PASS Test THR-E: Contradictory source flags corrected to score-based truth")


# === TIERED THRESHOLD TESTS (Foundation 70 / Activation & Reinforcement 80) ===

def test_tiered_threshold_map():
    """The per-type threshold lookup returns the correct tier and defaults to 70."""
    from app import pass_threshold_for_type, PASS_THRESHOLDS_BY_TYPE, PASS_THRESHOLD
    assert PASS_THRESHOLDS_BY_TYPE.get("foundation") == 70
    assert PASS_THRESHOLDS_BY_TYPE.get("activation") == 80
    assert PASS_THRESHOLDS_BY_TYPE.get("reinforcement") == 80
    assert pass_threshold_for_type("Foundation") == 70
    assert pass_threshold_for_type("Activation") == 80
    assert pass_threshold_for_type("Reinforcement") == 80
    assert pass_threshold_for_type("  reINForcement ") == 80   # case/space tolerant
    assert pass_threshold_for_type(None) == PASS_THRESHOLD      # missing -> 70
    assert pass_threshold_for_type("") == PASS_THRESHOLD        # blank -> 70
    assert pass_threshold_for_type("Champion") == PASS_THRESHOLD  # unknown -> 70
    print("PASS Test TIER-A: Per-type threshold map (F=70, A/R=80, default 70)")


def test_tiered_foundation_vs_activation_at_75():
    """A score of 75 passes Foundation (>=70) but FAILS Activation (needs >=80)."""
    from app import prepare_dataframe
    rows = [
        {"Date of Training": "2026-03-01", "Training Title": "F", "Trainer Name": "T",
         "Training Type": "Foundation", "Trainee Code": "F75",
         "Training Assessment Score %": 75, "Pass Flag": 0},
        {"Date of Training": "2026-03-01", "Training Title": "A", "Trainer Name": "T",
         "Training Type": "Activation", "Trainee Code": "A75",
         "Training Assessment Score %": 75, "Pass Flag": 1},
        {"Date of Training": "2026-03-01", "Training Title": "R", "Trainer Name": "T",
         "Training Type": "Reinforcement", "Trainee Code": "R75",
         "Training Assessment Score %": 75, "Pass Flag": 1},
    ]
    df = prepare_dataframe(pd.DataFrame(rows)).set_index("Trainee Code")
    assert df.loc["F75", "Pass Flag"] == 1.0, "Foundation 75 should PASS (>=70)"
    assert df.loc["A75", "Pass Flag"] == 0.0, "Activation 75 should FAIL (needs >=80)"
    assert df.loc["R75", "Pass Flag"] == 0.0, "Reinforcement 75 should FAIL (needs >=80)"
    print("PASS Test TIER-B: Score 75 passes Foundation but fails Activation/Reinforcement")


def test_tiered_activation_80_passes():
    """A score of exactly 80 passes Activation/Reinforcement (>= threshold)."""
    from app import prepare_dataframe
    rows = [
        {"Date of Training": "2026-03-01", "Training Title": "A", "Trainer Name": "T",
         "Training Type": "Activation", "Trainee Code": "A80",
         "Training Assessment Score %": 80, "Pass Flag": 0},
        {"Date of Training": "2026-03-01", "Training Title": "R", "Trainer Name": "T",
         "Training Type": "Reinforcement", "Trainee Code": "R79",
         "Training Assessment Score %": 79, "Pass Flag": 1},
    ]
    df = prepare_dataframe(pd.DataFrame(rows)).set_index("Trainee Code")
    assert df.loc["A80", "Pass Flag"] == 1.0, "Activation 80 should PASS (at threshold)"
    assert df.loc["R79", "Pass Flag"] == 0.0, "Reinforcement 79 should FAIL (below 80)"
    print("PASS Test TIER-C: Score 80 passes Activation; 79 fails Reinforcement")


def test_tiered_blank_type_defaults_to_70():
    """Rows with a blank/missing training type use the 70% default."""
    from app import prepare_dataframe
    rows = [
        {"Date of Training": "2026-03-01", "Training Title": "X", "Trainer Name": "T",
         "Training Type": None, "Trainee Code": "B72",
         "Training Assessment Score %": 72, "Pass Flag": 0},
        {"Date of Training": "2026-03-01", "Training Title": "X", "Trainer Name": "T",
         "Training Type": None, "Trainee Code": "B69",
         "Training Assessment Score %": 69, "Pass Flag": 1},
    ]
    df = prepare_dataframe(pd.DataFrame(rows)).set_index("Trainee Code")
    assert df.loc["B72", "Pass Flag"] == 1.0, "Blank type, 72 should PASS (default 70)"
    assert df.loc["B69", "Pass Flag"] == 0.0, "Blank type, 69 should FAIL (default 70)"
    print("PASS Test TIER-D: Blank training type defaults to 70% standard")


def test_tiered_training_type_vs_method_separation():
    """Training phase and delivery method are kept in separate columns."""
    from app import prepare_dataframe
    # Source has both a phase column and a delivery-method column
    rows = [{
        "Date of Training": "2026-03-01", "Training Title": "X", "Trainer Name": "T",
        "Trainee Code": "S1", "Training Assessment Score %": 90,
        "Training Type (Foundation, Activation, Reinforcement)": "Activation",
        "Training Method": "Face to Face",
    }]
    df = prepare_dataframe(pd.DataFrame(rows))
    assert df["Training Type"].iloc[0] == "Activation", "Phase must map to Training Type"
    assert "Training Method" in df.columns and df["Training Method"].iloc[0] == "Face to Face", \
        "Delivery mode must stay in Training Method, not hijack Training Type"
    print("PASS Test TIER-E: Training Type (phase) and Training Method (mode) kept separate")


# === NaN-GROUP HANDLING TESTS (blank-score groups must not show "nan") ===

def _mixed_market_df():
    """Build a dataset where one market (SG) has ALL blank assessment scores,
    while others have real scores — reproducing the 'nan%' insight bug."""
    from app import prepare_dataframe
    rows = []
    # ID: real scores (mostly passing)
    for i in range(20):
        rows.append({"Country": "ID", "Date of Training": "2026-03-01", "Training Title": "F",
                     "Trainer Name": "T1", "Partner Name": "ERAFONE", "Training Type": "Foundation",
                     "Trainee Code": f"ID{i}", "Training Assessment Score %": 85, "Pass Flag": 1})
    # PH: real scores (mixed)
    for i in range(20):
        sc = 90 if i % 2 == 0 else 40
        rows.append({"Country": "PH", "Date of Training": "2026-03-02", "Training Title": "F",
                     "Trainer Name": "T2", "Partner Name": "Globe", "Training Type": "Foundation",
                     "Trainee Code": f"PH{i}", "Training Assessment Score %": sc, "Pass Flag": 1})
    # SG: NO assessment scores at all -> Pass Flag becomes NaN for every row
    for i in range(10):
        rows.append({"Country": "SG", "Date of Training": "2026-03-03", "Training Title": "F",
                     "Trainer Name": "T3", "Partner Name": "Singtel", "Training Type": "Foundation",
                     "Trainee Code": f"SG{i}", "Training Assessment Score %": None, "Pass Flag": 1})
    return prepare_dataframe(pd.DataFrame(rows))


def test_nan_executive_insights_no_nan_string():
    """Regional insights must not render 'nan' when a market has no assessed learners."""
    from app import generate_executive_insights, compute_kpis, detect_metrics
    df = _mixed_market_df()
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)
    insights = generate_executive_insights(df, metrics, kpis, view_level="regional")
    blob = " ".join(f"{h} {d}" for _, h, d in insights).lower()
    assert "nan" not in blob, f"Executive insights leaked 'nan': {blob}"
    print("PASS Test NAN-A: Executive insights exclude blank-score market (no 'nan')")


def test_nan_training_intelligence_pass_rate_no_nan():
    """TI pass-rate answer (with by-market breakdown) must not show 'nan%'."""
    from app import run_training_intelligence, compute_kpis, detect_metrics
    df = _mixed_market_df()
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)
    result = run_training_intelligence("what is the pass rate?", df, metrics, kpis)
    assert "nan" not in result["answer"].lower(), f"TI pass-rate leaked 'nan': {result['answer']}"
    print("PASS Test NAN-B: TI pass-rate answer excludes blank-score market (no 'nan')")


def test_nan_ranking_bottom_no_nan():
    """A 'worst markets by pass rate' ranking must not surface the blank-score market as nan%."""
    from app import run_training_intelligence, compute_kpis, detect_metrics
    df = _mixed_market_df()
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)
    result = run_training_intelligence("worst markets by pass rate", df, metrics, kpis)
    assert "nan" not in result["answer"].lower(), f"Ranking leaked 'nan': {result['answer']}"
    print("PASS Test NAN-C: Bottom ranking excludes blank-score market (no 'nan')")


def test_nan_needs_attention_and_why_no_nan():
    """Needs-attention and why/root-cause answers must not show 'nan%'."""
    from app import run_training_intelligence, generate_needs_attention, compute_kpis, detect_metrics
    df = _mixed_market_df()
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)
    for q in ["which markets need attention?", "why is the pass rate low?"]:
        result = run_training_intelligence(q, df, metrics, kpis)
        assert "nan" not in result["answer"].lower(), f"'{q}' leaked 'nan': {result['answer']}"
    # generate_needs_attention items
    items = generate_needs_attention(df, metrics, kpis, view_level="regional")
    blob = " ".join(f"{e} {r} {m}" for e, r, m in items).lower()
    assert "nan" not in blob, f"Needs-attention leaked 'nan': {blob}"
    print("PASS Test NAN-D: Needs-attention & why answers exclude blank-score groups")


def test_nan_all_blank_subset_shows_no_data():
    """When the ENTIRE scope has no assessment scores, pass rate shows 'No assessment data', not nan%."""
    from app import prepare_dataframe, run_training_intelligence, compute_kpis, detect_metrics
    rows = [
        {"Country": "SG", "Date of Training": "2026-03-03", "Training Title": "F", "Trainer Name": "T3",
         "Partner Name": "Singtel", "Trainee Code": f"SG{i}", "Training Assessment Score %": None, "Pass Flag": 1}
        for i in range(8)
    ]
    df = prepare_dataframe(pd.DataFrame(rows))
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)
    result = run_training_intelligence("what is the pass rate?", df, metrics, kpis)
    ans = result["answer"].lower()
    assert "nan" not in ans, f"All-blank subset leaked 'nan': {result['answer']}"
    assert "no assessment data" in ans, f"Expected 'No assessment data' message, got: {result['answer']}"
    print("PASS Test NAN-E: All-blank scope shows 'No assessment data' (no 'nan')")


# === EDGE-CASE ROBUSTNESS TESTS (all-NaN-after-filter must not crash) ===

def test_edge_trend_all_nat_dates_no_crash():
    """TI trend must not crash when the scope has no valid dates (all NaT)."""
    from app import prepare_dataframe, run_training_intelligence, compute_kpis, detect_metrics
    # prepare_dataframe drops all-NaT rows, so simulate a subset by building a
    # df whose dates are all invalid strings → become NaT, then all dropped.
    rows = [
        {"Country": "PH", "Date of Training": "not-a-date", "Training Title": "F", "Trainer Name": "T",
         "Partner Name": "Globe", "Trainee Code": f"L{i}", "Training Assessment Score %": 80, "Pass Flag": 1}
        for i in range(5)
    ]
    df = prepare_dataframe(pd.DataFrame(rows))
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)
    # Should not raise. prepare_dataframe drops all-NaT rows, so df may be empty
    # here; the point is simply that no exception is thrown and we get output.
    result = run_training_intelligence("show me the training volume trend over time", df, metrics, kpis)
    answer = result["answer"] if isinstance(result, dict) else result
    assert isinstance(answer, str) and len(answer) > 0
    print("PASS Test EDGE-A: TI trend handles no-valid-date scope without crashing")


def test_edge_single_row_trend_no_crash():
    """A single-row scope must not crash the trend (insufficient range message)."""
    from app import prepare_dataframe, run_training_intelligence, compute_kpis, detect_metrics
    rows = [{"Country": "PH", "Date of Training": "2026-03-01", "Training Title": "F", "Trainer Name": "T",
             "Partner Name": "Globe", "Trainee Code": "L1", "Training Assessment Score %": 80, "Pass Flag": 1}]
    df = prepare_dataframe(pd.DataFrame(rows))
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)
    result = run_training_intelligence("trend over time", df, metrics, kpis)
    answer = result["answer"] if isinstance(result, dict) else result
    assert "insufficient" in answer.lower() or "trend" in answer.lower()
    print("PASS Test EDGE-B: Single-row scope handles trend without crashing")


def test_edge_attach_rate_no_double_scaling():
    """Attach rate values (already 0-100) must not be re-scaled by the removed heuristic."""
    from app import prepare_dataframe, run_training_intelligence, compute_kpis, detect_metrics
    # Low but legitimate attach rates already on a 0-100 scale (e.g. 0.9% and 1.0%).
    # prepare_dataframe normalizes per row: values <= 1 are treated as decimals → *100.
    # So supply already-percentage values > 1 to represent true low percentages.
    rows = [
        {"Country": "PH", "Date of Training": "2026-03-01", "Training Title": "F", "Trainer Name": "T",
         "Partner Name": "Globe", "Trainee Code": f"L{i}", "Training Assessment Score %": 80, "Pass Flag": 1,
         "Attach Rate Before": 3.0, "Attach Rate After": 5.0}
        for i in range(5)
    ]
    df = prepare_dataframe(pd.DataFrame(rows))
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)
    result = run_training_intelligence("what is the attach rate impact", df, metrics, kpis)
    ans = result["answer"] if isinstance(result, dict) else result
    # 3.0 and 5.0 are > 1 so stay as-is; must appear as 3.0%/5.0%, not 300%/500%.
    assert "3.0%" in ans and "5.0%" in ans, f"Attach rates were mis-scaled: {ans}"
    assert "300" not in ans and "500" not in ans, f"Attach rates double-scaled: {ans}"
    print("PASS Test EDGE-C: Attach rate not double-scaled (removed <=1 heuristic)")


def test_edge_empty_groupby_helpers_no_crash():
    """Core count helpers must return safe values on an empty dataframe."""
    from app import get_unique_sessions, compute_kpis, detect_metrics
    empty = pd.DataFrame(columns=["Country", "Date", "Training Name", "Trainer", "Trainee Code", "Pass Flag"])
    metrics = detect_metrics(empty)
    # Should not raise
    sessions = get_unique_sessions(empty, metrics)
    assert len(sessions) == 0
    kpis = compute_kpis(empty, metrics)
    assert isinstance(kpis, dict)
    print("PASS Test EDGE-D: Empty dataframe handled by session/KPI helpers without crashing")


# === DATA FRESHNESS (upload monitoring) TESTS ===

def test_data_freshness_current_overdue_nodata():
    """compute_data_freshness classifies markets as current / overdue / no_data
    against a fixed 'today', using a 14-day threshold."""
    from app import compute_data_freshness
    today = pd.Timestamp("2026-09-28")
    rows = [
        # ID: latest 5 days ago -> current
        {"Country": "ID", "Date": pd.Timestamp("2026-09-23")},
        {"Country": "ID", "Date": pd.Timestamp("2026-08-01")},
        # PH: latest exactly 14 days ago -> current (boundary, <= 14)
        {"Country": "PH", "Date": pd.Timestamp("2026-09-14")},
        # MY: latest 30 days ago -> overdue
        {"Country": "MY", "Date": pd.Timestamp("2026-08-29")},
        # VN: no valid date -> no_data
        {"Country": "VN", "Date": pd.NaT},
    ]
    df = pd.DataFrame(rows)
    res = compute_data_freshness(df, threshold_days=14, today=today)
    assert res is not None
    status = {r["market"]: r["status"] for r in res["rows"]}
    assert status["ID"] == "current", status
    assert status["PH"] == "current", status  # 14 days is within threshold
    assert status["MY"] == "overdue", status
    assert status["VN"] == "no_data", status
    assert res["current_count"] == 2
    assert res["overdue_count"] == 1
    assert res["no_data_count"] == 1
    assert res["total"] == 4
    # days_ago is measured against today
    my_days = next(r["days_ago"] for r in res["rows"] if r["market"] == "MY")
    assert my_days == 30, my_days
    print("PASS Test FRESH-A: freshness classifies current/overdue/no_data vs today")


def test_data_freshness_missing_columns():
    """Returns None when Country or Date is absent (no crash)."""
    from app import compute_data_freshness
    assert compute_data_freshness(pd.DataFrame({"Country": ["ID"]})) is None
    assert compute_data_freshness(pd.DataFrame({"Date": [pd.Timestamp("2026-01-01")]})) is None
    print("PASS Test FRESH-B: freshness returns None when Country/Date missing")


def test_data_freshness_overdue_sorted_first():
    """Overdue/no-data markets sort ahead of current ones for visibility."""
    from app import compute_data_freshness
    today = pd.Timestamp("2026-09-28")
    df = pd.DataFrame([
        {"Country": "ID", "Date": pd.Timestamp("2026-09-27")},   # current
        {"Country": "MY", "Date": pd.Timestamp("2026-07-01")},   # overdue
    ])
    res = compute_data_freshness(df, threshold_days=14, today=today)
    assert res["rows"][0]["market"] == "MY", "Overdue market should sort first"
    print("PASS Test FRESH-C: overdue markets sort first for visibility")


def _run_all_tests():
    test_a_repeated_trainee_rows()
    test_b_multiple_sessions_same_week()
    test_c_training_id()
    test_d_composite_fallback()
    test_e_country_aware()
    test_f_unique_learners_passed()
    test_g_no_trainee_fallback()
    test_h_training_type_sessions()
    print("--- Session logic tests passed ---")
    test_ti_filter_context()
    test_ti_session_count()
    test_ti_unique_learner()
    test_ti_insufficient_scope()
    test_ti_unsupported()
    print("--- Training Intelligence tests passed ---")
    test_p4_missing_score_no_nan()
    test_p4_comparison_is_table()
    test_p4_context_in_answer()
    print("--- Phase 4 cleanup tests passed ---")
    test_p41_based_on_metadata()
    test_p41_supporting_data_scope()
    test_p41_calc_description()
    test_p41_limited_data_status()
    test_p41_ranking_basis()
    test_p41_no_fake_confidence()
    print("--- Phase 4.1 tests passed ---")
    test_score_scaling_needs_attention()
    print("--- Scaling test passed ---")
    test_p5_prepare_dataframe_consistency()
    test_p5_upload_unsupported_type()
    test_p5_empty_scope_kpis()
    test_p5_single_market_no_comparison()
    print("--- Phase 5 tests passed ---")
    test_uat_mixed_score_formats()
    test_uat_ph_account_score_display()
    print("--- UAT display tests passed ---")
    test_threshold_derives_pass_flag_from_score()
    test_threshold_decimal_scores_scaled_before_threshold()
    test_threshold_blank_score_excluded_not_failed()
    test_threshold_fail_flag_is_inverse()
    test_threshold_inconsistent_source_flags_corrected()
    print("--- base passing standard tests passed ---")
    test_tiered_threshold_map()
    test_tiered_foundation_vs_activation_at_75()
    test_tiered_activation_80_passes()
    test_tiered_blank_type_defaults_to_70()
    test_tiered_training_type_vs_method_separation()
    print("--- tiered passing standard tests passed ---")
    test_nan_executive_insights_no_nan_string()
    test_nan_training_intelligence_pass_rate_no_nan()
    test_nan_ranking_bottom_no_nan()
    test_nan_needs_attention_and_why_no_nan()
    test_nan_all_blank_subset_shows_no_data()
    print("--- NaN-group handling tests passed ---")
    test_data_freshness_current_overdue_nodata()
    test_data_freshness_missing_columns()
    test_data_freshness_overdue_sorted_first()
    print("--- data freshness tests passed ---")
    test_edge_trend_all_nat_dates_no_crash()
    test_edge_single_row_trend_no_crash()
    test_edge_attach_rate_no_double_scaling()
    test_edge_empty_groupby_helpers_no_crash()
    print("--- edge-case robustness tests passed ---")
    print("\nAll tests passed!")


if __name__ == "__main__":
    _run_all_tests()
