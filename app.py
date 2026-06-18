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

# Custom CSS - theme-aware design that works in both light and dark mode
st.markdown("""
<style>
    .main-header {
        font-size: 1.8rem;
        font-weight: 700;
        color: #00BAC7;
        margin-bottom: 0.2rem;
        font-family: 'Segoe UI', sans-serif;
    }
    .sub-header {
        font-size: 0.85rem;
        opacity: 0.5;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Additional CSS for executive layout - theme-aware
st.markdown("""
<style>
    /* KPI Cards - use CSS variables for theme awareness */
    .kpi-card {
        background: var(--background-color, rgba(255,255,255,0.05));
        border-radius: 12px;
        padding: 20px 16px;
        text-align: center;
        border: 1px solid rgba(0,186,199,0.3);
        height: 100%;
    }
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #00BAC7;
        line-height: 1.1;
        margin: 8px 0 4px;
    }
    .kpi-label {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        opacity: 0.8;
        font-weight: 600;
        color: inherit;
    }
    .kpi-delta {
        font-size: 0.75rem;
        margin-top: 4px;
        opacity: 0.7;
        color: inherit;
    }
    .kpi-delta.positive { color: #2ecc71; font-weight: 600; opacity: 1; }
    .kpi-delta.negative { color: #e74c3c; font-weight: 600; opacity: 1; }

    /* Insight boxes - theme-aware */
    .insight-box {
        background: rgba(0,186,199,0.1);
        border-radius: 8px;
        padding: 12px 16px;
        border-left: 3px solid #00BAC7;
        margin: 6px 0;
        color: inherit;
        font-size: 0.9rem;
    }
    .warning-box {
        background: rgba(243,156,18,0.1);
        border-radius: 8px;
        padding: 12px 16px;
        border-left: 3px solid #f39c12;
        margin: 6px 0;
        color: inherit;
        font-size: 0.9rem;
    }
    .positive { color: #2ecc71; font-weight: 600; }
    .negative { color: #e74c3c; font-weight: 600; }

    /* Section headers */
    .section-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #00BAC7;
        margin: 1.5rem 0 0.8rem;
        padding-bottom: 6px;
        border-bottom: 2px solid rgba(0,186,199,0.3);
    }

    /* Data availability */
    .data-avail-present { color: #2ecc71; }
    .data-avail-missing { color: #e74c3c; opacity: 0.7; }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 20px;
        border-radius: 8px 8px 0 0;
    }

    /* Account cards in performance tab */
    .account-card {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 8px;
        padding: 10px 14px;
        border-radius: 8px;
        background: rgba(0,186,199,0.08);
        border: 1px solid rgba(0,186,199,0.15);
    }
    .account-card .name {
        font-weight: 600;
        font-size: 0.85rem;
        color: inherit;
    }
    .account-card .bar-bg {
        background: rgba(128,128,128,0.2);
        border-radius: 4px;
        height: 8px;
        width: 100%;
        margin-top: 4px;
    }

    /* Make multiselect tags more readable */
    span[data-baseweb="tag"] {
        background-color: rgba(0,186,199,0.2) !important;
        border-color: rgba(0,186,199,0.4) !important;
    }
    span[data-baseweb="tag"] span {
        color: inherit !important;
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
    elif metrics.get("Training Name") and metrics.get("Date"):
        kpis["Total Sessions"] = df.groupby(["Training Name", "Date"]).ngroups
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
        scores = df["Assessment Score"].dropna()
        if len(scores) > 0:
            avg = scores.mean()
            if avg <= 1:
                avg = avg * 100
            kpis["Avg Assessment Score"] = round(avg, 1)

    if metrics.get("Pass Flag"):
        total = df["Pass Flag"].notna().sum()
        passed = df["Pass Flag"].sum()
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
        invited = df["Total Invited"].sum()
        attended = df["Total Attended"].sum()
        if invited > 0:
            kpis["Attendance Rate"] = round(attended / invited * 100, 1)

    if metrics.get("Attach Rate Before"):
        vals = df["Attach Rate Before"].dropna()
        if len(vals) > 0:
            avg = vals.mean()
            kpis["Avg Attach Before"] = round(avg * 100 if avg <= 1 else avg, 1)

    if metrics.get("Attach Rate After"):
        vals = df["Attach Rate After"].dropna()
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


def generate_ai_insights(df, metrics, kpis):
    """Generate adaptive AI insights based on available data."""
    insights = []

    if "Pass Rate" in kpis:
        rate = kpis["Pass Rate"]
        if rate >= 85:
            insights.append(("✅", f"Excellent pass rate of **{rate}%** — training content is effective."))
        elif rate >= 70:
            insights.append(("⚠️", f"Pass rate at **{rate}%** — review assessment difficulty or add pre-training materials."))
        else:
            insights.append(("🚨", f"Pass rate of **{rate}%** is low — content may need simplification."))

    if "Avg Assessment Score" in kpis:
        score = kpis["Avg Assessment Score"]
        if score >= 80:
            insights.append(("✅", f"Strong average score of **{score}%** across all learners."))
        elif score >= 60:
            insights.append(("⚠️", f"Average score is **{score}%** — consider additional practice exercises."))
        else:
            insights.append(("🚨", f"Average score of **{score}%** suggests comprehension gaps."))

    if "Attach Improvement" in kpis:
        imp = kpis["Attach Improvement"]
        if imp > 0:
            insights.append(("📈", f"Training drives **+{imp}pp** attach rate improvement. ROI is positive."))
        else:
            insights.append(("📉", f"Attach rate **declined** by {abs(imp)}pp post-training. Investigate."))

    if metrics.get("Account") and metrics.get("Pass Flag"):
        acct_pass = df.groupby("Account")["Pass Flag"].mean().sort_values(ascending=False)
        if len(acct_pass) > 1:
            top = acct_pass.index[0]
            top_rate = acct_pass.iloc[0] * 100
            insights.append(("🏆", f"**{top}** is top-performing with **{top_rate:.0f}%** pass rate."))
            bottom = acct_pass.index[-1]
            bottom_rate = acct_pass.iloc[-1] * 100
            if bottom_rate < 70:
                insights.append(("🎯", f"**{bottom}** needs attention — only **{bottom_rate:.0f}%** pass rate."))

    if "Total Sessions" in kpis and "Unique Learners" in kpis:
        insights.append(("📊", f"**{kpis['Total Sessions']}** sessions trained **{kpis['Unique Learners']}** unique learners."))

    if "Stores" in kpis:
        insights.append(("🏪", f"Training reached **{kpis['Stores']}** stores across **{kpis.get('Countries', '?')}** markets."))

    return insights


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


def render_kpi_card(label, value, delta=None, delta_type="neutral"):
    """Render a styled KPI card."""
    delta_html = ""
    if delta:
        css_class = delta_type if delta_type in ("positive", "negative") else ""
        delta_html = f'<div class="kpi-delta {css_class}">{delta}</div>'
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """


# ====== MAIN APP ======

# Header row with title and data status
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    st.markdown('<div class="main-header">📊 Asia Training Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">bolttech · Executive Training Analytics</div>', unsafe_allow_html=True)

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
    st.markdown(f"<div style='text-align:right; padding-top:16px; font-size:0.8rem; opacity:0.7; color:inherit;'>{data_status}</div>", unsafe_allow_html=True)


# === MAIN CONTENT WITH SIDEBAR FILTERS ===
if df is not None and len(df) > 0:
    df = normalize_columns(df)
    metrics = detect_metrics(df)

    # Parse dates
    if metrics.get("Date"):
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"])

    # ─── SIDEBAR FILTERS ───
    with st.sidebar:
        st.markdown("### 🔍 Filters")

        # Date range
        if metrics.get("Date") and len(df) > 0:
            min_date = df["Date"].min().date()
            max_date = df["Date"].max().date()
            date_range = st.date_input("📅 Date Range", value=(min_date, max_date),
                                       min_value=min_date, max_value=max_date)
            if len(date_range) == 2:
                df = df[(df["Date"].dt.date >= date_range[0]) & (df["Date"].dt.date <= date_range[1])]

        # Country / Market
        if metrics.get("Country") and len(df) > 0:
            country_opts = ["All"] + sorted(df["Country"].dropna().unique().tolist())
            sel_countries = st.selectbox("🌏 Market", options=country_opts, index=0)
            if sel_countries != "All":
                df = df[df["Country"] == sel_countries]

        # Account / Partner
        if metrics.get("Account") and len(df) > 0:
            acct_opts = ["All"] + sorted(df["Account"].dropna().unique().tolist())
            sel_account = st.selectbox("🏢 Account / Partner", options=acct_opts, index=0)
            if sel_account != "All":
                df = df[df["Account"] == sel_account]

        # Training Name
        if metrics.get("Training Name") and len(df) > 0:
            training_opts = ["All"] + sorted(df["Training Name"].dropna().unique().tolist())
            sel_training = st.selectbox("📚 Training Name", options=training_opts, index=0)
            if sel_training != "All":
                df = df[df["Training Name"] == sel_training]

        # Trainer
        if metrics.get("Trainer") and len(df) > 0:
            trainer_opts = ["All"] + sorted(df["Trainer"].dropna().unique().tolist())
            sel_trainer = st.selectbox("👤 Trainer", options=trainer_opts, index=0)
            if sel_trainer != "All":
                df = df[df["Trainer"] == sel_trainer]

        # Training Type / Method
        if metrics.get("Training Type") and len(df) > 0:
            type_opts = ["All"] + sorted(df["Training Type"].dropna().unique().tolist())
            sel_type = st.selectbox("🏷️ Training Type", options=type_opts, index=0)
            if sel_type != "All":
                df = df[df["Training Type"] == sel_type]

        # Store
        if metrics.get("Store") and len(df) > 0:
            store_opts = ["All"] + sorted(df["Store"].dropna().unique().tolist())
            sel_store = st.selectbox("🏪 Store", options=store_opts, index=0)
            if sel_store != "All":
                df = df[df["Store"] == sel_store]

        # Filtered count
        st.markdown(f"""
        <div style="background:rgba(0,186,199,0.1); border-radius:8px; padding:10px 14px; text-align:center; margin:12px 0; border:1px solid rgba(0,186,199,0.3);">
            <span style="font-size:1.4rem; font-weight:700; color:#00BAC7;">{len(df):,}</span>
            <span style="opacity:0.7; font-size:0.85rem;"> records</span>
        </div>
        """, unsafe_allow_html=True)


    # Recompute after filtering
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)

    # ─── CONTEXT BANNER: Show active training name(s) ───
    st.markdown("---")
    if metrics.get("Training Name"):
        unique_trainings = df["Training Name"].dropna().unique()
        if len(unique_trainings) == 1:
            st.markdown(f'<div style="font-size:1rem; font-weight:600; color:#00BAC7; margin-bottom:4px;">📚 {unique_trainings[0]}</div>', unsafe_allow_html=True)
        elif len(unique_trainings) <= 5:
            names = " · ".join(unique_trainings)
            st.markdown(f'<div style="font-size:0.9rem; font-weight:500; color:#00BAC7; margin-bottom:4px;">📚 {names}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="font-size:0.9rem; font-weight:500; color:#00BAC7; margin-bottom:4px;">📚 {len(unique_trainings)} training programs</div>', unsafe_allow_html=True)

    if metrics.get("Date") and len(df) > 0:
        date_min = df["Date"].min().strftime("%b %d, %Y")
        date_max = df["Date"].max().strftime("%b %d, %Y")
        st.caption(f"📅 {date_min} → {date_max}")

    # ─── EXECUTIVE KPI SUMMARY (top of page, big numbers) ───

    # Row 1: Primary KPIs - the 5 things executives care about most
    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)

    with kpi_col1:
        val = f"{kpis.get('Total Sessions', 0):,}"
        st.markdown(render_kpi_card("Trainings Conducted", val, "total sessions"), unsafe_allow_html=True)

    with kpi_col2:
        val = f"{kpis.get('Unique Learners', kpis.get('Total Participants', 0)):,}"
        delta = f"of {kpis['Total Participants']:,} total" if "Unique Learners" in kpis else None
        st.markdown(render_kpi_card("People Trained", val, delta), unsafe_allow_html=True)

    with kpi_col3:
        val = f"{kpis.get('Pass Rate', 'N/A')}%"if "Pass Rate" in kpis else "N/A"
        delta_type = "positive" if kpis.get("Pass Rate", 0) >= 80 else "negative" if kpis.get("Pass Rate", 0) < 70 else "neutral"
        delta = f"{kpis.get('Total Passed', 0):,} passed" if "Total Passed" in kpis else None
        st.markdown(render_kpi_card("Passing Rate", val, delta, delta_type), unsafe_allow_html=True)

    with kpi_col4:
        val = f"{kpis.get('Avg Assessment Score', 'N/A')}%" if "Avg Assessment Score" in kpis else "N/A"
        delta_type = "positive" if kpis.get("Avg Assessment Score", 0) >= 75 else "negative" if kpis.get("Avg Assessment Score", 0) < 60 else "neutral"
        st.markdown(render_kpi_card("Avg Score", val, "assessment average", delta_type), unsafe_allow_html=True)

    with kpi_col5:
        if "Avg Attach After" in kpis:
            val = f"{kpis['Avg Attach After']}%"
            imp = kpis.get("Attach Improvement", 0)
            delta = f"+{imp}pp vs before" if imp > 0 else f"{imp}pp vs before"
            delta_type = "positive" if imp > 0 else "negative"
        else:
            val = "N/A"
            delta = "no sales data"
            delta_type = "neutral"
        st.markdown(render_kpi_card("Attach Rate (Post)", val, delta, delta_type), unsafe_allow_html=True)


    # Row 2: Secondary KPIs
    sec_col1, sec_col2, sec_col3, sec_col4, sec_col5 = st.columns(5)

    with sec_col1:
        val = f"{kpis.get('Countries', 0)}"
        st.markdown(render_kpi_card("Markets", val, "countries covered"), unsafe_allow_html=True)

    with sec_col2:
        val = f"{kpis.get('Accounts', 0)}"
        st.markdown(render_kpi_card("Partners", val, "active accounts"), unsafe_allow_html=True)

    with sec_col3:
        val = f"{kpis.get('Stores', 0):,}" if "Stores" in kpis else "N/A"
        st.markdown(render_kpi_card("Stores Reached", val), unsafe_allow_html=True)

    with sec_col4:
        if metrics.get("Training Type") and len(df) > 0:
            method_counts = df["Training Type"].value_counts()
            top_method = method_counts.index[0] if len(method_counts) > 0 else "N/A"
            val = top_method
            delta = f"{method_counts.iloc[0]:,} sessions"
            st.markdown(render_kpi_card("Top Method", val, delta), unsafe_allow_html=True)
        else:
            st.markdown(render_kpi_card("Training Hours", f"{kpis.get('Total Training Hours', 'N/A')}"), unsafe_allow_html=True)

    with sec_col5:
        if "Attendance Rate" in kpis:
            val = f"{kpis['Attendance Rate']}%"
            st.markdown(render_kpi_card("Attendance Rate", val), unsafe_allow_html=True)
        elif "Total Training Hours" in kpis:
            val = f"{kpis['Total Training Hours']:,.0f}"
            st.markdown(render_kpi_card("Training Hours", val), unsafe_allow_html=True)
        else:
            val = f"{len(df):,}"
            st.markdown(render_kpi_card("Total Records", val, "in filtered view"), unsafe_allow_html=True)


    # ─── TABBED CONTENT SECTIONS ───
    st.markdown("---")

    tab_overview, tab_performance, tab_trends, tab_data = st.tabs([
        "📋 Overview & Insights", "🎯 Performance", "📈 Trends", "🗂️ Data & Export"
    ])

    # === TAB 1: OVERVIEW & INSIGHTS ===
    with tab_overview:
        # AI Insights
        insights = generate_ai_insights(df, metrics, kpis)
        if insights:
            st.markdown('<div class="section-header">💡 Key Insights</div>', unsafe_allow_html=True)
            cols = st.columns(2)
            for i, (icon, text) in enumerate(insights):
                with cols[i % 2]:
                    st.markdown(f'<div class="insight-box">{icon} {text}</div>', unsafe_allow_html=True)

        # Country and Account breakdown side by side
        st.markdown("")
        overview_col1, overview_col2 = st.columns(2)

        if metrics.get("Country"):
            with overview_col1:
                st.markdown('<div class="section-header">🌏 Training by Market</div>', unsafe_allow_html=True)
                country_data = df["Country"].value_counts().reset_index()
                country_data.columns = ["Country", "Records"]
                fig = px.pie(country_data, values="Records", names="Country",
                             color_discrete_sequence=["#00BAC7", "#33C8D2", "#66D6DD", "#99E4E8", "#CCF2F3", "#E6F9FA"],
                             hole=0.45)
                fig.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0),
                                  legend=dict(orientation="h", yanchor="bottom", y=-0.2))
                st.plotly_chart(fig, use_container_width=True)

        if metrics.get("Training Type"):
            with overview_col2:
                st.markdown('<div class="section-header">🏷️ Training Methods</div>', unsafe_allow_html=True)
                method_data = df["Training Type"].value_counts().reset_index()
                method_data.columns = ["Method", "Count"]
                fig = px.bar(method_data, x="Count", y="Method", orientation="h",
                             color_discrete_sequence=["#00BAC7"])
                fig.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0),
                                  yaxis_title="", xaxis_title="Sessions")
                st.plotly_chart(fig, use_container_width=True)


    # === TAB 2: PERFORMANCE ===
    with tab_performance:
        perf_col1, perf_col2 = st.columns(2)

        # Pass Rate by Account
        if metrics.get("Account") and metrics.get("Pass Flag"):
            with perf_col1:
                st.markdown('<div class="section-header">🎯 Pass Rate by Account</div>', unsafe_allow_html=True)
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
                st.markdown('<div class="section-header">👤 Trainer Performance</div>', unsafe_allow_html=True)
                t_data = df.groupby("Trainer").agg(
                    sessions=("Date", "count"),
                    pass_rate=("Pass Flag", "mean")
                ).reset_index()
                t_data["Pass Rate (%)"] = (t_data["pass_rate"] * 100).round(1)
                t_data = t_data.sort_values("Pass Rate (%)", ascending=False)

                fig = px.bar(t_data, x="Trainer", y="Pass Rate (%)", color="sessions",
                             color_continuous_scale=[[0, "#e6f9fa"], [0.5, "#00BAC7"], [1, "#170F4F"]])
                fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0),
                                  xaxis_title="", yaxis_title="Pass Rate (%)")
                st.plotly_chart(fig, use_container_width=True)

        # Attach Rate Comparison
        if metrics.get("Attach Rate Before") and metrics.get("Attach Rate After") and metrics.get("Account"):
            st.markdown('<div class="section-header">📈 Attach Rate: Before vs After Training (30 Days)</div>', unsafe_allow_html=True)

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
                                         marker_color="#170F4F", opacity=0.6))
                    fig.add_trace(go.Bar(name="After", x=attach_data["Account"], y=attach_data["after"],
                                         marker_color="#00BAC7", opacity=0.85))
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
            st.markdown('<div class="section-header">🏪 Store Performance</div>', unsafe_allow_html=True)

            store_col1, store_col2 = st.columns([3, 1])

            with store_col1:
                store_agg = {"Records": ("Store", "count")}
                if metrics.get("Pass Flag"):
                    store_agg["Pass Rate"] = ("Pass Flag", "mean")
                if metrics.get("Assessment Score"):
                    store_agg["Avg Score"] = ("Assessment Score", "mean")
                if metrics.get("Attach Rate Before"):
                    store_agg["Attach Before"] = ("Attach Rate Before", "mean")
                if metrics.get("Attach Rate After"):
                    store_agg["Attach After"] = ("Attach Rate After", "mean")

                store_data = df.groupby(["Store"] + (["Account"] if metrics.get("Account") else [])).agg(**store_agg).reset_index()

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


    # === TAB 3: TRENDS ===
    with tab_trends:
        if metrics.get("Date"):
            st.markdown('<div class="section-header">📅 Training Volume Over Time</div>', unsafe_allow_html=True)
            df_trend = df.set_index("Date").resample("W").size().reset_index(name="Sessions")
            fig = px.area(df_trend, x="Date", y="Sessions", color_discrete_sequence=["#00BAC7"])
            fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0),
                              xaxis_title="", yaxis_title="Sessions per Week")
            st.plotly_chart(fig, use_container_width=True)

        # Country trend over time
        if metrics.get("Date") and metrics.get("Country"):
            st.markdown('<div class="section-header">🌏 Training Volume by Market</div>', unsafe_allow_html=True)
            country_trend = df.groupby([pd.Grouper(key="Date", freq="W"), "Country"]).size().reset_index(name="Sessions")
            fig = px.line(country_trend, x="Date", y="Sessions", color="Country",
                          color_discrete_sequence=["#00BAC7", "#170F4F", "#FFB74D", "#2ecc71", "#e74c3c", "#9b59b6"])
            fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0),
                              xaxis_title="", yaxis_title="Sessions per Week",
                              legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig, use_container_width=True)

        # Pass rate trend
        if metrics.get("Date") and metrics.get("Pass Flag"):
            st.markdown('<div class="section-header">📊 Pass Rate Trend</div>', unsafe_allow_html=True)
            pass_trend = df.set_index("Date").resample("W")["Pass Flag"].mean().reset_index()
            pass_trend["Pass Rate (%)"] = (pass_trend["Pass Flag"] * 100).round(1)
            fig = px.line(pass_trend, x="Date", y="Pass Rate (%)", color_discrete_sequence=["#00BAC7"])
            fig.add_hline(y=80, line_dash="dash", line_color="rgba(46,204,113,0.5)", annotation_text="Target: 80%")
            fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0),
                              xaxis_title="", yaxis_title="Pass Rate (%)")
            st.plotly_chart(fig, use_container_width=True)


    # === TAB 4: DATA & EXPORT ===
    with tab_data:
        data_col1, data_col2 = st.columns([3, 1])

        with data_col1:
            st.markdown('<div class="section-header">📋 Raw Data</div>', unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True, height=400)

        with data_col2:
            st.markdown('<div class="section-header">⬇️ Export</div>', unsafe_allow_html=True)
            st.download_button("📄 Download CSV", df.to_csv(index=False), "training_data.csv", "text/csv",
                               use_container_width=True)
            buf = BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as w:
                df.to_excel(w, index=False, sheet_name="Data")
            st.download_button("📊 Download Excel", buf.getvalue(), "training_dashboard.xlsx",
                              "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                              use_container_width=True)

            st.markdown("---")
            st.markdown('<div class="section-header">📋 Data Availability</div>', unsafe_allow_html=True)

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
                st.success(f"✅ Loaded {len(data):,} records")
                if df is None:
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
        st.markdown("""
        ### 📎 Upload Your Training Data

        **To get started:**
        1. Go to SharePoint → **SEA Training Site → Global Documents → Training Dashboard Masterfile**
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
