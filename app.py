import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import numpy as np
from datetime import datetime
from thefuzz import fuzz, process

# Page config
st.set_page_config(
    page_title="Asia Training Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Phase 1: Visual Foundation
st.markdown("""
<style>
    /* ═══ DESIGN SYSTEM ═══ */
    /* Palette:
       Brand: #E63946 (bolttech red)
       Analytics: #0891B2 (teal-600)
       Analytics Light: #06B6D4 (cyan-500)
       Success: #10B981 (emerald-500)
       Warning: #F59E0B (amber-500)
       Critical: #EF4444 (red-500)
       Neutral-900: #111827
       Neutral-700: #374151
       Neutral-500: #6B7280
       Neutral-300: #D1D5DB
       Neutral-100: #F3F4F6
       White: #FFFFFF
       Bg: #F8FAFC
    */

    /* ═══ GLOBAL ═══ */
    .stApp {
        background: #F8FAFC !important;
    }
    .stApp, .stApp p, .stApp span, .stApp li, .stApp label, .stApp div,
    .stMarkdown, .stMarkdown p, .stMarkdown span,
    [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] span,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] h4 {
        color: #111827 !important;
        font-family: 'Inter', 'Segoe UI', -apple-system, sans-serif;
    }
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div {
        color: #374151 !important;
    }
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #6B7280 !important;
    }

    /* ═══ TYPOGRAPHY ═══ */
    .dash-title {
        font-size: 1.5rem !important;
        font-weight: 800 !important;
        color: #111827 !important;
        margin: 0 !important;
        line-height: 1.2;
        letter-spacing: -0.02em;
    }
    .dash-subtitle {
        font-size: 0.78rem !important;
        color: #6B7280 !important;
        margin: 2px 0 0 !important;
        font-weight: 400;
        letter-spacing: 0.3px;
    }
    .section-header {
        font-size: 0.9rem;
        font-weight: 700;
        color: #111827 !important;
        margin: 1.2rem 0 0.6rem;
        padding-bottom: 6px;
        border-bottom: 1px solid #E5E7EB;
        letter-spacing: -0.01em;
    }

    /* ═══ CHIP / PILL STYLES ═══ */
    .chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin: 4px 0 8px;
    }
    .chip {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 10px;
        border-radius: 100px;
        font-size: 0.68rem;
        font-weight: 500;
        background: #F3F4F6;
        color: #374151 !important;
        border: 1px solid #E5E7EB;
        white-space: nowrap;
    }
    .chip.active {
        background: #ECFEFF;
        border-color: #0891B2;
        color: #0891B2 !important;
        font-weight: 600;
    }

    /* ═══ PRIMARY KPI CARDS ═══ */
    .kpi-card {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 18px 14px;
        text-align: center;
        border: 1px solid #F3F4F6;
        height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        transition: box-shadow 0.15s ease;
    }
    .kpi-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.07);
    }
    .kpi-value {
        font-size: clamp(1.3rem, 3.5vw, 1.7rem);
        font-weight: 800;
        color: #0891B2 !important;
        line-height: 1;
        margin: 6px 0 3px;
        word-break: break-word;
        overflow-wrap: break-word;
        max-width: 100%;
        letter-spacing: -0.02em;
    }
    .kpi-label {
        font-size: 0.62rem;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        font-weight: 600;
        color: #6B7280 !important;
    }
    .kpi-delta {
        font-size: 0.65rem;
        margin-top: 3px;
        color: #9CA3AF !important;
        font-weight: 400;
    }
    .kpi-delta.positive { color: #10B981 !important; font-weight: 600; }
    .kpi-delta.negative { color: #EF4444 !important; font-weight: 600; }

    /* ═══ SECONDARY KPI CARDS ═══ */
    .kpi-card-sm {
        background: #FFFFFF;
        border-radius: 10px;
        padding: 12px 10px;
        text-align: center;
        border: 1px solid #F3F4F6;
        height: 90px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        overflow: hidden;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .kpi-card-sm .kpi-value {
        font-size: clamp(0.75rem, 2vw, 1rem);
        font-weight: 700;
        color: #374151 !important;
        margin: 4px 0 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 100%;
    }
    .kpi-card-sm .kpi-label {
        font-size: 0.58rem;
        color: #9CA3AF !important;
    }
    .kpi-card-sm .kpi-delta {
        font-size: 0.6rem;
        color: #9CA3AF !important;
    }
    /* De-emphasize N/A or 0 values */
    .kpi-card-sm.muted {
        opacity: 0.5;
    }

    /* ═══ INSIGHT / INFO BOXES ═══ */
    .insight-box {
        background: #FFFFFF;
        border-radius: 10px;
        padding: 12px 16px;
        border-left: 3px solid #0891B2;
        margin: 5px 0;
        color: #374151 !important;
        font-size: 0.82rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        line-height: 1.5;
    }
    .warning-box {
        background: #FFFFFF;
        border-radius: 10px;
        padding: 12px 16px;
        border-left: 3px solid #F59E0B;
        margin: 5px 0;
        color: #374151 !important;
        font-size: 0.82rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        line-height: 1.5;
    }
    .positive { color: #10B981 !important; font-weight: 600; }
    .negative { color: #EF4444 !important; font-weight: 600; }

    /* ═══ DATA AVAILABILITY ═══ */
    .data-avail-present { color: #10B981; }
    .data-avail-missing { color: #EF4444; opacity: 0.7; }

    /* ═══ TABS ═══ */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background: #FFFFFF;
        border-radius: 10px;
        padding: 3px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        border: 1px solid #F3F4F6;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 18px;
        border-radius: 7px;
        font-weight: 500;
        font-size: 0.8rem;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: #0891B2 !important;
        color: white !important;
    }

    /* ═══ ACCOUNT CARDS (Performance tab) ═══ */
    .account-card {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 6px;
        padding: 10px 14px;
        border-radius: 10px;
        background: #FFFFFF;
        border: 1px solid #F3F4F6;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }
    .account-card .name {
        font-weight: 600;
        font-size: 0.82rem;
        color: #111827 !important;
    }
    .account-card .bar-bg {
        background: #E5E7EB;
        border-radius: 4px;
        height: 6px;
        width: 100%;
        margin-top: 3px;
    }

    /* ═══ SIDEBAR ═══ */
    [data-testid="stSidebar"] {
        background: #FFFFFF !important;
        border-right: 1px solid #E5E7EB;
    }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stDateInput label,
    [data-testid="stSidebar"] .stSlider label {
        color: #374151 !important;
        font-weight: 500;
        font-size: 0.78rem;
    }

    /* ═══ TAGS ═══ */
    span[data-baseweb="tag"] {
        background-color: #ECFEFF !important;
        border-color: #0891B2 !important;
    }
    span[data-baseweb="tag"] span {
        color: #0891B2 !important;
    }

    /* ═══ DATAFRAMES ═══ */
    [data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        border: 1px solid #F3F4F6;
    }

    /* ═══ METRICS ═══ */
    [data-testid="stMetric"] {
        background: #FFFFFF;
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        border: 1px solid #F3F4F6;
    }

    /* ═══ PLOTLY ═══ */
    .js-plotly-plot {
        border-radius: 10px;
    }

    /* ═══ REDUCE STREAMLIT PADDING ═══ */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0.5rem !important;
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 1rem !important;
    }
    /* Hide sidebar collapse button text artifact (Material icon fallback text) */
    [data-testid="stSidebarCollapseButton"],
    [data-testid="collapsedControl"] {
        visibility: hidden !important;
        height: 0 !important;
        overflow: hidden !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    /* Fix Material Symbols icon font fallback — hide text when icons fail to load */
    .material-symbols-rounded,
    .material-symbols-outlined,
    [data-testid="stExpanderToggleIcon"],
    [data-testid="stFileUploaderDropzoneIcon"] {
        font-size: 0 !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
    }
    /* Expander: ensure the toggle still functions but icon text is hidden */
    [data-testid="stExpander"] summary span[data-testid="stExpanderToggleIcon"] {
        display: none !important;
    }

    /* ═══ FILTER HEADER IN SIDEBAR ═══ */
    .sidebar-title {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #9CA3AF !important;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid #E5E7EB;
    }

    /* ═══ BREADCRUMB ═══ */
    .breadcrumb {
        font-size: 0.7rem;
        color: #9CA3AF !important;
        margin: 0 0 2px;
        letter-spacing: 0.2px;
    }
    .breadcrumb span {
        color: #9CA3AF !important;
    }
    .breadcrumb .sep {
        margin: 0 4px;
        opacity: 0.5;
    }

    /* ═══ INSIGHT STATUS CARDS ═══ */
    .insight-card {
        background: #FFFFFF;
        border-radius: 10px;
        padding: 12px 14px;
        margin: 5px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        border-left: 3px solid #D1D5DB;
        font-size: 0.82rem;
        line-height: 1.5;
        color: #374151 !important;
    }
    .insight-card.positive { border-left-color: #10B981; }
    .insight-card.attention { border-left-color: #F59E0B; }
    .insight-card.critical { border-left-color: #EF4444; }
    .insight-card.watch { border-left-color: #6366F1; }
    .insight-card.neutral { border-left-color: #9CA3AF; }
    .insight-status {
        font-size: 0.6rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 3px;
    }
    .insight-status.positive { color: #10B981 !important; }
    .insight-status.attention { color: #F59E0B !important; }
    .insight-status.critical { color: #EF4444 !important; }
    .insight-status.watch { color: #6366F1 !important; }
    .insight-status.neutral { color: #9CA3AF !important; }
    .insight-headline {
        font-weight: 600;
        font-size: 0.84rem;
        color: #111827 !important;
        margin-bottom: 2px;
    }
    .insight-detail {
        font-size: 0.75rem;
        color: #6B7280 !important;
    }
    /* Needs Attention list */
    .attention-list {
        background: #FFFFFF;
        border-radius: 10px;
        padding: 14px 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        border: 1px solid #FEF3C7;
    }
    .attention-item {
        display: flex;
        align-items: baseline;
        gap: 8px;
        padding: 6px 0;
        border-bottom: 1px solid #F3F4F6;
        font-size: 0.8rem;
    }
    .attention-item:last-child { border-bottom: none; }
    .attention-rank {
        font-weight: 700;
        color: #F59E0B !important;
        font-size: 0.72rem;
        min-width: 18px;
    }
    .attention-text { color: #374151 !important; }
    .attention-metric {
        margin-left: auto;
        font-weight: 600;
        color: #EF4444 !important;
        font-size: 0.75rem;
        white-space: nowrap;
    }
    /* Method comparison */
    .method-row {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 12px;
        background: #FFFFFF;
        border-radius: 8px;
        margin: 4px 0;
        border: 1px solid #F3F4F6;
    }
    .method-name {
        font-weight: 600;
        font-size: 0.8rem;
        color: #111827 !important;
        min-width: 100px;
    }
    .method-stat {
        font-size: 0.72rem;
        color: #6B7280 !important;
    }
    .method-rate {
        margin-left: auto;
        font-weight: 700;
        font-size: 0.9rem;
        color: #0891B2 !important;
    }
</style>
""", unsafe_allow_html=True)


# === COLUMN DETECTION & MAPPING ===

COLUMN_ALIASES = {
    "date": "Date", "date of training": "Date", "training date": "Date",
    "trainer": "Trainer", "trainer name": "Trainer", "facilitator": "Trainer",
    "account": "Account", "partner name": "Account", "partner": "Account", "client": "Account",
    "country": "Country", "market": "Country", "region": "Country",
    "store": "Store", "store name": "Store", "branch": "Store", "location": "Store", "outlet": "Store",
    "training name": "Training Name", "training title": "Training Name", "course": "Training Name",
    "program": "Training Name", "module": "Training Name",
    "training type": "Training Type", "training method": "Training Type", "type": "Training Type",
    "method": "Training Type", "delivery mode": "Training Type",
    "training id": "Training ID", "session id": "Training ID",
    "trainee name": "Trainee Name", "participant": "Trainee Name", "learner": "Trainee Name",
    "trainee code": "Trainee Code", "employee id": "Trainee Code",
    "training assessment score %": "Assessment Score", "score": "Assessment Score",
    "assessment score": "Assessment Score", "test score": "Assessment Score", "grade": "Assessment Score",
    "training assessment result": "Assessment Result", "result": "Assessment Result",
    "pass/fail": "Assessment Result", "status": "Assessment Result",
    "pass flag": "Pass Flag", "passed": "Pass Flag",
    "fail flag": "Fail Flag", "failed": "Fail Flag",
    "total invited": "Total Invited", "invited": "Total Invited",
    "total attended": "Total Attended", "attended": "Total Attended", "attendance count": "Total Attended",
    "total passed": "Total Passed",
    "attach rate before": "Attach Rate Before", "attach rate before (%)": "Attach Rate Before",
    "attach rate after": "Attach Rate After", "attach rate after (%)": "Attach Rate After",
    "attach lift": "Attach Lift",
    "training hours": "Training Hours", "hours": "Training Hours", "duration": "Training Hours",
    "duration (hours)": "Training Hours",
}


def normalize_columns(df):
    """Map uploaded column names to canonical names using aliases."""
    rename_map = {}
    for col in df.columns:
        col_lower = col.strip().lower()
        if col_lower in COLUMN_ALIASES:
            canonical = COLUMN_ALIASES[col_lower]
            if canonical not in rename_map.values():
                rename_map[col] = canonical
    df = df.rename(columns=rename_map)
    return df


def fuzzy_match_store(store_name, candidates, threshold=70):
    """Find the best fuzzy match for a store name."""
    if not store_name or not candidates:
        return None, 0
    clean_name = str(store_name).strip().lower()
    clean_candidates = [str(c).strip().lower() for c in candidates]
    if clean_name in clean_candidates:
        idx = clean_candidates.index(clean_name)
        return candidates[idx], 100
    result = process.extractOne(
        clean_name, clean_candidates,
        scorer=fuzz.token_sort_ratio,
        score_cutoff=threshold
    )
    if result:
        matched_text, score = result[0], result[1]
        idx = clean_candidates.index(matched_text)
        return candidates[idx], score
    return None, 0


def match_sales_to_training(training_df, sales_df, match_threshold=70):
    """Match sales data to training records using fuzzy store name matching."""
    training_df["Date"] = pd.to_datetime(training_df["Date"], errors="coerce")
    sales_df["Date"] = pd.to_datetime(sales_df["Date"], errors="coerce")

    sales_stores = sales_df["Store"].dropna().unique().tolist() if "Store" in sales_df.columns else []
    sales_accounts = sales_df["Account"].dropna().unique().tolist() if "Account" in sales_df.columns else []

    if "Store" in training_df.columns and sales_stores:
        training_match_col = "Store"
        sales_match_col = "Store"
        sales_candidates = sales_stores
    elif "Account" in training_df.columns and sales_accounts:
        training_match_col = "Account"
        sales_match_col = "Account"
        sales_candidates = sales_accounts
    else:
        return training_df, pd.DataFrame()

    training_names = training_df[training_match_col].dropna().unique()
    match_map = {}
    match_report = []

    for name in training_names:
        matched, score = fuzzy_match_store(name, sales_candidates, threshold=match_threshold)
        match_map[name] = matched
        match_report.append({
            "Training Name": name,
            "Matched To": matched if matched else "❌ No match",
            "Score": score,
            "Status": "✅ Matched" if matched else "❌ Unmatched"
        })

    match_report_df = pd.DataFrame(match_report).sort_values("Score", ascending=False)
    has_transactions = "Total Transactions" in sales_df.columns and "Transactions with Protection" in sales_df.columns

    attach_before_list = []
    attach_after_list = []

    for idx, row in training_df.iterrows():
        training_date = row["Date"]
        training_store = row.get(training_match_col)

        if pd.isna(training_date) or pd.isna(training_store):
            attach_before_list.append(np.nan)
            attach_after_list.append(np.nan)
            continue

        matched_store = match_map.get(training_store)

        if not matched_store or not has_transactions:
            attach_before_list.append(np.nan)
            attach_after_list.append(np.nan)
            continue

        store_sales = sales_df[sales_df[sales_match_col] == matched_store]

        before_mask = (store_sales["Date"] >= training_date - pd.Timedelta(days=30)) & \
                      (store_sales["Date"] < training_date)
        before = store_sales[before_mask]
        if len(before) > 0:
            total = before["Total Transactions"].sum()
            protected = before["Transactions with Protection"].sum()
            attach_before_list.append((protected / total) if total > 0 else np.nan)
        else:
            attach_before_list.append(np.nan)

        after_mask = (store_sales["Date"] > training_date) & \
                     (store_sales["Date"] <= training_date + pd.Timedelta(days=30))
        after = store_sales[after_mask]
        if len(after) > 0:
            total = after["Total Transactions"].sum()
            protected = after["Transactions with Protection"].sum()
            attach_after_list.append((protected / total) if total > 0 else np.nan)
        else:
            attach_after_list.append(np.nan)

    training_df["Attach Rate Before"] = attach_before_list
    training_df["Attach Rate After"] = attach_after_list
    return training_df, match_report_df


def detect_powerbi_format(df):
    """Detect if a DataFrame is a raw Power BI export and fix headers/columns.
    
    Power BI exports often have:
    - Row 0: Filter info ("Applied filters:..." or "Exported data limited to...")
    - Row 1: Actual column headers
    - Columns like 'Channel_Name', 'GX Unit Sold', 'GX Subs', 'GX AR %', calendar month
    """
    # Check if first column name looks like a Power BI filter line
    first_col = str(df.columns[0]).strip().lower()
    is_powerbi = ("applied filter" in first_col or
                  "exported data" in first_col or
                  "no filters" in first_col or
                  first_col.startswith("unnamed"))

    if not is_powerbi:
        return df, False

    # Find the actual header row (look for known column patterns in first few rows)
    header_row = None
    for i in range(min(5, len(df))):
        row_vals = [str(v).strip().lower() for v in df.iloc[i].values if pd.notna(v)]
        row_text = " ".join(row_vals)
        if any(kw in row_text for kw in ["channel_name", "store", "unit sold", "subs", "ar %", "attach"]):
            header_row = i
            break

    if header_row is not None:
        # Re-read with correct header
        new_cols = df.iloc[header_row].values
        new_df = df.iloc[header_row + 1:].reset_index(drop=True)
        new_df.columns = [str(c).strip() if pd.notna(c) else f"col_{i}" for i, c in enumerate(new_cols)]
        return new_df, True

    return df, False


def normalize_powerbi_sales(df):
    """Map Power BI sales export columns to the standard format.
    
    Handles columns like:
    - Channel_Name -> Store
    - GX Unit Sold / Unit Sold / Units Sold -> Total Transactions
    - GX Subs / Subs / Subscriptions -> Transactions with Protection
    - GX AR % / AR % / Attach Rate -> Attach Rate (pre-calculated)
    - 'Dates Table'[Calendar MonthYear] / MonthYear -> Date
    """
    col_lower_map = {str(c).strip().lower(): c for c in df.columns}

    rename = {}

    # Store
    for pattern in ["channel_name", "channel name", "store name", "store", "branch"]:
        if pattern in col_lower_map:
            rename[col_lower_map[pattern]] = "Store"
            break

    # Total Transactions (units sold)
    for pattern in ["gx unit sold", "unit sold", "units sold", "total transactions",
                    "total units", "devices sold", "total devices"]:
        if pattern in col_lower_map:
            rename[col_lower_map[pattern]] = "Total Transactions"
            break

    # Transactions with Protection (subscriptions)
    for pattern in ["gx subs", "subs", "subscriptions", "transactions with protection",
                    "protection sold", "attach count"]:
        if pattern in col_lower_map:
            rename[col_lower_map[pattern]] = "Transactions with Protection"
            break

    # Pre-calculated attach rate
    for pattern in ["gx ar %", "ar %", "attach rate", "attach rate %", "ar%"]:
        if pattern in col_lower_map:
            rename[col_lower_map[pattern]] = "Attach Rate"
            break

    # Date (monthly format like "Aug 2025")
    for col in df.columns:
        col_lower = str(col).strip().lower()
        if "monthyear" in col_lower or "calendar month" in col_lower or "month" in col_lower:
            rename[col] = "Date"
            break

    df = df.rename(columns=rename)

    # Parse monthly date strings (e.g., "Aug 2025" -> datetime)
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], format="mixed", errors="coerce")

    # Ensure numeric columns
    for col in ["Total Transactions", "Transactions with Protection", "Attach Rate"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def load_sales_exports(folder_path):
    """Auto-load all sales export files, handling both standard and Power BI formats."""
    import os
    import glob

    if not os.path.exists(folder_path):
        return None, f"Sales folder not found: {folder_path}"

    files = glob.glob(os.path.join(folder_path, "*.xlsx")) + \
            glob.glob(os.path.join(folder_path, "*.csv"))

    if not files:
        return None, "No sales export files found in folder."

    all_dfs = []
    loaded_files = []
    errors = []

    for file_path in files:
        try:
            filename = os.path.basename(file_path)
            if filename.endswith(".csv"):
                file_df = pd.read_csv(file_path)
            else:
                file_df = pd.read_excel(file_path)

            # Detect and fix Power BI exports
            file_df, was_powerbi = detect_powerbi_format(file_df)
            if was_powerbi:
                file_df = normalize_powerbi_sales(file_df)
            else:
                file_df = normalize_columns(file_df)

            # Infer country from filename if not present (e.g., "PH_Globe Sales Data.xlsx")
            if "Country" not in file_df.columns:
                country_code = filename.split("_")[0].upper()
                if len(country_code) == 2:
                    file_df["Country"] = country_code

            # Infer account from filename if not present (e.g., "PH_Globe Sales Data.xlsx")
            if "Account" not in file_df.columns:
                parts = filename.replace(".xlsx", "").replace(".csv", "").split("_")
                if len(parts) >= 2:
                    account_name = parts[1].split(" Sales")[0].split(" sales")[0].strip()
                    if account_name:
                        file_df["Account"] = account_name

            all_dfs.append(file_df)
            loaded_files.append(filename)
        except Exception as e:
            errors.append(f"{os.path.basename(file_path)}: {e}")

    if not all_dfs:
        return None, f"Could not read any files. Errors: {'; '.join(errors)}"

    combined = pd.concat(all_dfs, ignore_index=True)
    if "Date" in combined.columns:
        combined["Date"] = pd.to_datetime(combined["Date"], errors="coerce")

    status = f"Loaded {len(combined):,} rows from {len(loaded_files)} file(s): {', '.join(loaded_files)}"
    if errors:
        status += f" | Errors: {'; '.join(errors)}"
    return combined, status


def detect_metrics(df):
    """Detect which metrics are available in the dataset."""
    metrics = {}
    metrics["Date"] = "Date" in df.columns and df["Date"].notna().sum() > 0
    metrics["Trainer"] = "Trainer" in df.columns and df["Trainer"].notna().sum() > 0
    metrics["Account"] = "Account" in df.columns and df["Account"].notna().sum() > 0
    metrics["Country"] = "Country" in df.columns and df["Country"].notna().sum() > 0
    metrics["Store"] = "Store" in df.columns and df["Store"].notna().sum() > 0
    metrics["Training Name"] = "Training Name" in df.columns and df["Training Name"].notna().sum() > 0
    metrics["Training Type"] = "Training Type" in df.columns and df["Training Type"].notna().sum() > 0
    metrics["Training ID"] = "Training ID" in df.columns and df["Training ID"].notna().sum() > 0
    metrics["Trainee Name"] = "Trainee Name" in df.columns and df["Trainee Name"].notna().sum() > 0
    metrics["Trainee Code"] = "Trainee Code" in df.columns and df["Trainee Code"].notna().sum() > 0
    metrics["Assessment Score"] = "Assessment Score" in df.columns and df["Assessment Score"].notna().sum() > 0
    metrics["Assessment Result"] = "Assessment Result" in df.columns and df["Assessment Result"].notna().sum() > 0
    metrics["Pass Flag"] = "Pass Flag" in df.columns and df["Pass Flag"].notna().sum() > 0
    metrics["Total Invited"] = "Total Invited" in df.columns and df["Total Invited"].notna().sum() > 0
    metrics["Total Attended"] = "Total Attended" in df.columns and df["Total Attended"].notna().sum() > 0
    metrics["Attach Rate Before"] = "Attach Rate Before" in df.columns and df["Attach Rate Before"].notna().sum() > 0
    metrics["Attach Rate After"] = "Attach Rate After" in df.columns and df["Attach Rate After"].notna().sum() > 0
    metrics["Training Hours"] = "Training Hours" in df.columns and df["Training Hours"].notna().sum() > 0
    return metrics


def compute_kpis(df, metrics):
    """Compute KPIs based on available metrics."""
    kpis = {}

    if metrics.get("Training ID"):
        kpis["Total Sessions"] = df["Training ID"].nunique()
    else:
        # Count unique sessions as unique combos of Date + Training Name + Trainer
        session_cols = []
        if metrics.get("Date"):
            session_cols.append("Date")
        if metrics.get("Training Name"):
            session_cols.append("Training Name")
        if metrics.get("Trainer"):
            session_cols.append("Trainer")
        if session_cols:
            kpis["Total Sessions"] = df.groupby(session_cols).ngroups
        elif metrics.get("Date"):
            kpis["Total Sessions"] = df["Date"].nunique()

    if metrics.get("Training Hours"):
        kpis["Total Training Hours"] = df["Training Hours"].sum()

    if metrics.get("Trainee Code"):
        kpis["Unique Learners"] = df["Trainee Code"].nunique()
    elif metrics.get("Trainee Name"):
        kpis["Unique Learners"] = df["Trainee Name"].nunique()

    kpis["Total Participants"] = len(df)

    if metrics.get("Assessment Score"):
        scores = pd.to_numeric(df["Assessment Score"], errors="coerce").dropna()
        if len(scores) > 0:
            avg = scores.mean()
            if avg <= 1:
                avg = avg * 100
            kpis["Avg Assessment Score"] = round(avg, 1)

    if metrics.get("Pass Flag"):
        pass_flags = pd.to_numeric(df["Pass Flag"], errors="coerce")
        total = pass_flags.notna().sum()
        passed = pass_flags.sum()
        if total > 0:
            kpis["Pass Rate"] = round(passed / total * 100, 1)
            kpis["Total Passed"] = int(passed)
    elif metrics.get("Assessment Result"):
        results = df["Assessment Result"].str.strip().str.lower()
        total = results.notna().sum()
        passed = results.isin(["passed", "pass", "p", "1", "yes", "complete", "completed"]).sum()
        if total > 0:
            kpis["Pass Rate"] = round(passed / total * 100, 1)
            kpis["Total Passed"] = int(passed)

    if metrics.get("Total Invited") and metrics.get("Total Attended"):
        invited = pd.to_numeric(df["Total Invited"], errors="coerce").sum()
        attended = pd.to_numeric(df["Total Attended"], errors="coerce").sum()
        if invited > 0:
            kpis["Attendance Rate"] = round(attended / invited * 100, 1)

    if metrics.get("Attach Rate Before"):
        vals = pd.to_numeric(df["Attach Rate Before"], errors="coerce").dropna()
        if len(vals) > 0:
            avg = vals.mean()
            kpis["Avg Attach Before"] = round(avg * 100 if avg <= 1 else avg, 1)

    if metrics.get("Attach Rate After"):
        vals = pd.to_numeric(df["Attach Rate After"], errors="coerce").dropna()
        if len(vals) > 0:
            avg = vals.mean()
            kpis["Avg Attach After"] = round(avg * 100 if avg <= 1 else avg, 1)

    if "Avg Attach Before" in kpis and "Avg Attach After" in kpis:
        kpis["Attach Improvement"] = round(kpis["Avg Attach After"] - kpis["Avg Attach Before"], 1)

    if metrics.get("Country"):
        kpis["Countries"] = df["Country"].nunique()
    if metrics.get("Account"):
        kpis["Accounts"] = df["Account"].nunique()
    if metrics.get("Store"):
        kpis["Stores"] = df["Store"].nunique()

    return kpis


def render_insight_card(status, headline, detail=None):
    """Render a structured insight card with status, headline, and optional detail."""
    detail_html = f'<div class="insight-detail">{detail}</div>' if detail else ""
    return f"""
    <div class="insight-card {status}">
        <div class="insight-status {status}">{status}</div>
        <div class="insight-headline">{headline}</div>
        {detail_html}
    </div>
    """


def generate_executive_insights(df, metrics, kpis, view_level="regional", active_market=None):
    """Generate scoped, deterministic insights based on current filter context.

    view_level: 'regional' (all markets), 'market' (single market), or 'account' (single account)
    Returns list of (status, headline, detail) tuples.
    """
    insights = []

    # --- PASS RATE INSIGHTS ---
    if "Pass Rate" in kpis:
        rate = kpis["Pass Rate"]
        if view_level == "regional" and metrics.get("Country") and df["Country"].nunique() > 1:
            # Regional: compare markets
            mkt_rates = df.groupby("Country")["Pass Flag"].mean().sort_values(ascending=False) * 100
            if len(mkt_rates) > 1:
                top_mkt, top_rate = mkt_rates.index[0], mkt_rates.iloc[0]
                bot_mkt, bot_rate = mkt_rates.index[-1], mkt_rates.iloc[-1]
                gap = round(top_rate - bot_rate, 1)
                insights.append(("positive", f"{top_mkt} has the highest pass rate at {top_rate:.1f}%",
                                 f"{gap} pts above {bot_mkt} ({bot_rate:.1f}%)."))
                if bot_rate < 70:
                    insights.append(("attention", f"{bot_mkt} has the lowest pass rate at {bot_rate:.1f}%",
                                     f"{round(rate - bot_rate, 1)} pts below the regional average of {rate}%."))
        elif view_level == "market" and metrics.get("Account") and df["Account"].nunique() > 1:
            # Market: compare accounts
            acct_rates = df.groupby("Account")["Pass Flag"].mean().sort_values(ascending=False) * 100
            if len(acct_rates) > 1:
                top_acct, top_rate_a = acct_rates.index[0], acct_rates.iloc[0]
                bot_acct, bot_rate_a = acct_rates.index[-1], acct_rates.iloc[-1]
                mkt_name = active_market or "this market"
                insights.append(("positive", f"{top_acct} has the highest pass rate at {top_rate_a:.1f}%",
                                 f"In {mkt_name}."))
                if bot_rate_a < rate:
                    diff = round(rate - bot_rate_a, 1)
                    insights.append(("attention", f"{bot_acct} has the lowest pass rate at {bot_rate_a:.1f}%",
                                     f"{diff} pts below the {mkt_name} average of {rate}%."))
        else:
            # Single scope: just report the rate
            if rate >= 85:
                insights.append(("positive", f"Pass rate is {rate}%", "Strong assessment performance across the current selection."))
            elif rate >= 70:
                insights.append(("watch", f"Pass rate at {rate}%", "Below 85% — consider reviewing assessment content."))
            else:
                insights.append(("critical", f"Pass rate is {rate}%", "Below target threshold. Content or delivery may need adjustment."))

    # --- ASSESSMENT SCORE INSIGHTS ---
    if "Avg Assessment Score" in kpis:
        score = kpis["Avg Assessment Score"]
        if view_level == "regional" and metrics.get("Country") and df["Country"].nunique() > 1:
            mkt_scores = df.groupby("Country")["Assessment Score"].mean().sort_values(ascending=False)
            if mkt_scores.max() <= 1:
                mkt_scores = mkt_scores * 100
            if len(mkt_scores) > 1:
                top_s = mkt_scores.index[0]
                insights.append(("neutral", f"Highest avg score: {top_s} at {mkt_scores.iloc[0]:.1f}%",
                                 f"Regional average is {score}%."))
        elif view_level == "market" and metrics.get("Account") and df["Account"].nunique() > 1:
            acct_scores = df.groupby("Account")["Assessment Score"].mean().sort_values(ascending=False)
            if acct_scores.max() <= 1:
                acct_scores = acct_scores * 100
            if len(acct_scores) > 1:
                bot_s_acct = acct_scores.index[-1]
                bot_s_val = acct_scores.iloc[-1]
                diff = round(score - bot_s_val, 1)
                if diff > 5:
                    insights.append(("attention", f"{bot_s_acct} has the lowest avg score at {bot_s_val:.1f}%",
                                     f"{diff} pts below the market average."))

    # --- VOLUME INSIGHTS ---
    if view_level == "regional" and metrics.get("Country") and df["Country"].nunique() > 1:
        mkt_vol = df["Country"].value_counts()
        if len(mkt_vol) > 1:
            top_vol_mkt = mkt_vol.index[0]
            share = round(mkt_vol.iloc[0] / mkt_vol.sum() * 100, 1)
            insights.append(("neutral", f"{top_vol_mkt} accounts for {share}% of total training records",
                             f"{mkt_vol.iloc[0]:,} of {mkt_vol.sum():,} records."))

    # --- ATTACH RATE INSIGHTS ---
    if "Attach Improvement" in kpis:
        imp = kpis["Attach Improvement"]
        if imp > 0:
            insights.append(("positive", f"Attach rate improved by +{imp}pp post-training",
                             "Measured 30 days after training delivery."))
        elif imp < 0:
            insights.append(("critical", f"Attach rate declined by {abs(imp)}pp post-training",
                             "Investigate contributing factors in the affected accounts."))

    # --- TRAINING METHOD INSIGHTS ---
    if metrics.get("Training Type") and df["Training Type"].nunique() > 1 and metrics.get("Pass Flag"):
        method_perf = df.groupby("Training Type").agg(
            sessions=("Training Type", "count"),
            pass_rate=("Pass Flag", "mean")
        ).reset_index()
        method_perf["pass_rate"] = (method_perf["pass_rate"] * 100).round(1)
        method_perf = method_perf.sort_values("pass_rate", ascending=False)
        if len(method_perf) >= 2:
            top_m = method_perf.iloc[0]
            bot_m = method_perf.iloc[-1]
            diff = round(top_m["pass_rate"] - bot_m["pass_rate"], 1)
            if diff > 2:
                insights.append(("neutral",
                    f"{top_m['Training Type']} recorded a {diff} pt higher pass rate than {bot_m['Training Type']}",
                    f"{top_m['pass_rate']}% vs {bot_m['pass_rate']}%."))

    return insights


def generate_needs_attention(df, metrics, kpis, view_level="regional"):
    """Generate a prioritized 'Needs Attention' list. Returns list of (entity, reason, metric_str)."""
    items = []

    if view_level == "regional" and metrics.get("Country") and metrics.get("Pass Flag"):
        mkt_rates = df.groupby("Country")["Pass Flag"].mean().sort_values() * 100
        avg = kpis.get("Pass Rate", 0)
        for mkt, rate in mkt_rates.items():
            if rate < avg and rate < 75:
                items.append((mkt, "below-avg pass rate", f"{rate:.1f}%"))
                if len(items) >= 5:
                    break

    elif view_level == "market" and metrics.get("Account") and metrics.get("Pass Flag"):
        acct_rates = df.groupby("Account")["Pass Flag"].mean().sort_values() * 100
        avg = kpis.get("Pass Rate", 0)
        for acct, rate in acct_rates.items():
            if rate < avg:
                items.append((acct, "below-avg pass rate", f"{rate:.1f}%"))
                if len(items) >= 5:
                    break

    # Add low-score programs
    if metrics.get("Training Name") and metrics.get("Assessment Score") and df["Training Name"].nunique() > 1:
        prog_scores = df.groupby("Training Name")["Assessment Score"].mean().sort_values()
        if prog_scores.max() <= 1:
            prog_scores = prog_scores * 100
        overall_avg = kpis.get("Avg Assessment Score", 0)
        for prog, score in prog_scores.items():
            if score < overall_avg - 10 and len(items) < 5:
                items.append((prog, "low avg score", f"{score:.1f}%"))

    return items


def generate_ai_insights(df, metrics, kpis):
    """Legacy wrapper — calls generate_executive_insights for backward compatibility."""
    # Determine view level from data
    n_countries = df["Country"].nunique() if "Country" in df.columns else 0
    if n_countries > 1:
        view_level = "regional"
    elif n_countries == 1:
        view_level = "market"
    else:
        view_level = "account"
    active_market = df["Country"].iloc[0] if n_countries == 1 and len(df) > 0 else None

    exec_insights = generate_executive_insights(df, metrics, kpis, view_level, active_market)
    # Convert to legacy format for any remaining consumers
    return [(status, headline + (f" {detail}" if detail else "")) for status, headline, detail in exec_insights]


def process_natural_query(question, df, metrics, kpis):
    """Process a natural language question about the training data and return a text answer."""
    q = question.strip().lower()
    answers = []

    # Helper: get column values for a dimension
    def get_dimension_values(dim_col):
        if dim_col in df.columns:
            return df[dim_col].dropna().unique().tolist()
        return []

    # Helper: detect which dimension/filter the user is asking about
    def detect_entity(q, dim_col):
        """Find if the user mentioned a specific value from a dimension column."""
        values = get_dimension_values(dim_col)
        for val in values:
            if str(val).lower() in q:
                return str(val)
        return None

    # Detect mentioned entities
    mentioned_country = detect_entity(q, "Country")
    mentioned_account = detect_entity(q, "Account")
    mentioned_trainer = detect_entity(q, "Trainer")
    mentioned_store = detect_entity(q, "Store")
    mentioned_training = detect_entity(q, "Training Name")

    # Build a filtered subset based on mentioned entities
    subset = df.copy()
    filter_desc = []
    if mentioned_country:
        subset = subset[subset["Country"].str.lower() == mentioned_country.lower()]
        filter_desc.append(f"Market: {mentioned_country}")
    if mentioned_account:
        subset = subset[subset["Account"].str.lower() == mentioned_account.lower()]
        filter_desc.append(f"Account: {mentioned_account}")
    if mentioned_trainer:
        subset = subset[subset["Trainer"].str.lower() == mentioned_trainer.lower()]
        filter_desc.append(f"Trainer: {mentioned_trainer}")
    if mentioned_store:
        subset = subset[subset["Store"].str.lower() == mentioned_store.lower()]
        filter_desc.append(f"Store: {mentioned_store}")
    if mentioned_training:
        subset = subset[subset["Training Name"].str.lower() == mentioned_training.lower()]
        filter_desc.append(f"Training: {mentioned_training}")

    if len(subset) == 0:
        return "No data found for the specified filters. Check spelling or try broader terms."

    filter_note = f"📍 Filtered to: {', '.join(filter_desc)}" if filter_desc else "📍 Showing: All data"

    # === QUESTION TYPE DETECTION ===

    # WHY questions (root cause analysis)
    is_why = any(w in q for w in ["why", "reason", "cause", "explain", "what's wrong", "what happened"])

    # COMPARISON questions
    is_compare = any(w in q for w in ["compare", "vs", "versus", "difference between", "compared to"])

    # RANKING questions
    is_ranking = any(w in q for w in ["top", "best", "worst", "bottom", "highest", "lowest", "rank", "ranking"])

    # COUNT / TOTAL questions
    is_count = any(w in q for w in ["how many", "total", "count", "number of"])

    # PASS RATE questions
    is_pass_rate = any(w in q for w in ["pass rate", "passing rate", "pass %", "passing", "fail", "failure"])

    # SCORE questions
    is_score = any(w in q for w in ["score", "average score", "avg score", "assessment"])

    # ATTACH RATE questions
    is_attach = any(w in q for w in ["attach", "attachment", "attach rate", "conversion"])

    # TRAINER questions
    is_trainer_q = any(w in q for w in ["trainer", "facilitator", "who trained"])

    # STORE questions
    is_store_q = any(w in q for w in ["store", "branch", "outlet", "location"])

    # === GENERATE ANSWERS ===

    # WHY analysis (dig into contributing factors)
    if is_why and is_pass_rate:
        answers.append(f"**🔍 Analysis: Why is the pass rate {'low' if 'low' in q else 'what it is'}?**")
        answers.append(filter_note)
        answers.append("")

        if "Pass Flag" in subset.columns:
            overall_rate = subset["Pass Flag"].mean() * 100
            answers.append(f"• Overall pass rate in this scope: **{overall_rate:.1f}%**")
            total_records = len(subset)
            passed = int(subset["Pass Flag"].sum())
            failed = total_records - passed
            answers.append(f"• {passed} passed, {failed} failed out of {total_records} records")
            answers.append("")

            # Break down by available dimensions
            if "Account" in subset.columns and subset["Account"].nunique() > 1:
                acct_rates = subset.groupby("Account")["Pass Flag"].agg(["mean", "count"]).reset_index()
                acct_rates["rate"] = (acct_rates["mean"] * 100).round(1)
                acct_rates = acct_rates.sort_values("rate", ascending=True)
                answers.append("**By Account (lowest first):**")
                for _, row in acct_rates.iterrows():
                    answers.append(f"  • {row['Account']}: {row['rate']}% ({int(row['count'])} records)")
                answers.append("")

            if "Trainer" in subset.columns and subset["Trainer"].nunique() > 1:
                trainer_rates = subset.groupby("Trainer")["Pass Flag"].agg(["mean", "count"]).reset_index()
                trainer_rates["rate"] = (trainer_rates["mean"] * 100).round(1)
                trainer_rates = trainer_rates.sort_values("rate", ascending=True)
                answers.append("**By Trainer (lowest first):**")
                for _, row in trainer_rates.head(5).iterrows():
                    answers.append(f"  • {row['Trainer']}: {row['rate']}% ({int(row['count'])} sessions)")
                answers.append("")

            if "Training Name" in subset.columns and subset["Training Name"].nunique() > 1:
                prog_rates = subset.groupby("Training Name")["Pass Flag"].agg(["mean", "count"]).reset_index()
                prog_rates["rate"] = (prog_rates["mean"] * 100).round(1)
                prog_rates = prog_rates.sort_values("rate", ascending=True)
                answers.append("**By Training Program (lowest first):**")
                for _, row in prog_rates.head(5).iterrows():
                    answers.append(f"  • {row['Training Name']}: {row['rate']}% ({int(row['count'])} learners)")
                answers.append("")

            if "Assessment Score" in subset.columns:
                scores = subset["Assessment Score"].dropna()
                if len(scores) > 0:
                    avg = scores.mean()
                    if avg <= 1:
                        avg *= 100
                        scores = scores * 100
                    answers.append(f"**Score Distribution:** Avg={avg:.1f}%, Min={scores.min():.0f}%, Max={scores.max():.0f}%")
                    below_60 = (scores < 60).sum()
                    if below_60 > 0:
                        answers.append(f"  ⚠️ {below_60} learners scored below 60%")

            answers.append("")
            answers.append("**💡 Possible causes:** Look at accounts/trainers with lowest rates above. "
                          "Consider content difficulty, trainer effectiveness, or learner preparation.")
        else:
            answers.append("Pass rate data not available in this dataset.")

    elif is_why and is_attach:
        answers.append("**🔍 Analysis: Attach Rate Performance**")
        answers.append(filter_note)
        answers.append("")
        if "Attach Rate Before" in subset.columns and "Attach Rate After" in subset.columns:
            before_vals = subset["Attach Rate Before"].dropna()
            after_vals = subset["Attach Rate After"].dropna()
            if len(before_vals) > 0 and len(after_vals) > 0:
                avg_before = before_vals.mean()
                avg_after = after_vals.mean()
                if avg_before <= 1:
                    avg_before *= 100
                    avg_after *= 100
                diff = avg_after - avg_before
                answers.append(f"• Before training: **{avg_before:.1f}%**")
                answers.append(f"• After training: **{avg_after:.1f}%**")
                answers.append(f"• Change: **{'+' if diff > 0 else ''}{diff:.1f}pp**")
                if diff < 0:
                    answers.append("")
                    answers.append("⚠️ Attach rate declined. Possible reasons: seasonal effects, "
                                  "insufficient sales follow-up, or training not translating to floor behavior.")
            else:
                answers.append("Insufficient attach rate data for analysis.")
        else:
            answers.append("Attach rate columns not available.")

    # RANKING questions
    elif is_ranking:
        answers.append(filter_note)
        answers.append("")

        is_bottom = any(w in q for w in ["worst", "bottom", "lowest"])
        n = 5  # default top/bottom count

        if is_pass_rate and "Pass Flag" in subset.columns:
            if is_trainer_q and "Trainer" in subset.columns:
                grouped = subset.groupby("Trainer")["Pass Flag"].agg(["mean", "count"]).reset_index()
                grouped["rate"] = (grouped["mean"] * 100).round(1)
                grouped = grouped.sort_values("rate", ascending=is_bottom).head(n)
                label = "Bottom" if is_bottom else "Top"
                answers.append(f"**{label} {n} Trainers by Pass Rate:**")
                for i, (_, row) in enumerate(grouped.iterrows(), 1):
                    answers.append(f"  {i}. {row['Trainer']} — {row['rate']}% ({int(row['count'])} sessions)")
            elif is_store_q and "Store" in subset.columns:
                grouped = subset.groupby("Store")["Pass Flag"].agg(["mean", "count"]).reset_index()
                grouped["rate"] = (grouped["mean"] * 100).round(1)
                grouped = grouped.sort_values("rate", ascending=is_bottom).head(n)
                label = "Bottom" if is_bottom else "Top"
                answers.append(f"**{label} {n} Stores by Pass Rate:**")
                for i, (_, row) in enumerate(grouped.iterrows(), 1):
                    answers.append(f"  {i}. {row['Store']} — {row['rate']}% ({int(row['count'])} records)")
            elif "Account" in subset.columns:
                grouped = subset.groupby("Account")["Pass Flag"].agg(["mean", "count"]).reset_index()
                grouped["rate"] = (grouped["mean"] * 100).round(1)
                grouped = grouped.sort_values("rate", ascending=is_bottom).head(n)
                label = "Bottom" if is_bottom else "Top"
                answers.append(f"**{label} {n} Accounts by Pass Rate:**")
                for i, (_, row) in enumerate(grouped.iterrows(), 1):
                    answers.append(f"  {i}. {row['Account']} — {row['rate']}% ({int(row['count'])} records)")
            elif "Country" in subset.columns:
                grouped = subset.groupby("Country")["Pass Flag"].agg(["mean", "count"]).reset_index()
                grouped["rate"] = (grouped["mean"] * 100).round(1)
                grouped = grouped.sort_values("rate", ascending=is_bottom).head(n)
                label = "Bottom" if is_bottom else "Top"
                answers.append(f"**{label} {n} Markets by Pass Rate:**")
                for i, (_, row) in enumerate(grouped.iterrows(), 1):
                    answers.append(f"  {i}. {row['Country']} — {row['rate']}% ({int(row['count'])} records)")
        elif is_score and "Assessment Score" in subset.columns:
            dim = "Account" if "Account" in subset.columns else "Country" if "Country" in subset.columns else None
            if dim:
                grouped = subset.groupby(dim)["Assessment Score"].mean().reset_index()
                grouped["Assessment Score"] = grouped["Assessment Score"].apply(lambda x: x * 100 if x <= 1 else x).round(1)
                grouped = grouped.sort_values("Assessment Score", ascending=is_bottom).head(n)
                label = "Bottom" if is_bottom else "Top"
                answers.append(f"**{label} {n} by Assessment Score ({dim}):**")
                for i, (_, row) in enumerate(grouped.iterrows(), 1):
                    answers.append(f"  {i}. {row[dim]} — {row['Assessment Score']}%")
        elif is_count:
            dim = "Account" if "Account" in subset.columns else "Country" if "Country" in subset.columns else None
            if dim:
                grouped = subset.groupby(dim).size().reset_index(name="Count")
                grouped = grouped.sort_values("Count", ascending=is_bottom).head(n)
                label = "Bottom" if is_bottom else "Top"
                answers.append(f"**{label} {n} by Training Volume ({dim}):**")
                for i, (_, row) in enumerate(grouped.iterrows(), 1):
                    answers.append(f"  {i}. {row[dim]} — {row['Count']:,} records")
        else:
            # Generic ranking by volume
            dim = "Account" if "Account" in subset.columns else "Country" if "Country" in subset.columns else None
            if dim:
                grouped = subset.groupby(dim).size().reset_index(name="Count")
                grouped = grouped.sort_values("Count", ascending=is_bottom).head(n)
                label = "Bottom" if is_bottom else "Top"
                answers.append(f"**{label} {n} by Volume ({dim}):**")
                for i, (_, row) in enumerate(grouped.iterrows(), 1):
                    answers.append(f"  {i}. {row[dim]} — {row['Count']:,} records")

    # COMPARISON questions
    elif is_compare:
        answers.append(filter_note)
        answers.append("")
        # Compare across countries or accounts
        if "Country" in subset.columns and subset["Country"].nunique() > 1:
            answers.append("**Market Comparison:**")
            compare_data = subset.groupby("Country").agg(
                records=("Country", "count"),
                **({} if "Pass Flag" not in subset.columns else {"pass_rate": ("Pass Flag", "mean")}),
                **({} if "Assessment Score" not in subset.columns else {"avg_score": ("Assessment Score", "mean")})
            ).reset_index()
            for _, row in compare_data.iterrows():
                line = f"  • **{row['Country']}**: {int(row['records']):,} records"
                if "pass_rate" in compare_data.columns:
                    line += f", Pass Rate: {row['pass_rate'] * 100:.1f}%"
                if "avg_score" in compare_data.columns:
                    score = row["avg_score"]
                    score = score * 100 if score <= 1 else score
                    line += f", Avg Score: {score:.1f}%"
                answers.append(line)
        elif "Account" in subset.columns and subset["Account"].nunique() > 1:
            answers.append("**Account Comparison:**")
            compare_data = subset.groupby("Account").agg(
                records=("Account", "count"),
                **({} if "Pass Flag" not in subset.columns else {"pass_rate": ("Pass Flag", "mean")})
            ).reset_index()
            for _, row in compare_data.iterrows():
                line = f"  • **{row['Account']}**: {int(row['records']):,} records"
                if "pass_rate" in compare_data.columns:
                    line += f", Pass Rate: {row['pass_rate'] * 100:.1f}%"
                answers.append(line)

    # PASS RATE questions (without why)
    elif is_pass_rate and "Pass Flag" in subset.columns:
        answers.append(filter_note)
        answers.append("")
        rate = subset["Pass Flag"].mean() * 100
        total = len(subset)
        passed = int(subset["Pass Flag"].sum())
        answers.append(f"**Pass Rate: {rate:.1f}%** ({passed}/{total} passed)")

        if "Country" in subset.columns and subset["Country"].nunique() > 1:
            answers.append("")
            answers.append("By Market:")
            by_country = subset.groupby("Country")["Pass Flag"].mean().sort_values(ascending=False)
            for country, rate_val in by_country.items():
                answers.append(f"  • {country}: {rate_val * 100:.1f}%")

    # SCORE questions
    elif is_score and "Assessment Score" in subset.columns:
        answers.append(filter_note)
        answers.append("")
        scores = subset["Assessment Score"].dropna()
        if len(scores) > 0:
            avg = scores.mean()
            if avg <= 1:
                avg *= 100
                scores = scores * 100
            answers.append(f"**Avg Assessment Score: {avg:.1f}%**")
            answers.append(f"  • Min: {scores.min():.0f}%, Max: {scores.max():.0f}%, Median: {scores.median():.0f}%")
            answers.append(f"  • Records with scores: {len(scores):,}")

    # ATTACH RATE questions
    elif is_attach:
        answers.append(filter_note)
        answers.append("")
        if "Attach Rate Before" in subset.columns and "Attach Rate After" in subset.columns:
            before_vals = subset["Attach Rate Before"].dropna()
            after_vals = subset["Attach Rate After"].dropna()
            if len(before_vals) > 0:
                avg_b = before_vals.mean()
                avg_a = after_vals.mean()
                if avg_b <= 1:
                    avg_b *= 100
                    avg_a *= 100
                answers.append(f"**Attach Rate Before:** {avg_b:.1f}%")
                answers.append(f"**Attach Rate After:** {avg_a:.1f}%")
                answers.append(f"**Improvement:** {'+' if (avg_a - avg_b) > 0 else ''}{avg_a - avg_b:.1f}pp")
            else:
                answers.append("No attach rate data available for this filter.")
        else:
            answers.append("Attach rate columns not found in the data.")

    # COUNT questions
    elif is_count:
        answers.append(filter_note)
        answers.append("")
        answers.append(f"**Total Records:** {len(subset):,}")
        if "Trainee Code" in subset.columns:
            answers.append(f"**Unique Learners:** {subset['Trainee Code'].nunique():,}")
        elif "Trainee Name" in subset.columns:
            answers.append(f"**Unique Learners:** {subset['Trainee Name'].nunique():,}")
        if "Training ID" in subset.columns:
            answers.append(f"**Sessions:** {subset['Training ID'].nunique():,}")
        if "Store" in subset.columns:
            answers.append(f"**Stores:** {subset['Store'].nunique():,}")
        if "Account" in subset.columns:
            answers.append(f"**Accounts:** {subset['Account'].nunique():,}")
        if "Country" in subset.columns:
            answers.append(f"**Markets:** {subset['Country'].nunique():,}")

    # TRAINER questions
    elif is_trainer_q and "Trainer" in subset.columns:
        answers.append(filter_note)
        answers.append("")
        trainer_data = subset.groupby("Trainer").agg(
            sessions=("Trainer", "count"),
            **({} if "Pass Flag" not in subset.columns else {"pass_rate": ("Pass Flag", "mean")})
        ).reset_index().sort_values("sessions", ascending=False)
        answers.append(f"**Trainers ({len(trainer_data)}):**")
        for _, row in trainer_data.iterrows():
            line = f"  • {row['Trainer']}: {int(row['sessions'])} sessions"
            if "pass_rate" in trainer_data.columns:
                line += f", Pass Rate: {row['pass_rate'] * 100:.1f}%"
            answers.append(line)

    # Generic summary (fallback)
    else:
        answers.append(filter_note)
        answers.append("")
        answers.append(f"**Summary for your query:**")
        answers.append(f"• Records: {len(subset):,}")
        if "Pass Flag" in subset.columns:
            answers.append(f"• Pass Rate: {subset['Pass Flag'].mean() * 100:.1f}%")
        if "Assessment Score" in subset.columns:
            avg = subset["Assessment Score"].dropna().mean()
            if avg <= 1:
                avg *= 100
            answers.append(f"• Avg Score: {avg:.1f}%")
        if "Country" in subset.columns:
            answers.append(f"• Markets: {', '.join(subset['Country'].dropna().unique().tolist())}")
        if "Account" in subset.columns:
            answers.append(f"• Accounts: {', '.join(subset['Account'].dropna().unique().tolist()[:10])}")
        answers.append("")
        answers.append("💡 *Try asking: 'Why is the pass rate low for [country]?', "
                      "'Top 5 stores by pass rate', 'Compare markets', "
                      "'How many trainees in PH?'*")

    return "\n".join(answers)


def generate_sample_data():
    """Generate sample training data mimicking the real format."""
    np.random.seed(42)
    n = 200

    countries = ["PH", "MY", "TH", "VN", "ID", "SG"]
    partners = ["Samsung", "TGDĐ", "Abenson", "AEON", "ALL IT", "Globe", "AeroPhone"]
    trainers = ["Benj Javier", "Huong Tran", "Andrea Cruz", "Mark Santos", "Lisa Tan"]
    stores = ["SM North EDSA", "SM Megamall", "Retailer - TGDĐ", "AEON Mall", "ALL IT HQ",
              "Globe Store Makati", "AeroPhone Cebu", "Mid Valley", "Central World",
              "Pavilion KL", "ION Orchard", "VivoCity", "Vincom Center"]
    titles = ["Samsung Care+ Foundation", "Device Protection 101", "New Device and SAMSUNG CARE+",
              "Gadget Xchange Masterclass", "bolttech Product Overview", "Sales Spiel Coaching",
              "Extended Warranty Deep Dive", "Screen Protection Workshop"]
    methods = ["Online", "Face-to-face", "Hybrid"]

    dates = pd.date_range(start="2025-01-01", end="2025-06-30", periods=n)

    df = pd.DataFrame({
        "Country": np.random.choice(countries, n),
        "Date of Training": dates,
        "Trainer Name": np.random.choice(trainers, n),
        "Training Title": np.random.choice(titles, n),
        "Training Method": np.random.choice(methods, n),
        "Store Name": np.random.choice(stores, n),
        "Trainee Code": [f"EMP{i:05d}" for i in np.random.randint(1000, 9999, n)],
        "Trainee Name": [f"Trainee_{i}" for i in range(n)],
        "Partner Name": np.random.choice(partners, n),
        "Training Assessment Score %": np.random.uniform(0.3, 1.0, n).round(2),
        "Pass Flag": np.random.choice([0.0, 1.0], n, p=[0.2, 0.8]),
    })

    df["Training ID"] = df["Country"] + "-" + df["Date of Training"].dt.strftime("%Y%m%d") + "-" + df["Training Title"].str[:20]
    df["Training Assessment Result"] = df["Pass Flag"].map({1.0: "Passed", 0.0: "Failed"})
    df["Fail Flag"] = 1.0 - df["Pass Flag"]

    df["Attach Rate Before"] = np.nan
    df["Attach Rate After"] = np.nan
    attach_idx = np.random.choice(n, 40, replace=False)
    df.loc[attach_idx, "Attach Rate Before"] = np.random.uniform(0.05, 0.20, 40).round(3)
    df.loc[attach_idx, "Attach Rate After"] = df.loc[attach_idx, "Attach Rate Before"] + np.random.uniform(0.01, 0.10, 40).round(3)

    return df


def compute_store_completion(df, duration_days=30, reference_date=None):
    """Compute store completion status within a given duration.
    
    A store is considered 'completed' if it has at least one training session
    within the specified duration window (from reference_date - duration_days to reference_date).
    
    Returns:
        dict with:
        - completed_stores: list of store names that have been trained
        - pending_stores: list of store names not yet trained in the window
        - total_stores: total unique stores in entire dataset
        - completed_count: number of completed stores
        - pending_count: number of pending stores
        - completion_rate: percentage of stores completed
        - store_details: DataFrame with per-store completion info
    """
    if "Store" not in df.columns or "Date" not in df.columns:
        return None
    
    if reference_date is None:
        reference_date = df["Date"].max()
    else:
        reference_date = pd.Timestamp(reference_date)
    
    start_date = reference_date - pd.Timedelta(days=duration_days)
    
    # All unique stores in the full dataset (the "universe" of stores to cover)
    all_stores = df["Store"].dropna().unique().tolist()
    
    # Stores that have training within the duration window
    window_df = df[(df["Date"] >= start_date) & (df["Date"] <= reference_date)]
    completed_stores = window_df["Store"].dropna().unique().tolist()
    
    # Pending stores = all stores minus completed ones
    pending_stores = [s for s in all_stores if s not in completed_stores]
    
    total = len(all_stores)
    completed_count = len(completed_stores)
    pending_count = len(pending_stores)
    completion_rate = round((completed_count / total * 100), 1) if total > 0 else 0.0
    
    # Build detail DataFrame
    store_details = []
    for store in all_stores:
        store_df = df[df["Store"] == store]
        window_store_df = window_df[window_df["Store"] == store]
        last_training = store_df["Date"].max()
        sessions_in_window = len(window_store_df)
        status = "✅ Completed" if store in completed_stores else "⏳ Pending"
        store_details.append({
            "Store": store,
            "Status": status,
            "Sessions in Window": sessions_in_window,
            "Last Training Date": last_training,
            "Days Since Last Training": (reference_date - last_training).days if pd.notna(last_training) else None
        })
    
    store_details_df = pd.DataFrame(store_details).sort_values("Status", ascending=False)
    
    return {
        "completed_stores": completed_stores,
        "pending_stores": pending_stores,
        "total_stores": total,
        "completed_count": completed_count,
        "pending_count": pending_count,
        "completion_rate": completion_rate,
        "store_details": store_details_df,
        "start_date": start_date,
        "end_date": reference_date,
    }


def render_kpi_card(label, value, delta=None, delta_type="neutral", size="primary", muted=False):
    """Render a styled KPI card. size='primary' or 'secondary'. muted=True for N/A values."""
    delta_html = ""
    if delta:
        css_class = delta_type if delta_type in ("positive", "negative") else ""
        delta_html = f'<div class="kpi-delta {css_class}">{delta}</div>'
    card_class = "kpi-card" if size == "primary" else "kpi-card-sm"
    if muted:
        card_class += " muted"
    return f"""
    <div class="{card_class}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """


# ====== MAIN APP ======

# Header row with title and data status
header_col1, header_col2 = st.columns([2, 1])
with header_col1:
    pass  # Dynamic title rendered after filters

# === DATA LOADING ===
MASTER_FILE = r"c:\Users\BenjJavier\OneDrive - bolttech\Documents\Copilot\Created\Asia Training Dashboard v1.xlsx"
MASTER_SHEET = "Raw_Data"
SALES_EXPORTS_FOLDER = r"c:\Users\BenjJavier\OneDrive - bolttech\Documents\Copilot\Created\Sales Exports"

# SharePoint URL for the master file (used as reference for trainers)
SHAREPOINT_URL = "https://bolttechio.sharepoint.com/:x:/s/SEATrainingSite/IQCmb4CztJcmTq5QCPy-h54KAbUdZARp7SWeZDL-c9frFnE"


def is_running_on_cloud():
    """Detect if we're running on Streamlit Cloud vs local machine."""
    import os
    # Streamlit Cloud runs on Linux; local dev is Windows
    return not os.path.exists(MASTER_FILE)


@st.cache_data(ttl=300)
def load_master_data():
    """Load the master training file from local OneDrive sync."""
    import os
    if not os.path.exists(MASTER_FILE):
        return None, "Master file not found."
    try:
        xls = pd.ExcelFile(MASTER_FILE)
        if MASTER_SHEET in xls.sheet_names:
            data = pd.read_excel(MASTER_FILE, sheet_name=MASTER_SHEET, dtype={"Trainee Code": str, "Store Code": str})
        else:
            data = pd.read_excel(MASTER_FILE, sheet_name=0)
        last_modified = datetime.fromtimestamp(os.path.getmtime(MASTER_FILE))
        return data, last_modified
    except PermissionError:
        return None, "File open in Excel. Close it or use 'Upload'."
    except Exception as e:
        return None, str(e)


def load_uploaded_file(uploaded_file):
    """Load data from an uploaded file."""
    try:
        if uploaded_file.name.endswith(".csv"):
            data = pd.read_csv(uploaded_file)
        else:
            xls = pd.ExcelFile(uploaded_file)
            if "Raw_Data" in xls.sheet_names:
                data = pd.read_excel(uploaded_file, sheet_name="Raw_Data")
            else:
                data = pd.read_excel(uploaded_file, sheet_name=0)
        # Fix mixed-type columns that cause Arrow serialization errors
        for col in data.columns:
            if data[col].dtype == object:
                # Convert object columns to string to avoid mixed-type issues
                data[col] = data[col].astype(str).replace("nan", pd.NA).replace("None", pd.NA)
        return data, None
    except Exception as e:
        return None, str(e)


# Initialize session state - smart default based on environment
if "data_source" not in st.session_state:
    if is_running_on_cloud():
        st.session_state.data_source = "� Upload Excel/CSV"
    else:
        st.session_state.data_source = "�📂 Auto-load Master File"

# Load data
df = None
data_status = ""

if st.session_state.data_source == "📂 Auto-load Master File":
    result = load_master_data()
    if result[0] is not None:
        df = result[0]
        last_modified = result[1]
        data_status = f"✅ {len(df):,} records · Updated {last_modified.strftime('%b %d, %I:%M %p')}"
    else:
        data_status = f"⚠️ {result[1]}"
        if is_running_on_cloud():
            data_status = "📎 Upload the master file from SharePoint to get started"
        else:
            df = generate_sample_data()
            data_status += " (using demo data)"
elif st.session_state.data_source == "🎯 Use Demo Data":
    df = generate_sample_data()
    data_status = f"✅ Demo data ({len(df)} records)"
elif st.session_state.data_source == "📎 Upload Excel/CSV":
    # Handled in sidebar — check session state for uploaded data
    if "uploaded_df" in st.session_state and st.session_state.uploaded_df is not None:
        df = st.session_state.uploaded_df
        data_status = f"✅ {len(df):,} records (uploaded)"
    else:
        data_status = "📎 Upload the master file to get started"

# Show data status in header
with header_col2:
    st.markdown(f"<div style='text-align:right; padding-top:12px; font-size:0.68rem; color:#6B7280 !important; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{data_status}</div>", unsafe_allow_html=True)


# === MAIN CONTENT WITH SIDEBAR FILTERS ===
if df is not None and len(df) > 0:
    df = normalize_columns(df)
    metrics = detect_metrics(df)

    # Normalize Training Type values (consolidate inconsistent entries)
    if "Training Type" in df.columns:
        training_type_map = {
            "virtual/online": "Virtual/Online",
            "online": "Virtual/Online",
            "virtual": "Virtual/Online",
            "face to face": "Face to Face",
            "tatap muka/offline": "Face to Face",
            "tatap muka / offline": "Face to Face",
            "offline": "Face to Face",
            "f2f": "Face to Face",
        }
        df["Training Type"] = df["Training Type"].apply(
            lambda x: training_type_map.get(str(x).strip().lower(), x) if pd.notna(x) else x
        )

    # Coerce numeric columns upfront to prevent TypeError in all downstream .agg() calls
    numeric_cols = ["Pass Flag", "Fail Flag", "Assessment Score", "Attach Rate Before",
                    "Attach Rate After", "Attach Lift", "Training Hours",
                    "Total Invited", "Total Attended", "Total Passed"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Parse dates
    if metrics.get("Date"):
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"])

    # ─── SIDEBAR FILTERS ───
    with st.sidebar:
        st.markdown('<div class="sidebar-title">Filters</div>', unsafe_allow_html=True)

        # Date range
        if metrics.get("Date") and len(df) > 0:
            from datetime import date as _date, timedelta
            min_date = df["Date"].min().date()
            max_date = df["Date"].max().date()
            today = _date.today()

            # Preset date range options
            date_presets = {
                "Year to Date (2026)": (_date(2026, 1, 1), today),
                "This Month": (_date(today.year, today.month, 1), today),
                "Last 30 Days": (today - timedelta(days=30), today),
                "Last 90 Days": (today - timedelta(days=90), today),
                "This Quarter": (_date(today.year, ((today.month - 1) // 3) * 3 + 1, 1), today),
                "Last 6 Months": (today - timedelta(days=180), today),
                "This Year": (_date(today.year, 1, 1), today),
                "All Time": (min_date, max_date),
                "Custom": None,
            }

            selected_preset = st.selectbox(
                "Date Range",
                options=list(date_presets.keys()),
                index=0
            )

            if selected_preset == "Custom":
                date_range = st.date_input("Select range", value=(_date(2026, 1, 1), max_date),
                                           min_value=min_date, max_value=max_date)
                if len(date_range) == 2:
                    df = df[(df["Date"].dt.date >= date_range[0]) & (df["Date"].dt.date <= date_range[1])]
            else:
                start, end = date_presets[selected_preset]
                # Clamp to available data range
                start = max(start, min_date)
                end = min(end, max_date)
                st.caption(f"{start.strftime('%Y/%m/%d')} – {end.strftime('%Y/%m/%d')}")
                df = df[(df["Date"].dt.date >= start) & (df["Date"].dt.date <= end)]

        # Country / Market
        if metrics.get("Country") and len(df) > 0:
            country_opts = ["All"] + sorted(df["Country"].dropna().unique().tolist())
            sel_countries = st.selectbox("Market", options=country_opts, index=0)
            if sel_countries != "All":
                df = df[df["Country"] == sel_countries]

        # Account / Partner
        if metrics.get("Account") and len(df) > 0:
            acct_opts = ["All"] + sorted(df["Account"].dropna().unique().tolist())
            sel_account = st.selectbox("Account / Partner", options=acct_opts, index=0)
            if sel_account != "All":
                df = df[df["Account"] == sel_account]

        # Training Name
        if metrics.get("Training Name") and len(df) > 0:
            training_opts = ["All"] + sorted(df["Training Name"].dropna().unique().tolist())
            sel_training = st.selectbox("Training Name", options=training_opts, index=0)
            if sel_training != "All":
                df = df[df["Training Name"] == sel_training]

        # Trainer
        if metrics.get("Trainer") and len(df) > 0:
            trainer_opts = ["All"] + sorted(df["Trainer"].dropna().unique().tolist())
            sel_trainer = st.selectbox("Trainer", options=trainer_opts, index=0)
            if sel_trainer != "All":
                df = df[df["Trainer"] == sel_trainer]

        # Training Type / Method
        if metrics.get("Training Type") and len(df) > 0:
            type_opts = ["All"] + sorted(df["Training Type"].dropna().unique().tolist())
            sel_type = st.selectbox("Training Type", options=type_opts, index=0)
            if sel_type != "All":
                df = df[df["Training Type"] == sel_type]

        # Store
        if metrics.get("Store") and len(df) > 0:
            store_opts = ["All"] + sorted(df["Store"].dropna().unique().tolist())
            sel_store = st.selectbox("Store", options=store_opts, index=0)
            if sel_store != "All":
                df = df[df["Store"] == sel_store]

        # Filtered count
        st.markdown(f"""
        <div style="background:#F3F4F6; border-radius:8px; padding:8px 12px; text-align:center; margin:12px 0;">
            <span style="font-size:1.1rem; font-weight:700; color:#0891B2;">{len(df):,}</span>
            <span style="color:#6B7280; font-size:0.75rem;"> records</span>
        </div>
        """, unsafe_allow_html=True)


    # Recompute after filtering
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)

    # ─── DYNAMIC TITLE & BREADCRUMB ───
    COUNTRY_NAMES = {
        "PH": "Philippines", "MY": "Malaysia", "TH": "Thailand",
        "VN": "Vietnam", "ID": "Indonesia", "SG": "Singapore",
        "HK": "Hong Kong", "TW": "Taiwan", "KR": "South Korea",
        "JP": "Japan", "IN": "India", "BD": "Bangladesh",
    }
    # Determine view level
    _active_market = None
    _active_account = None
    try:
        if sel_countries and sel_countries != "All":
            _active_market = sel_countries
    except NameError:
        pass
    try:
        if sel_account and sel_account != "All":
            _active_account = sel_account
    except NameError:
        pass

    if _active_market:
        market_full = COUNTRY_NAMES.get(_active_market, _active_market)
        dash_title = f"{market_full} Training Dashboard"
        dash_subtitle = "Market Training Performance"
    else:
        dash_title = "Asia Training Dashboard"
        dash_subtitle = "Regional Training Performance"

    # Breadcrumb
    crumbs = ["Asia"]
    if _active_market:
        crumbs.append(COUNTRY_NAMES.get(_active_market, _active_market))
    if _active_account:
        crumbs.append(_active_account)
    breadcrumb_html = '<span class="sep">›</span>'.join(f"<span>{c}</span>" for c in crumbs)

    st.markdown(f'<p class="breadcrumb">{breadcrumb_html}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="dash-title">{dash_title}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="dash-subtitle">{dash_subtitle}</p>', unsafe_allow_html=True)

    # ─── COMPACT HEADER CHIPS (replaces hero banner) ───
    # Summary chips: dynamic context about the current view
    chips = []
    if metrics.get("Date") and len(df) > 0:
        date_min = df["Date"].min().strftime("%b %d")
        date_max = df["Date"].max().strftime("%b %d, %Y")
        chips.append(f"{date_min} – {date_max}")
    if metrics.get("Training Name"):
        n_programs = df["Training Name"].nunique()
        chips.append(f"{n_programs} Programs")
    if metrics.get("Account"):
        n_accounts = df["Account"].nunique()
        chips.append(f"{n_accounts} Partners")
    if metrics.get("Country"):
        n_countries = df["Country"].nunique()
        chips.append(f"{n_countries} Markets")
    chips.append(f"{len(df):,} records")

    chips_html = "".join(f'<span class="chip">{c}</span>' for c in chips)
    st.markdown(f'<div class="chip-row">{chips_html}</div>', unsafe_allow_html=True)

    # Active filter chips — only show meaningful non-default selections
    filter_chips = []
    try:
        if selected_preset and selected_preset not in ("Year to Date (2026)", "All Time"):
            filter_chips.append(("Date", selected_preset))
    except NameError:
        pass
    try:
        if sel_countries and sel_countries != "All":
            filter_chips.append(("Market", sel_countries))
    except NameError:
        pass
    try:
        if sel_account and sel_account != "All":
            filter_chips.append(("Partner", sel_account))
    except NameError:
        pass
    try:
        if sel_training and sel_training != "All":
            filter_chips.append(("Training", sel_training))
    except NameError:
        pass
    try:
        if sel_trainer and sel_trainer != "All":
            filter_chips.append(("Trainer", sel_trainer))
    except NameError:
        pass
    try:
        if sel_type and sel_type != "All":
            filter_chips.append(("Type", sel_type))
    except NameError:
        pass

    if filter_chips:
        active_chips_html = "".join(
            f'<span class="chip active">{label}: {val}</span>' for label, val in filter_chips
        )
        st.markdown(f'<div class="chip-row">{active_chips_html}</div>', unsafe_allow_html=True)

    # ─── EXECUTIVE KPI SUMMARY (top of page, big numbers) ───

    # Compute view context for KPI relative comparisons
    _n_countries = df["Country"].nunique() if "Country" in df.columns else 0

    # Row 1: The 5 things executives care about most
    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)

    with kpi_col1:
        val = f"{kpis.get('Total Sessions', 0):,}"
        st.markdown(render_kpi_card("Trainings Done", val, "total sessions conducted"), unsafe_allow_html=True)

    with kpi_col2:
        val = f"{kpis.get('Unique Learners', kpis.get('Total Participants', 0)):,}"
        st.markdown(render_kpi_card("Frontliners Trained", val, "unique individuals"), unsafe_allow_html=True)

    with kpi_col3:
        stores_val = f"{kpis.get('Stores', 0):,}" if "Stores" in kpis else "N/A"
        st.markdown(render_kpi_card("Stores Trained", stores_val), unsafe_allow_html=True)

    with kpi_col4:
        val = f"{kpis.get('Pass Rate', 'N/A')}%" if "Pass Rate" in kpis else "N/A"
        delta_type = "positive" if kpis.get("Pass Rate", 0) >= 80 else "negative" if kpis.get("Pass Rate", 0) < 70 else "neutral"
        # Relative context: vs scope average or ranking
        delta = None
        if "Pass Rate" in kpis:
            rate = kpis["Pass Rate"]
            if _n_countries > 1 and metrics.get("Country") and metrics.get("Pass Flag"):
                # Regional view — show if highest/lowest
                mkt_rates = df.groupby("Country")["Pass Flag"].mean() * 100
                if len(mkt_rates) > 1:
                    if rate >= mkt_rates.max():
                        delta = "highest in region"
                        delta_type = "positive"
                    elif rate <= mkt_rates.min():
                        delta = "lowest in region"
                        delta_type = "negative"
                    else:
                        delta = f"{kpis.get('Total Passed', 0):,} passed"
                else:
                    delta = f"{kpis.get('Total Passed', 0):,} passed"
            else:
                delta = f"{kpis.get('Total Passed', 0):,} passed" if "Total Passed" in kpis else None
        st.markdown(render_kpi_card("Passing Rate", val, delta, delta_type), unsafe_allow_html=True)

    with kpi_col5:
        val = f"{kpis.get('Avg Assessment Score', 'N/A')}%" if "Avg Assessment Score" in kpis else "N/A"
        delta_type = "positive" if kpis.get("Avg Assessment Score", 0) >= 75 else "negative" if kpis.get("Avg Assessment Score", 0) < 60 else "neutral"
        delta = "avg assessment score"
        st.markdown(render_kpi_card("Product Knowledge", val, delta, delta_type), unsafe_allow_html=True)

    # Row 2: Secondary metrics (smaller cards)
    sec_col1, sec_col2, sec_col3, sec_col4, sec_col5 = st.columns(5)

    with sec_col1:
        if "Avg Attach Before" in kpis:
            val = f"{kpis['Avg Attach Before']}%"
            is_muted = kpis['Avg Attach Before'] == 0
        else:
            val = "N/A"
            is_muted = True
        st.markdown(render_kpi_card("Attach Before", val, "pre-training", size="secondary", muted=is_muted), unsafe_allow_html=True)

    with sec_col2:
        if "Avg Attach After" in kpis:
            val = f"{kpis['Avg Attach After']}%"
            imp = kpis.get("Attach Improvement", 0)
            delta = f"+{imp}pp" if imp > 0 else f"{imp}pp"
            delta_type = "positive" if imp > 0 else "negative" if imp < 0 else "neutral"
            is_muted = False
        else:
            val = "N/A"
            delta = "post-training"
            delta_type = "neutral"
            is_muted = True
        st.markdown(render_kpi_card("Attach After", val, delta, delta_type, size="secondary", muted=is_muted), unsafe_allow_html=True)

    with sec_col3:
        val = f"{kpis.get('Countries', 0)}"
        st.markdown(render_kpi_card("Markets", val, size="secondary"), unsafe_allow_html=True)

    with sec_col4:
        val = f"{kpis.get('Accounts', 0)}"
        st.markdown(render_kpi_card("Partners", val, size="secondary"), unsafe_allow_html=True)

    with sec_col5:
        if metrics.get("Training Type") and len(df) > 0:
            # Count actual unique sessions per training type
            if metrics.get("Training ID"):
                method_sessions = df.groupby("Training Type")["Training ID"].nunique().sort_values(ascending=False)
            else:
                # Use combo of Date + Training Name + Trainer as session key
                session_cols = ["Training Type"]
                if metrics.get("Date"):
                    session_cols.append("Date")
                if metrics.get("Training Name"):
                    session_cols.append("Training Name")
                if metrics.get("Trainer"):
                    session_cols.append("Trainer")
                if len(session_cols) > 1:
                    method_sessions = df.groupby(session_cols).ngroups  # total — need per-type
                    method_sessions = df.groupby("Training Type").apply(
                        lambda g: g.drop_duplicates(subset=session_cols[1:]).shape[0]
                    ).sort_values(ascending=False)
                else:
                    method_sessions = df["Training Type"].value_counts()
            top_method = method_sessions.index[0] if len(method_sessions) > 0 else "N/A"
            val = top_method
            delta = f"{method_sessions.iloc[0]:,} sessions"
            st.markdown(render_kpi_card("Top Method", val, delta, size="secondary"), unsafe_allow_html=True)
        elif "Total Training Hours" in kpis:
            val = f"{kpis['Total Training Hours']:,.0f}"
            st.markdown(render_kpi_card("Training Hours", val, size="secondary"), unsafe_allow_html=True)
        else:
            val = f"{len(df):,}"
            st.markdown(render_kpi_card("Total Records", val, "in filtered view", size="secondary"), unsafe_allow_html=True)


    # ─── ACCOUNT BREAKDOWN (when a specific market is selected) ───
    selected_market = None
    try:
        if metrics.get("Country") and sel_countries != "All":
            selected_market = sel_countries
    except NameError:
        pass
    if not selected_market and metrics.get("Country") and df["Country"].nunique() == 1:
        selected_market = df["Country"].iloc[0]

    if selected_market and metrics.get("Account") and len(df) > 0 and df["Account"].nunique() > 1:
        st.markdown("---")
        _market_full_name = COUNTRY_NAMES.get(selected_market, selected_market)
        st.markdown(f'<div class="section-header">{_market_full_name} — Account Breakdown</div>', unsafe_allow_html=True)

        # Training Name filter for the account breakdown
        breakdown_df = df.copy()
        if metrics.get("Training Name") and len(df) > 0:
            training_options = ["All Trainings"] + sorted(df["Training Name"].dropna().unique().tolist())
            sel_breakdown_training = st.selectbox(
                "Filter by Training Program",
                options=training_options,
                index=0,
                key="breakdown_training_filter"
            )
            if sel_breakdown_training != "All Trainings":
                breakdown_df = df[df["Training Name"] == sel_breakdown_training]
                st.caption(f"Showing data for: **{sel_breakdown_training}**")
        else:
            sel_breakdown_training = "All Trainings"

        # Build per-account summary
        # Count actual unique sessions, not rows
        # A unique session = unique combination of Date + Training Name + Trainer (or Training ID if available)
        if metrics.get("Training ID"):
            acct_breakdown_agg = {"Trainings": ("Training ID", "nunique")}
        else:
            # Create a synthetic session key from available fields
            session_key_parts = []
            if metrics.get("Date"):
                session_key_parts.append(breakdown_df["Date"].astype(str))
            if metrics.get("Training Name"):
                session_key_parts.append(breakdown_df["Training Name"].astype(str))
            if metrics.get("Trainer"):
                session_key_parts.append(breakdown_df["Trainer"].astype(str))
            if session_key_parts:
                breakdown_df = breakdown_df.copy()
                breakdown_df["_session_key"] = session_key_parts[0]
                for part in session_key_parts[1:]:
                    breakdown_df["_session_key"] = breakdown_df["_session_key"] + "|" + part
                acct_breakdown_agg = {"Trainings": ("_session_key", "nunique")}
            else:
                acct_breakdown_agg = {"Trainings": ("Account", "count")}

        if metrics.get("Trainee Code"):
            acct_breakdown_agg["Frontliners"] = ("Trainee Code", "nunique")
        elif metrics.get("Trainee Name"):
            acct_breakdown_agg["Frontliners"] = ("Trainee Name", "nunique")
        if metrics.get("Store"):
            acct_breakdown_agg["Stores"] = ("Store", "nunique")
        if metrics.get("Pass Flag") and "Pass Flag" in breakdown_df.columns:
            acct_breakdown_agg["Pass Rate"] = ("Pass Flag", "mean")
        if metrics.get("Assessment Score") and "Assessment Score" in breakdown_df.columns:
            acct_breakdown_agg["Avg Score"] = ("Assessment Score", "mean")
        if metrics.get("Attach Rate Before") and "Attach Rate Before" in breakdown_df.columns:
            acct_breakdown_agg["AR Before"] = ("Attach Rate Before", "mean")
        if metrics.get("Attach Rate After") and "Attach Rate After" in breakdown_df.columns:
            acct_breakdown_agg["AR After"] = ("Attach Rate After", "mean")

        acct_breakdown = breakdown_df.groupby("Account").agg(**acct_breakdown_agg).reset_index()

        # If Frontliners is 0 but we don't have trainee data, show N/A instead of a fake number
        # (don't fallback to row count — it's misleading)

        # Format percentages
        if "Pass Rate" in acct_breakdown.columns:
            acct_breakdown["Pass Rate"] = (acct_breakdown["Pass Rate"] * 100).round(1)
        if "Avg Score" in acct_breakdown.columns:
            scores = acct_breakdown["Avg Score"]
            acct_breakdown["Avg Score"] = (scores * 100 if scores.max() <= 1 else scores).round(1)
        if "AR Before" in acct_breakdown.columns:
            if acct_breakdown["AR Before"].max() <= 1:
                acct_breakdown["AR Before"] = (acct_breakdown["AR Before"] * 100).round(1)
        if "AR After" in acct_breakdown.columns:
            if acct_breakdown["AR After"].max() <= 1:
                acct_breakdown["AR After"] = (acct_breakdown["AR After"] * 100).round(1)
        if "AR Before" in acct_breakdown.columns and "AR After" in acct_breakdown.columns:
            acct_breakdown["AR Lift (pp)"] = (acct_breakdown["AR After"] - acct_breakdown["AR Before"]).round(1)

        acct_breakdown = acct_breakdown.sort_values("Trainings", ascending=False)

        # Display as KPI cards per account (top 6)
        top_accounts = acct_breakdown.head(6)
        acct_card_cols = st.columns(min(len(top_accounts), 3))

        # Compute market average for comparison context
        _mkt_avg_pass = acct_breakdown["Pass Rate"].mean() if "Pass Rate" in acct_breakdown.columns else None
        _pass_rank = acct_breakdown.sort_values("Pass Rate", ascending=False).reset_index(drop=True) if "Pass Rate" in acct_breakdown.columns else None

        for i, (_, row) in enumerate(top_accounts.iterrows()):
            with acct_card_cols[i % 3]:
                acct_name = row["Account"]
                trainings = int(row["Trainings"])

                # Ranking badge
                rank_badge = ""
                if _pass_rank is not None and len(_pass_rank) > 1:
                    rank_pos = _pass_rank[_pass_rank["Account"] == acct_name].index
                    if len(rank_pos) > 0:
                        pos = rank_pos[0] + 1
                        if pos == 1:
                            rank_badge = '<span style="font-size:0.6rem;background:#ECFDF5;color:#10B981;padding:2px 6px;border-radius:100px;font-weight:600;margin-left:6px;">#1 Pass Rate</span>'
                        elif pos == len(_pass_rank):
                            rank_badge = '<span style="font-size:0.6rem;background:#FEF2F2;color:#EF4444;padding:2px 6px;border-radius:100px;font-weight:600;margin-left:6px;">Lowest</span>'

                parts = [f"<strong style='font-size:0.95rem;'>{acct_name}</strong>{rank_badge}", f"📋 {trainings:,} trainings"]
                if "Frontliners" in row and row["Frontliners"] > 0:
                    parts.append(f"👥 {int(row['Frontliners']):,} frontliners")
                else:
                    # No unique trainee data — count rows as participants trained
                    acct_participants = len(breakdown_df[breakdown_df["Account"] == acct_name])
                    parts.append(f"👥 {acct_participants:,} participants")
                if "Stores" in row:
                    parts.append(f"🏪 {int(row['Stores']):,} stores")
                if "Pass Rate" in row and pd.notna(row["Pass Rate"]):
                    rate = row["Pass Rate"]
                    color = "#10B981" if rate >= 80 else "#EF4444" if rate < 70 else "#F59E0B"
                    vs_avg = ""
                    if _mkt_avg_pass is not None and len(acct_breakdown) > 1:
                        diff = round(rate - _mkt_avg_pass, 1)
                        if diff > 0:
                            vs_avg = f' <span style="font-size:0.7rem;color:#10B981;">+{diff} vs avg</span>'
                        elif diff < 0:
                            vs_avg = f' <span style="font-size:0.7rem;color:#EF4444;">{diff} vs avg</span>'
                    parts.append(f'<span style="color:{color};font-weight:600;">{rate:.1f}%</span> pass rate{vs_avg}')
                if "Avg Score" in row and pd.notna(row["Avg Score"]):
                    parts.append(f"📝 {row['Avg Score']:.1f}% avg score")
                if "AR Lift (pp)" in row and pd.notna(row["AR Lift (pp)"]):
                    lift = row["AR Lift (pp)"]
                    sign = "+" if lift > 0 else ""
                    color = "#2ecc71" if lift > 0 else "#e74c3c"
                    parts.append(f'📈 <span style="color:{color};font-weight:600;">{sign}{lift:.1f}pp</span> attach lift')

                # Show trainers for this account (leaderboard style)
                if metrics.get("Trainer"):
                    acct_df = breakdown_df[breakdown_df["Account"] == acct_name]
                    # Count unique sessions per trainer (by Training ID or Date)
                    if metrics.get("Training ID"):
                        acct_trainer_counts = acct_df.groupby("Trainer")["Training ID"].nunique().sort_values(ascending=False)
                    elif metrics.get("Date"):
                        acct_trainer_counts = acct_df.groupby("Trainer")["Date"].nunique().sort_values(ascending=False)
                    else:
                        acct_trainer_counts = acct_df["Trainer"].dropna().value_counts()

                    if len(acct_trainer_counts) > 0:
                        top_trainers = acct_trainer_counts.head(5)
                        medals = ["🥇", "🥈", "🥉", "4.", "5."]
                        trainer_lines = ""
                        for rank, (trainer, count) in enumerate(top_trainers.items()):
                            trainer_lines += f'<div style="display:flex;justify-content:space-between;align-items:center;padding:2px 0;"><span>{medals[rank]} {trainer}</span><span style="opacity:0.6;font-size:0.75rem;">{int(count)} sessions</span></div>'
                        # Expandable section for remaining trainers
                        suffix = ""
                        if len(acct_trainer_counts) > 5:
                            remaining = acct_trainer_counts.iloc[5:]
                            remaining_lines = ""
                            for rank_offset, (trainer, count) in enumerate(remaining.items(), start=6):
                                remaining_lines += f'<div style="display:flex;justify-content:space-between;align-items:center;padding:2px 0;"><span>{rank_offset}. {trainer}</span><span style="opacity:0.6;font-size:0.75rem;">{int(count)} sessions</span></div>'
                            suffix = f'<details style="margin-top:4px;cursor:pointer;"><summary style="opacity:0.6;font-size:0.7rem;list-style:none;">▸ +{len(remaining)} more trainers</summary>{remaining_lines}</details>'
                        parts.append(f'<div style="margin-top:4px;border-top:1px solid rgba(0,186,199,0.15);padding-top:6px;"><span style="font-size:0.75rem;opacity:0.6;">TRAINERS</span>{trainer_lines}{suffix}</div>')

                st.markdown(f"""
                <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:12px; padding:16px; margin-bottom:10px; min-height:320px; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                    {"<br>".join(parts)}
                </div>
                """, unsafe_allow_html=True)

        # Full table below cards
        col_config_acct = {}
        if "Pass Rate" in acct_breakdown.columns:
            col_config_acct["Pass Rate"] = st.column_config.ProgressColumn("Pass Rate %", min_value=0, max_value=100, format="%.1f%%")

        st.dataframe(acct_breakdown, use_container_width=True, height=250, column_config=col_config_acct)


    # ─── TABBED CONTENT SECTIONS ───
    st.markdown("---")

    tab_overview, tab_performance, tab_trends, tab_data = st.tabs([
        "Overview", "Performance", "Trends", "Data & Export"
    ])

    # === TAB 1: OVERVIEW & INSIGHTS ===
    with tab_overview:
        # Determine view level for insights
        _n_countries = df["Country"].nunique() if "Country" in df.columns else 0
        if _n_countries > 1:
            _view_level = "regional"
        elif _n_countries == 1:
            _view_level = "market"
        else:
            _view_level = "account"
        _insight_market = df["Country"].iloc[0] if _n_countries == 1 and len(df) > 0 else None

        # Executive Insights
        exec_insights = generate_executive_insights(df, metrics, kpis, _view_level, _insight_market)
        if exec_insights:
            st.markdown('<div class="section-header">Key Insights</div>', unsafe_allow_html=True)
            cols = st.columns(2)
            for i, (status, headline, detail) in enumerate(exec_insights):
                with cols[i % 2]:
                    st.markdown(render_insight_card(status, headline, detail), unsafe_allow_html=True)

        # Training Method Comparison
        if metrics.get("Training Type") and metrics.get("Pass Flag") and df["Training Type"].nunique() > 1:
            st.markdown('<div class="section-header">Training Method Comparison</div>', unsafe_allow_html=True)
            method_comp = df.groupby("Training Type").agg(
                sessions=("Training Type", "count"),
                pass_rate=("Pass Flag", "mean")
            ).reset_index()
            method_comp["pass_rate"] = (method_comp["pass_rate"] * 100).round(1)
            method_comp = method_comp.sort_values("pass_rate", ascending=False)
            for _, row in method_comp.iterrows():
                st.markdown(f"""
                <div class="method-row">
                    <span class="method-name">{row["Training Type"]}</span>
                    <span class="method-stat">{row["sessions"]:,} records</span>
                    <span class="method-rate">{row["pass_rate"]}%</span>
                </div>
                """, unsafe_allow_html=True)

        # Needs Attention
        attention_items = generate_needs_attention(df, metrics, kpis, _view_level)
        if attention_items:
            st.markdown('<div class="section-header">Needs Attention</div>', unsafe_allow_html=True)
            items_html = "".join(
                f'<div class="attention-item"><span class="attention-rank">{i}.</span><span class="attention-text">{entity} — {reason}</span><span class="attention-metric">{metric_str}</span></div>'
                for i, (entity, reason, metric_str) in enumerate(attention_items, 1)
            )
            st.markdown(f'<div class="attention-list">{items_html}</div>', unsafe_allow_html=True)

        # Ask the Data section
        st.markdown("")
        st.markdown('<div class="section-header">Ask the Data</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="insight-box">
        Ask questions about your training data in plain English. Examples:<br>
        • "Why do we have a low passing rate for Vietnam?"<br>
        • "Top 5 stores by pass rate"<br>
        • "Compare markets"<br>
        • "What's the pass rate for Samsung?"<br>
        • "How many trainees in PH?"
        </div>
        """, unsafe_allow_html=True)

        # Chat history in session state
        if "ask_history" not in st.session_state:
            st.session_state.ask_history = []

        # Display chat history
        for entry in st.session_state.ask_history:
            st.markdown(f"**🧑 You:** {entry['question']}")
            st.markdown(entry["answer"])
            st.markdown("---")

        # Input
        user_question = st.text_input("💬 Ask a question about your data:",
                                       placeholder="e.g., Compare markets by pass rate",
                                       key="nlq_input")

        ask_col1, ask_col2 = st.columns([1, 5])
        with ask_col1:
            ask_btn = st.button("Ask", type="primary", use_container_width=True)
        with ask_col2:
            if st.button("Clear History", use_container_width=False):
                st.session_state.ask_history = []
                st.rerun()

        if ask_btn and user_question:
            answer = process_natural_query(user_question, df, metrics, kpis)
            st.session_state.ask_history.append({
                "question": user_question,
                "answer": answer
            })
            st.rerun()

        # Quick-ask buttons for common questions
        st.markdown("")
        st.markdown("**Quick questions:**")
        quick_col1, quick_col2, quick_col3 = st.columns(3)
        with quick_col1:
            if st.button("📊 Overall pass rate", use_container_width=True, key="quick_pass"):
                answer = process_natural_query("What is the overall pass rate?", df, metrics, kpis)
                st.session_state.ask_history.append({"question": "What is the overall pass rate?", "answer": answer})
                st.rerun()
        with quick_col2:
            if st.button("🌏 Compare markets", use_container_width=True, key="quick_compare"):
                answer = process_natural_query("Compare all markets", df, metrics, kpis)
                st.session_state.ask_history.append({"question": "Compare all markets", "answer": answer})
                st.rerun()
        with quick_col3:
            if st.button("🏆 Top accounts", use_container_width=True, key="quick_top"):
                answer = process_natural_query("Top 5 accounts by pass rate", df, metrics, kpis)
                st.session_state.ask_history.append({"question": "Top 5 accounts by pass rate", "answer": answer})
                st.rerun()

        quick_col4, quick_col5, quick_col6 = st.columns(3)
        with quick_col4:
            if st.button("👤 Trainer breakdown", use_container_width=True, key="quick_trainer"):
                answer = process_natural_query("Show me trainer performance", df, metrics, kpis)
                st.session_state.ask_history.append({"question": "Show me trainer performance", "answer": answer})
                st.rerun()
        with quick_col5:
            if st.button("📈 Attach rate impact", use_container_width=True, key="quick_attach"):
                answer = process_natural_query("What is the attach rate improvement?", df, metrics, kpis)
                st.session_state.ask_history.append({"question": "What is the attach rate improvement?", "answer": answer})
                st.rerun()
        with quick_col6:
            if st.button("📋 Data summary", use_container_width=True, key="quick_summary"):
                answer = process_natural_query("How many total records and learners?", df, metrics, kpis)
                st.session_state.ask_history.append({"question": "How many total records and learners?", "answer": answer})
                st.rerun()

        # ─── TRAINING TYPE BREAKDOWN (Foundation / Activation / Reinforcement / Champion) ───
        st.markdown("")
        if metrics.get("Training Type") and len(df) > 0:
            st.markdown('<div class="section-header">Training Type Breakdown</div>', unsafe_allow_html=True)

            type_data = df["Training Type"].value_counts().reset_index()
            type_data.columns = ["Type", "Sessions"]
            type_data["% of Total"] = (type_data["Sessions"] / type_data["Sessions"].sum() * 100).round(1)

            # Color map for known training types
            type_colors = {
                "Foundation": "#170F4F",
                "Activation": "#00BAC7",
                "Reinforcement": "#FFB74D",
                "Champion": "#2ecc71",
            }

            type_cols = st.columns(len(type_data) if len(type_data) <= 5 else 5)
            for i, (_, row) in enumerate(type_data.head(5).iterrows()):
                with type_cols[i]:
                    color = type_colors.get(row["Type"], "#00BAC7")
                    st.markdown(f"""
                    <div class="kpi-card" style="border-left: 4px solid {color};">
                        <div class="kpi-label">{row["Type"]}</div>
                        <div class="kpi-value" style="color: {color};">{row["Sessions"]:,}</div>
                        <div class="kpi-delta">{row["% of Total"]}% of trainings</div>
                    </div>
                    """, unsafe_allow_html=True)

            # Donut chart for visual breakdown
            st.markdown("")
            type_chart_col1, type_chart_col2 = st.columns([1, 1])
            with type_chart_col1:
                colors = [type_colors.get(t, "#99E4E8") for t in type_data["Type"]]
                fig = px.pie(type_data, values="Sessions", names="Type",
                             color_discrete_sequence=colors, hole=0.5)
                fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0),
                                  legend=dict(orientation="h", yanchor="bottom", y=-0.2))
                fig.update_traces(textinfo="label+percent", textposition="outside")
                st.plotly_chart(fig, use_container_width=True)

            with type_chart_col2:
                # Training Type with pass rate if available
                if metrics.get("Pass Flag"):
                    type_perf = df.groupby("Training Type").agg(
                        sessions=("Training Type", "count"),
                        pass_rate=("Pass Flag", "mean")
                    ).reset_index()
                    type_perf["Pass Rate (%)"] = (type_perf["pass_rate"] * 100).round(1)
                    type_perf = type_perf.sort_values("sessions", ascending=False)

                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=type_perf["Training Type"], y=type_perf["sessions"],
                        name="Sessions", marker_color="#a5b4fc", opacity=0.8, yaxis="y"
                    ))
                    fig.add_trace(go.Scatter(
                        x=type_perf["Training Type"], y=type_perf["Pass Rate (%)"],
                        name="Pass Rate %", mode="markers+lines",
                        marker=dict(size=10, color="#00BAC7"), line=dict(color="#00BAC7", width=2),
                        yaxis="y2"
                    ))
                    fig.update_layout(
                        height=280, margin=dict(l=0, r=0, t=10, b=0),
                        yaxis=dict(title="Sessions", showgrid=False),
                        yaxis2=dict(title="Pass Rate (%)", overlaying="y", side="right", range=[0, 100]),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        xaxis_title=""
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    fig = px.bar(type_data, x="Type", y="Sessions", color_discrete_sequence=["#00BAC7"])
                    fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0),
                                      xaxis_title="", yaxis_title="Sessions")
                    st.plotly_chart(fig, use_container_width=True)

        # ─── TRAINING NAMES SUMMARY TABLE ───
        if metrics.get("Training Name") and len(df) > 0:
            st.markdown('<div class="section-header">Training Programs Summary</div>', unsafe_allow_html=True)

            training_agg = {"Sessions": ("Training Name", "count")}
            if metrics.get("Pass Flag"):
                training_agg["Pass Rate (%)"] = ("Pass Flag", "mean")
            if metrics.get("Assessment Score"):
                training_agg["Avg Score"] = ("Assessment Score", "mean")
            if metrics.get("Trainee Code"):
                training_agg["Learners"] = ("Trainee Code", "nunique")
            elif metrics.get("Trainee Name"):
                training_agg["Learners"] = ("Trainee Name", "nunique")
            if metrics.get("Store"):
                training_agg["Stores"] = ("Store", "nunique")

            groupby_training = ["Training Name"]
            if metrics.get("Training Type"):
                groupby_training = ["Training Name", "Training Type"]

            training_summary = df.groupby(groupby_training).agg(**training_agg).reset_index()

            if "Pass Rate (%)" in training_summary.columns:
                training_summary["Pass Rate (%)"] = (training_summary["Pass Rate (%)"] * 100).round(1)
            if "Avg Score" in training_summary.columns:
                scores = training_summary["Avg Score"]
                training_summary["Avg Score"] = (scores * 100 if scores.max() <= 1 else scores).round(1)

            training_summary = training_summary.sort_values("Sessions", ascending=False)

            col_config_training = {}
            if "Pass Rate (%)" in training_summary.columns:
                col_config_training["Pass Rate (%)"] = st.column_config.ProgressColumn(
                    "Pass Rate %", min_value=0, max_value=100, format="%.1f%%"
                )

            st.dataframe(training_summary, use_container_width=True, height=300, column_config=col_config_training)

        # ─── ATTACH RATE IMPACT (30 Days Post-Training) ───
        if metrics.get("Attach Rate Before") and metrics.get("Attach Rate After") and len(df) > 0:
            st.markdown('<div class="section-header">Attach Rate Impact — 30 Days Post-Training</div>', unsafe_allow_html=True)
            st.markdown("""
            <div class="insight-box">
            Attach Rate data sourced from Power BI, measured 30 days after training delivery.
            Shows whether training translates to actual sales behavior change at the store level.
            </div>
            """, unsafe_allow_html=True)

            attach_df = df[df["Attach Rate Before"].notna() & df["Attach Rate After"].notna()]
            if len(attach_df) > 0:
                attach_viz1, attach_viz2 = st.columns([2, 1])

                with attach_viz1:
                    # Group by Training Name or Account for the chart
                    group_col = "Training Name" if metrics.get("Training Name") else "Account" if metrics.get("Account") else None
                    if group_col:
                        attach_grouped = attach_df.groupby(group_col).agg(
                            before=("Attach Rate Before", "mean"),
                            after=("Attach Rate After", "mean"),
                            n=("Attach Rate Before", "count")
                        ).reset_index()
                        if attach_grouped["before"].max() <= 1:
                            attach_grouped["before"] = (attach_grouped["before"] * 100).round(1)
                            attach_grouped["after"] = (attach_grouped["after"] * 100).round(1)
                        attach_grouped["Improvement"] = (attach_grouped["after"] - attach_grouped["before"]).round(1)
                        attach_grouped = attach_grouped.sort_values("Improvement", ascending=False)

                        fig = go.Figure()
                        fig.add_trace(go.Bar(
                            name="Before Training", x=attach_grouped[group_col], y=attach_grouped["before"],
                            marker_color="#a5b4fc", opacity=0.7
                        ))
                        fig.add_trace(go.Bar(
                            name="After Training (30d)", x=attach_grouped[group_col], y=attach_grouped["after"],
                            marker_color="#00BAC7", opacity=0.9
                        ))
                        fig.update_layout(
                            barmode="group", height=320, margin=dict(l=0, r=0, t=10, b=0),
                            yaxis_title="Attach Rate (%)", xaxis_title="",
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                        )
                        st.plotly_chart(fig, use_container_width=True)

                with attach_viz2:
                    st.markdown("**Improvement Ranking**")
                    if group_col and len(attach_grouped) > 0:
                        for _, row in attach_grouped.iterrows():
                            imp = row["Improvement"]
                            color = "positive" if imp > 0 else "negative"
                            sign = "+" if imp > 0 else ""
                            st.markdown(
                                f'<span class="{color}"><b>{sign}{imp:.1f}pp</b></span> — {row[group_col]} ({int(row["n"])} stores)',
                                unsafe_allow_html=True
                            )
            else:
                st.info("No attach rate data available for the current filter selection.")

        # ─── MARKET BREAKDOWN ───
        st.markdown("")
        overview_col1, overview_col2 = st.columns(2)

        if metrics.get("Country"):
            with overview_col1:
                st.markdown('<div class="section-header">Training by Market</div>', unsafe_allow_html=True)
                country_data = df["Country"].value_counts().reset_index()
                country_data.columns = ["Country", "Records"]
                fig = px.pie(country_data, values="Records", names="Country",
                             color_discrete_sequence=["#00BAC7", "#33C8D2", "#66D6DD", "#99E4E8", "#CCF2F3", "#E6F9FA"],
                             hole=0.45)
                fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0),
                                  legend=dict(orientation="h", yanchor="bottom", y=-0.2))
                st.plotly_chart(fig, use_container_width=True)

        if metrics.get("Account"):
            with overview_col2:
                st.markdown('<div class="section-header">Training by Partner</div>', unsafe_allow_html=True)
                acct_data_overview = df["Account"].value_counts().reset_index()
                acct_data_overview.columns = ["Account", "Records"]
                fig = px.bar(acct_data_overview.head(10), x="Records", y="Account", orientation="h",
                             color_discrete_sequence=["#00BAC7"])
                fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0),
                                  yaxis_title="", xaxis_title="Sessions")
                st.plotly_chart(fig, use_container_width=True)


    # === TAB 2: PERFORMANCE ===
    with tab_performance:
        perf_col1, perf_col2 = st.columns(2)

        # Pass Rate by Account
        if metrics.get("Account") and metrics.get("Pass Flag"):
            with perf_col1:
                st.markdown('<div class="section-header">Pass Rate by Account</div>', unsafe_allow_html=True)
                acct_data = df.groupby("Account")["Pass Flag"].agg(["sum", "count"]).reset_index()
                acct_data["Pass Rate (%)"] = (acct_data["sum"] / acct_data["count"] * 100).round(1)
                acct_data = acct_data.sort_values("Pass Rate (%)", ascending=False)

                for _, row in acct_data.iterrows():
                    account = row["Account"]
                    rate = row["Pass Rate (%)"]
                    total = int(row["count"])
                    passed = int(row["sum"])
                    initial = account[0].upper() if account else "?"

                    if rate >= 80:
                        bar_color = "#00BAC7"
                    elif rate >= 60:
                        bar_color = "#FFB74D"
                    else:
                        bar_color = "#e74c3c"

                    st.markdown(f"""
                    <div class="account-card">
                        <div style="width:32px;height:32px;min-width:32px;border-radius:6px;background:#00BAC7;color:white;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;">{initial}</div>
                        <div style="flex:1;">
                            <div class="name">{account}</div>
                            <div class="bar-bg">
                                <div style="background:{bar_color}; border-radius:4px; height:8px; width:{min(rate, 100)}%;"></div>
                            </div>
                        </div>
                        <div style="text-align:right; min-width:55px;">
                            <div style="font-weight:700; color:{bar_color}; font-size:1.1rem;">{rate:.0f}%</div>
                            <div style="font-size:0.65rem; opacity:0.5;">{passed}/{total}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)


        # Trainer Performance
        if metrics.get("Trainer") and metrics.get("Pass Flag"):
            with perf_col2:
                st.markdown('<div class="section-header">Trainer Performance</div>', unsafe_allow_html=True)
                t_data = df.groupby("Trainer").agg(
                    sessions=("Date", "count"),
                    pass_rate=("Pass Flag", "mean")
                ).reset_index()
                t_data["Pass Rate (%)"] = (t_data["pass_rate"] * 100).round(1)
                t_data = t_data.sort_values("Pass Rate (%)", ascending=False)

                # Show top 15 as horizontal bar chart
                top_trainers = t_data.head(15)
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    y=top_trainers["Trainer"],
                    x=top_trainers["Pass Rate (%)"],
                    orientation="h",
                    marker_color="#0891B2",
                    text=[f"{r:.0f}% · {s:,} sessions" for r, s in zip(top_trainers["Pass Rate (%)"], top_trainers["sessions"])],
                    textposition="auto",
                    textfont=dict(size=10),
                ))
                fig.update_layout(
                    height=max(250, len(top_trainers) * 28),
                    margin=dict(l=0, r=10, t=5, b=5),
                    xaxis=dict(title="Pass Rate (%)", range=[0, 105], showgrid=True, gridcolor="#F3F4F6"),
                    yaxis=dict(title="", autorange="reversed", tickfont=dict(size=11)),
                    plot_bgcolor="#FFFFFF",
                )
                st.plotly_chart(fig, use_container_width=True)

                # Expandable full trainer table
                if len(t_data) > 15:
                    with st.expander(f"View all {len(t_data)} trainers"):
                        st.dataframe(
                            t_data[["Trainer", "Pass Rate (%)", "sessions"]].rename(columns={"sessions": "Sessions"}),
                            use_container_width=True, height=300
                        )

        # Attach Rate Comparison
        if metrics.get("Attach Rate Before") and metrics.get("Attach Rate After") and metrics.get("Account"):
            st.markdown('<div class="section-header">Attach Rate: Before vs After Training</div>', unsafe_allow_html=True)

            attach_df = df[df["Attach Rate Before"].notna() & df["Attach Rate After"].notna()]
            if len(attach_df) > 0:
                attach_col1, attach_col2 = st.columns([2, 1])

                with attach_col1:
                    attach_data = attach_df.groupby("Account").agg(
                        before=("Attach Rate Before", "mean"),
                        after=("Attach Rate After", "mean")
                    ).reset_index()
                    if attach_data["before"].max() <= 1:
                        attach_data["before"] = attach_data["before"] * 100
                        attach_data["after"] = attach_data["after"] * 100
                    attach_data["Improvement"] = attach_data["after"] - attach_data["before"]
                    attach_data = attach_data.sort_values("Improvement", ascending=False)

                    fig = go.Figure()
                    fig.add_trace(go.Bar(name="Before", x=attach_data["Account"], y=attach_data["before"],
                                         marker_color="#a5b4fc", opacity=0.7))
                    fig.add_trace(go.Bar(name="After", x=attach_data["Account"], y=attach_data["after"],
                                         marker_color="#00BAC7", opacity=0.9))
                    fig.update_layout(barmode="group", height=320, margin=dict(l=0, r=0, t=10, b=0),
                                      yaxis_title="Attach Rate (%)",
                                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    st.plotly_chart(fig, use_container_width=True)

                with attach_col2:
                    st.markdown("**Improvement Ranking**")
                    for _, row in attach_data.iterrows():
                        imp = row["Improvement"]
                        color = "positive" if imp > 0 else "negative"
                        sign = "+" if imp > 0 else ""
                        st.markdown(f'<span class="{color}"><b>{sign}{imp:.1f}pp</b></span> — {row["Account"]}',
                                    unsafe_allow_html=True)


        # Store Performance Table
        if metrics.get("Store") and (metrics.get("Pass Flag") or metrics.get("Assessment Score")):
            st.markdown('<div class="section-header">Store Performance</div>', unsafe_allow_html=True)

            store_col1, store_col2 = st.columns([3, 1])

            with store_col1:
                store_agg = {"Records": ("Store", "count")}
                if metrics.get("Pass Flag") and "Pass Flag" in df.columns:
                    store_agg["Pass Rate"] = ("Pass Flag", "mean")
                if metrics.get("Assessment Score") and "Assessment Score" in df.columns:
                    store_agg["Avg Score"] = ("Assessment Score", "mean")
                if metrics.get("Attach Rate Before") and "Attach Rate Before" in df.columns:
                    store_agg["Attach Before"] = ("Attach Rate Before", "mean")
                if metrics.get("Attach Rate After") and "Attach Rate After" in df.columns:
                    store_agg["Attach After"] = ("Attach Rate After", "mean")

                groupby_cols = ["Store"] + (["Account"] if metrics.get("Account") and "Account" in df.columns else [])
                store_data = df.groupby(groupby_cols).agg(**store_agg).reset_index()

                if "Pass Rate" in store_data.columns:
                    store_data["Pass Rate"] = (store_data["Pass Rate"] * 100).round(1)
                if "Avg Score" in store_data.columns:
                    scores = store_data["Avg Score"]
                    store_data["Avg Score"] = (scores * 100 if scores.max() <= 1 else scores).round(1)
                if "Attach Before" in store_data.columns:
                    if store_data["Attach Before"].max() <= 1:
                        store_data["Attach Before"] = (store_data["Attach Before"] * 100).round(1)
                        if "Attach After" in store_data.columns:
                            store_data["Attach After"] = (store_data["Attach After"] * 100).round(1)
                if "Attach Before" in store_data.columns and "Attach After" in store_data.columns:
                    store_data["Improvement (pp)"] = (store_data["Attach After"] - store_data["Attach Before"]).round(1)

                sort_col = "Pass Rate" if "Pass Rate" in store_data.columns else "Records"
                store_data = store_data.sort_values(sort_col, ascending=False)

                col_config = {}
                if "Pass Rate" in store_data.columns:
                    col_config["Pass Rate"] = st.column_config.ProgressColumn("Pass Rate %", min_value=0, max_value=100, format="%.1f%%")

                st.dataframe(store_data, use_container_width=True, height=350, column_config=col_config)

            with store_col2:
                st.metric("Stores Trained", df["Store"].nunique())
                if "Pass Rate" in store_data.columns:
                    st.markdown("**🏆 Top 5**")
                    for _, row in store_data.nlargest(5, "Pass Rate").iterrows():
                        st.markdown(f'• {row["Store"]} — **{row["Pass Rate"]:.0f}%**')
                    st.markdown("**⚠️ Needs Attention**")
                    for _, row in store_data.nsmallest(3, "Pass Rate").iterrows():
                        st.markdown(f'• {row["Store"]} — **{row["Pass Rate"]:.0f}%**')


        # Store Completion Tracker
        if metrics.get("Store") and metrics.get("Date"):
            st.markdown('<div class="section-header">Store Completion Tracker</div>', unsafe_allow_html=True)
            st.markdown("""
            <div class="insight-box">
            Track how many stores have been trained within a chosen time window. 
            <b>Completed</b> = at least one training session within the period. <b>Pending</b> = no training yet in that window.
            </div>
            """, unsafe_allow_html=True)

            comp_col1, comp_col2 = st.columns([1, 1])
            with comp_col1:
                duration_days = st.slider("📅 Duration window (days)", min_value=7, max_value=180, value=30, step=7,
                                          help="How many days back from the reference date to check for store visits")
            with comp_col2:
                max_date = df["Date"].max().date()
                min_date = df["Date"].min().date()
                ref_date = st.date_input("📌 Reference date (end of window)", value=max_date,
                                         min_value=min_date, max_value=max_date,
                                         help="The end date of the measurement window")

            completion = compute_store_completion(df, duration_days=duration_days, reference_date=ref_date)

            if completion:
                # KPI row
                comp_kpi1, comp_kpi2, comp_kpi3, comp_kpi4 = st.columns(4)
                with comp_kpi1:
                    st.markdown(render_kpi_card("Total Stores", str(completion["total_stores"])), unsafe_allow_html=True)
                with comp_kpi2:
                    delta_type = "positive" if completion["completion_rate"] >= 70 else "negative" if completion["completion_rate"] < 50 else "neutral"
                    st.markdown(render_kpi_card("Completed", str(completion["completed_count"]),
                                               f"{completion['completion_rate']}%", delta_type), unsafe_allow_html=True)
                with comp_kpi3:
                    delta_type = "negative" if completion["pending_count"] > completion["completed_count"] else "neutral"
                    st.markdown(render_kpi_card("Pending", str(completion["pending_count"]),
                                               f"{100 - completion['completion_rate']}% remaining", delta_type), unsafe_allow_html=True)
                with comp_kpi4:
                    st.markdown(render_kpi_card("Window",
                                               f"{duration_days}d",
                                               f"{completion['start_date'].strftime('%b %d')} → {completion['end_date'].strftime('%b %d')}"),
                                unsafe_allow_html=True)

                # Visual: donut chart + detail table
                comp_viz1, comp_viz2 = st.columns([1, 2])

                with comp_viz1:
                    fig_donut = go.Figure(data=[go.Pie(
                        labels=["Completed", "Pending"],
                        values=[completion["completed_count"], completion["pending_count"]],
                        hole=0.6,
                        marker_colors=["#00BAC7", "#e74c3c"],
                        textinfo="label+value",
                        textfont_size=13
                    )])
                    fig_donut.update_layout(
                        height=280,
                        margin=dict(l=10, r=10, t=10, b=10),
                        showlegend=False,
                        annotations=[dict(text=f"{completion['completion_rate']}%", x=0.5, y=0.5,
                                          font_size=24, font_color="#00BAC7", showarrow=False)]
                    )
                    st.plotly_chart(fig_donut, use_container_width=True)

                with comp_viz2:
                    detail_df = completion["store_details"].copy()
                    detail_df["Last Training Date"] = pd.to_datetime(detail_df["Last Training Date"]).dt.strftime("%b %d, %Y")
                    col_config = {
                        "Sessions in Window": st.column_config.NumberColumn("Sessions", format="%d"),
                        "Days Since Last Training": st.column_config.NumberColumn("Days Since", format="%d days"),
                    }
                    st.dataframe(detail_df, use_container_width=True, height=280, column_config=col_config)

                # Show pending stores list if any
                if completion["pending_stores"]:
                    with st.expander(f"⏳ View {completion['pending_count']} Pending Stores", expanded=False):
                        pending_cols = st.columns(3)
                        for i, store in enumerate(sorted(completion["pending_stores"])):
                            with pending_cols[i % 3]:
                                st.markdown(f"• {store}")
            else:
                st.warning("Store and Date columns are required for completion tracking.")


    # === TAB 3: TRENDS ===
    with tab_trends:
        if metrics.get("Date"):
            st.markdown('<div class="section-header">Training Volume Over Time</div>', unsafe_allow_html=True)
            # NOTE: This chart counts ROWS per week (each row = one trainee attendance record),
            # NOT unique training sessions. The headline "Trainings Done" KPI uses unique
            # Date+TrainingName+Trainer combos. This discrepancy is documented — the trend
            # shows participation volume (records), not session count.
            df_trend = df.set_index("Date").resample("W").size().reset_index(name="Records")
            fig = px.line(df_trend, x="Date", y="Records", color_discrete_sequence=["#0891B2"])
            fig.update_traces(line=dict(width=2.5))
            fig.update_layout(
                height=260, margin=dict(l=0, r=0, t=5, b=0),
                xaxis=dict(title="", tickformat="%b %d", showgrid=False),
                yaxis=dict(title="Records per Week", showgrid=True, gridcolor="#F3F4F6"),
                plot_bgcolor="#FFFFFF",
            )
            st.plotly_chart(fig, use_container_width=True)

        # Country trend over time — small multiples for readability
        if metrics.get("Date") and metrics.get("Country") and df["Country"].nunique() > 1:
            st.markdown('<div class="section-header">Training Volume by Market</div>', unsafe_allow_html=True)
            country_trend = df.groupby([pd.Grouper(key="Date", freq="W"), "Country"]).size().reset_index(name="Records")
            # Map to full names for legend
            country_trend["Market"] = country_trend["Country"].map(lambda c: COUNTRY_NAMES.get(c, c))

            fig = px.line(country_trend, x="Date", y="Records", color="Market",
                          color_discrete_sequence=["#0891B2", "#6366F1", "#F59E0B", "#10B981", "#EF4444", "#8B5CF6"])
            fig.update_traces(line=dict(width=2))
            fig.update_layout(
                height=280, margin=dict(l=0, r=0, t=5, b=0),
                xaxis=dict(title="", tickformat="%b %d", showgrid=False),
                yaxis=dict(title="Records per Week", showgrid=True, gridcolor="#F3F4F6"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
                plot_bgcolor="#FFFFFF",
            )
            st.plotly_chart(fig, use_container_width=True)

        # Pass rate trend
        if metrics.get("Date") and metrics.get("Pass Flag"):
            st.markdown('<div class="section-header">Pass Rate Trend</div>', unsafe_allow_html=True)
            pass_trend = df.set_index("Date").resample("W")["Pass Flag"].mean().reset_index()
            pass_trend["Pass Rate (%)"] = (pass_trend["Pass Flag"] * 100).round(1)
            fig = px.line(pass_trend, x="Date", y="Pass Rate (%)", color_discrete_sequence=["#0891B2"])
            fig.update_traces(line=dict(width=2.5))
            fig.add_hline(y=80, line_dash="dash", line_color="rgba(16,185,129,0.5)", annotation_text="Target: 80%")
            fig.update_layout(
                height=250, margin=dict(l=0, r=0, t=5, b=0),
                xaxis=dict(title="", tickformat="%b %d", showgrid=False),
                yaxis=dict(title="Pass Rate (%)", range=[0, 105], showgrid=True, gridcolor="#F3F4F6"),
                plot_bgcolor="#FFFFFF",
            )
            st.plotly_chart(fig, use_container_width=True)


    # === TAB 4: DATA & EXPORT ===
    with tab_data:
        data_col1, data_col2 = st.columns([3, 1])

        with data_col1:
            st.markdown('<div class="section-header">Raw Data</div>', unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True, height=400)

        with data_col2:
            st.markdown('<div class="section-header">Export</div>', unsafe_allow_html=True)
            st.download_button("📄 Download CSV", df.to_csv(index=False), "training_data.csv", "text/csv",
                               use_container_width=True)
            buf = BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as w:
                df.to_excel(w, index=False, sheet_name="Data")
            st.download_button("📊 Download Excel", buf.getvalue(), "training_dashboard.xlsx",
                              "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                              use_container_width=True)

            st.markdown("---")
            st.markdown('<div class="section-header">Data Availability</div>', unsafe_allow_html=True)

            metric_groups = {
                "Core": ["Date", "Trainer", "Account", "Country", "Store", "Training Name", "Training Type", "Training ID"],
                "Learner": ["Trainee Name", "Trainee Code", "Assessment Score", "Assessment Result", "Pass Flag"],
                "Optional": ["Total Invited", "Total Attended", "Training Hours", "Attach Rate Before", "Attach Rate After"],
            }

            for group, fields in metric_groups.items():
                st.markdown(f"**{group}**")
                for field in fields:
                    present = metrics.get(field, False)
                    icon = "✅" if present else "❌"
                    color = "data-avail-present" if present else "data-avail-missing"
                    st.markdown(f'<span class="{color}">{icon} {field}</span>', unsafe_allow_html=True)
                st.markdown("")

            st.markdown(f"**{len(df):,}** rows · **{len(df.columns)}** columns")


# === SIDEBAR: Data Source & Sales (inside expanders below filters) ===
with st.sidebar:
    st.markdown("---")

    # On cloud: show upload prominently. On local: show as expander.
    if is_running_on_cloud():
        st.markdown("### 📎 Load Data")
        st.markdown("""
        <div style="background:rgba(0,186,199,0.08); border-radius:8px; padding:10px 12px; margin-bottom:12px; font-size:0.8rem; border:1px solid rgba(0,186,199,0.2);">
            📁 Upload the master file from SharePoint:<br>
            <b>SEA Training Site → Global Documents → Training Dashboard Masterfile</b>
        </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader("Upload Master File", type=["xlsx", "csv"], key="main_upload")
        if uploaded_file:
            data, error = load_uploaded_file(uploaded_file)
            if data is not None:
                st.session_state.uploaded_df = data
                st.session_state.data_source = "📎 Upload Excel/CSV"
                st.success(f"✅ Loaded {len(data):,} records")
                st.rerun()
            else:
                st.error(f"Error: {error}")

        st.markdown("---")
        with st.expander("Other options", expanded=False):
            if st.button("🎯 Use Demo Data", use_container_width=True):
                st.session_state.data_source = "🎯 Use Demo Data"
                st.rerun()
    else:
        with st.expander("⚙️ Data Source", expanded=False):
            _options = ["📂 Auto-load Master File", " Upload Excel/CSV", "🎯 Use Demo Data"]
            _current = st.session_state.data_source if st.session_state.data_source in _options else _options[0]
            data_source = st.radio(
                "Choose input:",
                _options,
                index=_options.index(_current),
                key="data_source_radio"
            )

            if data_source != st.session_state.data_source:
                st.session_state.data_source = data_source
                st.rerun()

            if data_source == "📂 Auto-load Master File":
                if st.button("🔄 Refresh Data", use_container_width=True):
                    st.cache_data.clear()
                    st.rerun()

            elif data_source == "📎 Upload Excel/CSV":
                uploaded_file = st.file_uploader("Upload your file", type=["xlsx", "csv"])
                if uploaded_file:
                    data, error = load_uploaded_file(uploaded_file)
                    if data is not None:
                        st.session_state.uploaded_df = data
                        st.success(f"Loaded {len(data):,} records")
                        st.rerun()
                    else:
                        st.error(f"Error: {error}")

    with st.expander("📊 Sales Data (Attach Rate)", expanded=False):
        import os
        if os.path.exists(SALES_EXPORTS_FOLDER):
            sales_df, sales_status = load_sales_exports(SALES_EXPORTS_FOLDER)
            if sales_df is not None and len(sales_df) > 0:
                st.success(sales_status)
                threshold = st.slider("Match sensitivity", 50, 100, 70, 5)
                if st.button("🔗 Match & Calculate Attach Rates", use_container_width=True):
                    with st.spinner("Fuzzy matching stores..."):
                        df, match_report = match_sales_to_training(df, sales_df, match_threshold=threshold)
                    if len(match_report) > 0:
                        matched_count = (match_report["Status"] == "✅ Matched").sum()
                        st.success(f"Matched {matched_count}/{len(match_report)} stores")
                        st.dataframe(match_report, use_container_width=True)
            else:
                st.warning(sales_status)
        else:
            if not is_running_on_cloud():
                st.info("Sales folder not configured.")

        sales_upload = st.file_uploader("Upload sales data:", type=["xlsx", "csv"], key="sales_file")
        if sales_upload:
            try:
                if sales_upload.name.endswith(".csv"):
                    sales_df = pd.read_csv(sales_upload)
                else:
                    sales_df = pd.read_excel(sales_upload)
                sales_df = normalize_columns(sales_df)
                st.success(f"Sales: {len(sales_df):,} rows")
                threshold = st.slider("Match sensitivity", 50, 100, 70, 5, key="manual_threshold")
                if st.button("🔗 Match & Calculate", key="manual_match", use_container_width=True):
                    with st.spinner("Fuzzy matching..."):
                        df, match_report = match_sales_to_training(df, sales_df, match_threshold=threshold)
                    if len(match_report) > 0:
                        matched_count = (match_report["Status"] == "✅ Matched").sum()
                        st.success(f"Matched {matched_count}/{len(match_report)} stores")
            except Exception as e:
                st.error(f"Error: {e}")


# === NO DATA STATE ===
if df is None or len(df) == 0:
    st.markdown("---")
    if is_running_on_cloud():
        st.markdown(f"""
        ### 📎 Upload Your Training Data

        **To get started:**
        1. Go to [SharePoint → SEA Training Site → Global Documents → Training Dashboard Masterfile]({SHAREPOINT_URL})
        2. Download `Asia Training Dashboard v1.xlsx`
        3. Upload it using the sidebar on the left

        The dashboard will automatically detect your columns and populate all metrics.

        ---
        *Or click "Use Demo Data" in the sidebar to explore with sample data.*
        """)
    else:
        st.info("👈 Use the sidebar filters and data source to get started.")
        st.markdown("""
        ### 📋 Getting Started

        This dashboard **auto-detects** your columns. Upload any Excel/CSV with training data.

        **Key fields recognized:** Date, Trainer, Account, Country, Store, Training Name,
        Assessment Score, Pass/Fail, Attach Rate, Training Hours, and more.
        """)
