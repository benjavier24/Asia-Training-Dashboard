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
         "Partner Name": "Globe", "Training Method": "Online", "Trainee Code": "E1", "Pass Flag": "1"}
        for _ in range(5)
    ]
    raw = pd.DataFrame(rows)
    prepared = prepare_dataframe(raw)
    # Columns normalized to canonical names
    assert "Training Name" in prepared.columns, "Training Title should normalize to Training Name"
    assert "Trainer" in prepared.columns, "Trainer Name should normalize to Trainer"
    assert "Account" in prepared.columns, "Partner Name should normalize to Account"
    # Training Type consolidated (Online -> Virtual/Online)
    assert (prepared["Training Type"] == "Virtual/Online").all(), "Online should consolidate to Virtual/Online"
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
    print("\nAll tests passed!")


if __name__ == "__main__":
    _run_all_tests()
