import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import numpy as np
from datetime import datetime
from rapidfuzz import fuzz, process

# Page config
st.set_page_config(
    page_title="Asia Training Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - bolttech branding (light & dark mode compatible)
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, rgba(0,186,199,0.08) 0%, transparent 30%);
    }
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #00BAC7;
        text-align: center;
        margin-bottom: 0.5rem;
        font-family: 'Segoe UI', sans-serif;
    }
    .sub-header {
        font-size: 0.9rem;
        color: inherit;
        opacity: 0.6;
        text-align: center;
        margin-bottom: 2rem;
    }
    .positive { color: #2ecc71; font-weight: 600; }
    .negative { color: #e74c3c; font-weight: 600; }
    .insight-box {
        background: rgba(0,186,199,0.1);
        border-radius: 8px;
        padding: 1rem;
        border-left: 3px solid #00BAC7;
        margin: 0.5rem 0;
        color: inherit;
    }
    .warning-box {
        background: rgba(243,156,18,0.1);
        border-radius: 8px;
        padding: 1rem;
        border-left: 3px solid #f39c12;
        margin: 0.5rem 0;
        color: inherit;
    }
    .data-avail-present { color: #2ecc71; }
    .data-avail-missing { color: #e74c3c; opacity: 0.7; }
    div[data-testid="stMetricValue"] { color: #00BAC7 !important; }
    h3, h4 { color: #00BAC7 !important; }
    
    /* Justified metric cards */
    div[data-testid="stMetric"] {
        text-align: center;
        background: rgba(0,186,199,0.04);
        border-radius: 10px;
        padding: 16px 8px;
        border: 1px solid rgba(0,186,199,0.1);
        height: 100%;
    }
    div[data-testid="stMetricLabel"] {
        justify-content: center;
    }
    div[data-testid="stMetricDelta"] {
        justify-content: center;
        display: flex;
        width: 100%;
    }
    div[data-testid="stMetricDelta"] > div {
        justify-content: center;
        width: 100%;
        display: flex;
    }
    /* Make columns in metric rows equal height */
    div[data-testid="stHorizontalBlock"] {
        align-items: stretch;
    }
</style>
""", unsafe_allow_html=True)


# === COLUMN DETECTION & MAPPING ===

# Known column name variants mapped to canonical names
COLUMN_ALIASES = {
    # Date
    "date": "Date", "date of training": "Date", "training date": "Date",
    # Trainer
    "trainer": "Trainer", "trainer name": "Trainer", "facilitator": "Trainer",
    # Account / Partner
    "account": "Account", "partner name": "Account", "partner": "Account", "client": "Account",
    # Country
    "country": "Country", "market": "Country", "region": "Country",
    # Store
    "store": "Store", "store name": "Store", "branch": "Store", "location": "Store", "outlet": "Store",
    # Training name
    "training name": "Training Name", "training title": "Training Name", "course": "Training Name",
    "program": "Training Name", "module": "Training Name",
    # Training type/method
    "training type": "Training Type", "training method": "Training Type", "type": "Training Type",
    "method": "Training Type", "delivery mode": "Training Type",
    # Training ID
    "training id": "Training ID", "session id": "Training ID",
    # Trainee
    "trainee name": "Trainee Name", "participant": "Trainee Name", "learner": "Trainee Name",
    "trainee code": "Trainee Code", "employee id": "Trainee Code",
    # Assessment
    "training assessment score %": "Assessment Score", "score": "Assessment Score",
    "assessment score": "Assessment Score", "test score": "Assessment Score", "grade": "Assessment Score",
    # Pass/Fail
    "training assessment result": "Assessment Result", "result": "Assessment Result",
    "pass/fail": "Assessment Result", "status": "Assessment Result",
    "pass flag": "Pass Flag", "passed": "Pass Flag",
    "fail flag": "Fail Flag", "failed": "Fail Flag",
    # Attendance metrics (optional)
    "total invited": "Total Invited", "invited": "Total Invited",
    "total attended": "Total Attended", "attended": "Total Attended", "attendance count": "Total Attended",
    "total passed": "Total Passed",
    # Attach rates
    "attach rate before": "Attach Rate Before", "attach rate before (%)": "Attach Rate Before",
    "attach rate after": "Attach Rate After", "attach rate after (%)": "Attach Rate After",
    "attach lift": "Attach Lift",
    # Training hours
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
            if canonical not in rename_map.values():  # avoid duplicates
                rename_map[col] = canonical
    df = df.rename(columns=rename_map)
    return df


def fuzzy_match_store(store_name, candidates, threshold=70):
    """Find the best fuzzy match for a store name from a list of candidates.
    Returns (matched_name, score) or (None, 0) if no match above threshold."""
    if not store_name or not candidates:
        return None, 0
    
    # Clean the store name for better matching
    clean_name = str(store_name).strip().lower()
    clean_candidates = [str(c).strip().lower() for c in candidates]
    
    # Try exact match first
    if clean_name in clean_candidates:
        idx = clean_candidates.index(clean_name)
        return candidates[idx], 100
    
    # Fuzzy match
    result = process.extractOne(
        clean_name,
        clean_candidates,
        scorer=fuzz.token_sort_ratio,
        score_cutoff=threshold
    )
    
    if result:
        matched_text, score, idx = result
        return candidates[idx], score
    
    return None, 0


def match_sales_to_training(training_df, sales_df, match_threshold=70):
    """Match sales data to training records using fuzzy store name matching.
    
    Returns:
        training_df with Attach Rate Before/After filled from sales data,
        match_report DataFrame showing match results
    """
    # Ensure dates are parsed
    training_df["Date"] = pd.to_datetime(training_df["Date"], errors="coerce")
    sales_df["Date"] = pd.to_datetime(sales_df["Date"], errors="coerce")
    
    # Get unique store names from sales data
    sales_stores = sales_df["Store"].dropna().unique().tolist() if "Store" in sales_df.columns else []
    sales_accounts = sales_df["Account"].dropna().unique().tolist() if "Account" in sales_df.columns else []
    
    # Determine matching column (Store preferred, fall back to Account)
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
    
    # Build fuzzy match mapping
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
    
    # Calculate attach rates using matched stores
    attach_before_list = []
    attach_after_list = []
    
    # Ensure sales has required columns
    has_transactions = "Total Transactions" in sales_df.columns and "Transactions with Protection" in sales_df.columns
    
    for idx, row in training_df.iterrows():
        training_date = row["Date"]
        training_store = row.get(training_match_col)
        
        if pd.isna(training_date) or pd.isna(training_store):
            attach_before_list.append(np.nan)
            attach_after_list.append(np.nan)
            continue
        
        # Get matched sales store name
        matched_store = match_map.get(training_store)
        
        if not matched_store or not has_transactions:
            attach_before_list.append(np.nan)
            attach_after_list.append(np.nan)
            continue
        
        # Filter sales for matched store
        store_sales = sales_df[sales_df[sales_match_col] == matched_store]
        
        # 30 days before
        before_mask = (store_sales["Date"] >= training_date - pd.Timedelta(days=30)) & \
                      (store_sales["Date"] < training_date)
        before = store_sales[before_mask]
        
        if len(before) > 0:
            total = before["Total Transactions"].sum()
            protected = before["Transactions with Protection"].sum()
            attach_before_list.append((protected / total) if total > 0 else np.nan)
        else:
            attach_before_list.append(np.nan)
        
        # 30 days after
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


def detect_metrics(df):
    """Detect which metrics are available in the dataset."""
    metrics = {}
    
    # Date
    metrics["Date"] = "Date" in df.columns and df["Date"].notna().sum() > 0
    # Trainer
    metrics["Trainer"] = "Trainer" in df.columns and df["Trainer"].notna().sum() > 0
    # Account
    metrics["Account"] = "Account" in df.columns and df["Account"].notna().sum() > 0
    # Country
    metrics["Country"] = "Country" in df.columns and df["Country"].notna().sum() > 0
    # Store
    metrics["Store"] = "Store" in df.columns and df["Store"].notna().sum() > 0
    # Training Name
    metrics["Training Name"] = "Training Name" in df.columns and df["Training Name"].notna().sum() > 0
    # Training Type
    metrics["Training Type"] = "Training Type" in df.columns and df["Training Type"].notna().sum() > 0
    # Training ID (for session counting)
    metrics["Training ID"] = "Training ID" in df.columns and df["Training ID"].notna().sum() > 0
    # Trainee-level
    metrics["Trainee Name"] = "Trainee Name" in df.columns and df["Trainee Name"].notna().sum() > 0
    metrics["Trainee Code"] = "Trainee Code" in df.columns and df["Trainee Code"].notna().sum() > 0
    # Assessment
    metrics["Assessment Score"] = "Assessment Score" in df.columns and df["Assessment Score"].notna().sum() > 0
    metrics["Assessment Result"] = "Assessment Result" in df.columns and df["Assessment Result"].notna().sum() > 0
    metrics["Pass Flag"] = "Pass Flag" in df.columns and df["Pass Flag"].notna().sum() > 0
    # Attendance (optional)
    metrics["Total Invited"] = "Total Invited" in df.columns and df["Total Invited"].notna().sum() > 0
    metrics["Total Attended"] = "Total Attended" in df.columns and df["Total Attended"].notna().sum() > 0
    # Attach rates
    metrics["Attach Rate Before"] = "Attach Rate Before" in df.columns and df["Attach Rate Before"].notna().sum() > 0
    metrics["Attach Rate After"] = "Attach Rate After" in df.columns and df["Attach Rate After"].notna().sum() > 0
    # Training hours
    metrics["Training Hours"] = "Training Hours" in df.columns and df["Training Hours"].notna().sum() > 0
    
    return metrics


def compute_kpis(df, metrics):
    """Compute KPIs based on available metrics."""
    kpis = {}
    
    # Total Sessions
    if metrics.get("Training ID"):
        kpis["Total Sessions"] = df["Training ID"].nunique()
    elif metrics.get("Training Name") and metrics.get("Date"):
        kpis["Total Sessions"] = df.groupby(["Training Name", "Date"]).ngroups
    elif metrics.get("Date"):
        kpis["Total Sessions"] = df["Date"].nunique()
    
    # Training Hours
    if metrics.get("Training Hours"):
        kpis["Total Training Hours"] = df["Training Hours"].sum()
    
    # Unique Learners
    if metrics.get("Trainee Code"):
        kpis["Unique Learners"] = df["Trainee Code"].nunique()
    elif metrics.get("Trainee Name"):
        kpis["Unique Learners"] = df["Trainee Name"].nunique()
    
    # Total Participants (rows)
    kpis["Total Participants"] = len(df)
    
    # Average Assessment Score
    if metrics.get("Assessment Score"):
        scores = df["Assessment Score"].dropna()
        if len(scores) > 0:
            avg = scores.mean()
            # If scores are 0-1, convert to percentage
            if avg <= 1:
                avg = avg * 100
            kpis["Avg Assessment Score"] = round(avg, 1)
    
    # Pass Rate
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
    
    # Attendance Rate (only if data available)
    if metrics.get("Total Invited") and metrics.get("Total Attended"):
        invited = df["Total Invited"].sum()
        attended = df["Total Attended"].sum()
        if invited > 0:
            kpis["Attendance Rate"] = round(attended / invited * 100, 1)
    
    # Attach Rates
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
    
    # Countries & Accounts
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
    
    # Pass rate insight
    if "Pass Rate" in kpis:
        rate = kpis["Pass Rate"]
        if rate >= 85:
            insights.append(("✅", f"Excellent pass rate of **{rate}%** — training content is effective."))
        elif rate >= 70:
            insights.append(("⚠️", f"Pass rate at **{rate}%** — review assessment difficulty or add pre-training materials."))
        else:
            insights.append(("🚨", f"Pass rate of **{rate}%** is low — content may need simplification."))
    
    # Assessment score insight
    if "Avg Assessment Score" in kpis:
        score = kpis["Avg Assessment Score"]
        if score >= 80:
            insights.append(("✅", f"Strong average score of **{score}%** across all learners."))
        elif score >= 60:
            insights.append(("⚠️", f"Average score is **{score}%** — consider additional practice exercises."))
        else:
            insights.append(("🚨", f"Average score of **{score}%** suggests comprehension gaps."))
    
    # Attach rate insight
    if "Attach Improvement" in kpis:
        imp = kpis["Attach Improvement"]
        if imp > 0:
            insights.append(("📈", f"Training drives **+{imp}pp** attach rate improvement. ROI is positive."))
        else:
            insights.append(("📉", f"Attach rate **declined** by {abs(imp)}pp post-training. Investigate."))
    
    # Top/bottom performers
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
    
    # Volume
    if "Total Sessions" in kpis and "Unique Learners" in kpis:
        insights.append(("📊", f"**{kpis['Total Sessions']}** sessions trained **{kpis['Unique Learners']}** unique learners."))
    
    # Store coverage
    if "Stores" in kpis:
        insights.append(("🏪", f"Training reached **{kpis['Stores']}** stores across **{kpis.get('Countries', '?')}** countries."))
    
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
    
    # Generate Training ID
    df["Training ID"] = df["Country"] + "-" + df["Date of Training"].dt.strftime("%Y%m%d") + "-" + df["Training Title"].str[:20]
    
    # Assessment Result from Pass Flag
    df["Training Assessment Result"] = df["Pass Flag"].map({1.0: "Passed", 0.0: "Failed"})
    df["Fail Flag"] = 1.0 - df["Pass Flag"]
    
    # Sparse attach rates (realistic - only some rows have it)
    df["Attach Rate Before"] = np.nan
    df["Attach Rate After"] = np.nan
    attach_idx = np.random.choice(n, 40, replace=False)
    df.loc[attach_idx, "Attach Rate Before"] = np.random.uniform(0.05, 0.20, 40).round(3)
    df.loc[attach_idx, "Attach Rate After"] = df.loc[attach_idx, "Attach Rate Before"] + np.random.uniform(0.01, 0.10, 40).round(3)
    
    return df


# ====== MAIN APP ======

st.markdown('<div class="main-header">📚 Asia Training Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Powered Training Analytics | bolttech</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 📚 bolttech Training")
    
    # Data source selection at bottom using a container trick:
    # Load data first (in a bottom container), then show filters on top
    
    # --- DATA SOURCE (rendered at bottom via expander) ---
    data_source_container = st.container()
    
    # --- FILTERS PLACEHOLDER (rendered first visually) ---
    filters_container = st.container()
    
    # --- Populate data source (appears at bottom) ---
    with data_source_container:
        st.markdown("---")
        with st.expander("📁 Data Source", expanded=False):
            data_source = st.radio(
                "Choose data input:",
                ["📂 Auto-load Master File", "📋 Paste Data", "📎 Upload Excel/CSV", "🎯 Use Demo Data"],
                index=0
            )
    
    df = None
    
    # Path to the shared master file (trainers update this file directly)
    MASTER_FILE = r"c:\Users\BenjJavier\OneDrive - bolttech\Documents\Copilot\Created\Asia Training Dashboard v1.xlsx"
    MASTER_SHEET = "Raw_Data"
    
    with data_source_container:
        if data_source == "📂 Auto-load Master File":
            st.caption("Reading from shared master file...")
            
            if st.button("🔄 Refresh Data"):
                st.cache_data.clear()
            
            try:
                import os
                if os.path.exists(MASTER_FILE):
                    xls = pd.ExcelFile(MASTER_FILE)
                    if MASTER_SHEET in xls.sheet_names:
                        df = pd.read_excel(MASTER_FILE, sheet_name=MASTER_SHEET, dtype={"Trainee Code": str, "Store Code": str})
                    else:
                        df = pd.read_excel(MASTER_FILE, sheet_name=0)
                    
                    last_modified = datetime.fromtimestamp(os.path.getmtime(MASTER_FILE))
                    st.success(f"Loaded {len(df):,} records")
                    st.caption(f"Last updated: {last_modified.strftime('%b %d, %Y %I:%M %p')}")
                else:
                    st.warning("Master file not found.")
                    df = generate_sample_data()
            except PermissionError:
                st.warning("File open in Excel. Close it or use 'Upload'.")
            except Exception as e:
                st.error(f"Error: {e}")
        
        elif data_source == "🎯 Use Demo Data":
            df = generate_sample_data()
            st.success(f"Demo data loaded ({len(df)} records)")
            
        elif data_source == "📎 Upload Excel/CSV":
            uploaded_file = st.file_uploader("Upload your file", type=["xlsx", "csv"])
            if uploaded_file:
                try:
                    if uploaded_file.name.endswith(".csv"):
                        df = pd.read_csv(uploaded_file)
                    else:
                        xls = pd.ExcelFile(uploaded_file)
                        if "Raw_Data" in xls.sheet_names:
                            df = pd.read_excel(uploaded_file, sheet_name="Raw_Data")
                        else:
                            df = pd.read_excel(uploaded_file, sheet_name=0)
                    st.success(f"Loaded {len(df)} records")
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.info("Upload an Excel or CSV file")
                
        elif data_source == "📋 Paste Data":
            st.markdown("Paste tab-separated data:")
            pasted = st.text_area("Paste here", height=150,
                placeholder="Country\tDate of Training\tTrainer Name\t...")
            if pasted.strip():
                try:
                    from io import StringIO
                    df = pd.read_csv(StringIO(pasted), sep="\t")
                    st.success(f"Parsed {len(df)} records")
                except Exception as e:
                    st.error(f"Could not parse: {e}")
    
    # --- FILTERS (rendered at top) ---
    if df is not None and len(df) > 0:
        df = normalize_columns(df)
        metrics = detect_metrics(df)
        
        # Parse dates
        if metrics.get("Date"):
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df = df.dropna(subset=["Date"])
        
        with filters_container:
            st.markdown("### 🔍 Filters")
            
            # Date range filter
            if metrics.get("Date") and len(df) > 0:
                st.markdown("**📅 Date Range**")
                min_date = df["Date"].min().date()
                max_date = df["Date"].max().date()
                date_range = st.date_input("Select range", value=(min_date, max_date),
                                           min_value=min_date, max_value=max_date)
                if len(date_range) == 2:
                    df = df[(df["Date"].dt.date >= date_range[0]) & (df["Date"].dt.date <= date_range[1])]
            
            # Dynamic filters
            if metrics.get("Country") and len(df) > 0:
                opts = sorted(df["Country"].dropna().unique())
                sel = st.multiselect("🌏 Country", options=opts, default=opts)
                df = df[df["Country"].isin(sel)]
            
            if metrics.get("Account") and len(df) > 0:
                opts = sorted(df["Account"].dropna().unique())
                sel = st.multiselect("🏢 Account", options=opts, default=opts)
                df = df[df["Account"].isin(sel)]
            
            if metrics.get("Trainer") and len(df) > 0:
                opts = sorted(df["Trainer"].dropna().unique())
                sel = st.multiselect("👤 Trainer", options=opts, default=opts)
                df = df[df["Trainer"].isin(sel)]
            
            if metrics.get("Store") and len(df) > 0:
                opts = sorted(df["Store"].dropna().unique())
                sel = st.multiselect("🏪 Store", options=opts, default=opts)
                df = df[df["Store"].isin(sel)]
            
            if metrics.get("Training Name") and len(df) > 0:
                opts = sorted(df["Training Name"].dropna().unique())
                sel = st.multiselect("📚 Training Name", options=opts, default=opts)
                df = df[df["Training Name"].isin(sel)]
            
            if metrics.get("Training Type") and len(df) > 0:
                opts = sorted(df["Training Type"].dropna().unique())
                sel = st.multiselect("🏷️ Training Type", options=opts, default=opts)
                df = df[df["Training Type"].isin(sel)]
            
            st.markdown(f"**📊 Filtered: {len(df):,} records**")
        
        # Sales data matching (at bottom)
        with data_source_container:
            st.markdown("---")
            with st.expander("📊 Sales Data (Attach Rate)", expanded=False):
                sales_upload = st.file_uploader("Upload sales export", type=["xlsx", "csv"], key="sales_file")
                
                if sales_upload:
                    try:
                        if sales_upload.name.endswith(".csv"):
                            sales_df = pd.read_csv(sales_upload)
                        else:
                            sales_df = pd.read_excel(sales_upload)
                        
                        sales_df = normalize_columns(sales_df)
                        st.success(f"Sales data: {len(sales_df):,} rows")
                        
                        threshold = st.slider("Match sensitivity", 50, 100, 70, 5)
                        
                        if st.button("🔗 Match & Calculate"):
                            with st.spinner("Fuzzy matching..."):
                                df, match_report = match_sales_to_training(df, sales_df, match_threshold=threshold)
                            
                            if len(match_report) > 0:
                                matched_count = (match_report["Status"] == "✅ Matched").sum()
                                st.success(f"Matched {matched_count}/{len(match_report)} stores")
                                st.dataframe(match_report, use_container_width=True)
                                metrics = detect_metrics(df)
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.caption("Upload Power BI export for auto attach rate calculation.")


# ====== MAIN CONTENT ======
if df is not None and len(df) > 0:
    metrics = detect_metrics(df)
    kpis = compute_kpis(df, metrics)
    
    # === ADAPTIVE KPI CARDS ===
    st.markdown("---")
    
    # Show filtered training name(s) as context header
    if metrics.get("Training Name"):
        unique_trainings = df["Training Name"].dropna().unique()
        if len(unique_trainings) == 1:
            training_label = f"**📚 Training: {unique_trainings[0]}**"
        elif len(unique_trainings) <= 3:
            training_label = f"**📚 Trainings: {' · '.join(unique_trainings)}**"
        else:
            training_label = f"**📚 Trainings: {len(unique_trainings)} programs selected**"
    else:
        training_label = ""
    
    # Date range context
    if metrics.get("Date") and len(df) > 0:
        date_min = df["Date"].min().strftime("%b %d, %Y")
        date_max = df["Date"].max().strftime("%b %d, %Y")
        date_label = f"**📅 Date Range: {date_min} → {date_max}**"
    else:
        date_label = ""
    
    # Display context line
    context_parts = [p for p in [training_label, date_label] if p]
    if context_parts:
        st.markdown(" &nbsp;|&nbsp; ".join(context_parts), unsafe_allow_html=True)
    
    # Build KPI display list in specified order
    kpi_items = []
    
    # 1. Total Sessions
    if "Total Sessions" in kpis:
        kpi_items.append(("Total Sessions", f"{kpis['Total Sessions']:,}", "sessions conducted"))
    
    # 2. Individuals Trained
    if "Unique Learners" in kpis:
        kpi_items.append(("Individuals Trained", f"{kpis['Unique Learners']:,}", "unique participants"))
    
    # 3. Passing Rate
    if "Pass Rate" in kpis:
        kpi_items.append(("Passing Rate", f"{kpis['Pass Rate']}%", f"{kpis.get('Total Passed', 0):,} passed"))
    
    # 4. Average Score
    if "Avg Assessment Score" in kpis:
        kpi_items.append(("Average Score", f"{kpis['Avg Assessment Score']}%", "assessment average"))
    
    # 5. Attach Rate 30 Days After Training
    if "Avg Attach After" in kpis:
        detail = f"+{kpis['Attach Improvement']}pp lift" if "Attach Improvement" in kpis and kpis["Attach Improvement"] > 0 else "30-day post-training"
        kpi_items.append(("Attach Rate (30 Days After)", f"{kpis['Avg Attach After']}%", detail))
    
    # 6. Training Method (compact format for smaller screens)
    if metrics.get("Training Type") and len(df) > 0:
        method_counts = df["Training Type"].value_counts()
        method_str = "\n".join([f"{method}: {count}" for method, count in method_counts.items()])
        kpi_items.append(("Training Method", f"{len(method_counts)} types", method_str))
    
    # Display KPIs in 2 rows of 3, justified (equal width columns)
    if kpi_items:
        row1 = kpi_items[:3]
        row2_metrics = [item for item in kpi_items[3:] if item[0] != "Training Method"]
        training_method_item = next((item for item in kpi_items if item[0] == "Training Method"), None)
        
        cols1 = st.columns([1, 1, 1])
        for i, (label, value, detail) in enumerate(row1):
            with cols1[i]:
                st.metric(label, value, detail)
        
        if row2_metrics or training_method_item:
            cols2 = st.columns([1, 1, 1])
            for i, (label, value, detail) in enumerate(row2_metrics[:2]):
                with cols2[i]:
                    st.metric(label, value, detail)
            
            # Training Method as custom styled card (same size as st.metric cards)
            if training_method_item:
                col_idx = len(row2_metrics[:2])
                with cols2[col_idx]:
                    method_counts = df["Training Type"].value_counts()
                    lines = "".join([f'<div style="display:flex;justify-content:space-between;margin:4px 0;"><span style="font-size:1.3rem;">{m}</span><span style="font-weight:700;color:#00BAC7;font-size:1.3rem;">{c}</span></div>' for m, c in method_counts.items()])
                    st.markdown(f"""
                    <div style="text-align:center; background:rgba(0,186,199,0.04); border-radius:10px; padding:16px 12px; border:1px solid rgba(0,186,199,0.1); height:100%; display:flex; flex-direction:column; justify-content:center;">
                        <div style="font-size:0.875rem; opacity:0.7; margin-bottom:8px; font-weight:400;">Training Method</div>
                        <div style="text-align:left; padding:0 8px;">{lines}</div>
                    </div>
                    """, unsafe_allow_html=True)
    
    # === AI INSIGHTS ===
    st.markdown("---")
    st.markdown("### 💡 AI-Powered Insights")
    
    insights = generate_ai_insights(df, metrics, kpis)
    if insights:
        cols = st.columns(2)
        for i, (icon, text) in enumerate(insights):
            with cols[i % 2]:
                st.markdown(f'<div class="insight-box">{icon} {text}</div>', unsafe_allow_html=True)
    else:
        st.info("Upload more data to generate insights.")
    
    # === CHARTS ===
    st.markdown("---")
    chart_col1, chart_col2 = st.columns(2)
    
    # Account initial as logo
    def get_logo_html(account_name):
        """Styled initial circle for the account."""
        initial = account_name[0].upper() if account_name else "?"
        return f'<div style="width:30px;height:30px;min-width:30px;border-radius:6px;background:#00BAC7;color:white;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;">{initial}</div>'
    
    # Pass Rate by Account (with logos)
    if metrics.get("Account") and metrics.get("Pass Flag"):
        with chart_col1:
            st.markdown("#### 🎯 Pass Rate by Account")
            acct_data = df.groupby("Account")["Pass Flag"].agg(["sum", "count"]).reset_index()
            acct_data["Pass Rate (%)"] = (acct_data["sum"] / acct_data["count"] * 100).round(1)
            acct_data = acct_data.sort_values("Pass Rate (%)", ascending=False)
            
            # Display as cards with logos
            for _, row in acct_data.iterrows():
                account = row["Account"]
                rate = row["Pass Rate (%)"]
                total = int(row["count"])
                passed = int(row["sum"])
                logo_html = get_logo_html(account)
                
                # Color based on pass rate
                if rate >= 80:
                    bar_color = "#00BAC7"
                elif rate >= 60:
                    bar_color = "#FFB74D"
                else:
                    bar_color = "#e74c3c"
                
                st.markdown(f"""
                <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px; padding:8px 12px; border-radius:8px; background:rgba(0,186,199,0.05); border:1px solid rgba(0,186,199,0.1);">
                    {logo_html}
                    <div style="flex:1;">
                        <div style="font-weight:600; font-size:0.85rem;">{account}</div>
                        <div style="background:rgba(128,128,128,0.15); border-radius:4px; height:8px; width:100%; margin-top:4px;">
                            <div style="background:{bar_color}; border-radius:4px; height:8px; width:{min(rate, 100)}%;"></div>
                        </div>
                    </div>
                    <div style="text-align:right; min-width:55px;">
                        <div style="font-weight:700; color:{bar_color}; font-size:1.1rem;">{rate:.0f}%</div>
                        <div style="font-size:0.65rem; opacity:0.6;">{passed}/{total}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # Trainings by Country
    if metrics.get("Country"):
        with chart_col2:
            st.markdown("#### 🌏 Distribution by Country")
            country_data = df["Country"].value_counts().reset_index()
            country_data.columns = ["Country", "Records"]
            
            fig = px.pie(country_data, values="Records", names="Country",
                         color_discrete_sequence=["#00BAC7", "#33C8D2", "#66D6DD", "#99E4E8", "#CCF2F3", "#E6F9FA"],
                         hole=0.4)
            fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
    
    # === ATTACH RATE COMPARISON ===
    if metrics.get("Attach Rate Before") and metrics.get("Attach Rate After") and metrics.get("Account"):
        st.markdown("---")
        st.markdown("#### 📈 Attach Rate: 30 Days Before vs After Training")
        
        attach_df = df[df["Attach Rate Before"].notna() & df["Attach Rate After"].notna()]
        if len(attach_df) > 0:
            attach_col1, attach_col2 = st.columns([2, 1])
            
            with attach_col1:
                attach_data = attach_df.groupby("Account").agg(
                    before=("Attach Rate Before", "mean"),
                    after=("Attach Rate After", "mean")
                ).reset_index()
                # Convert if 0-1 scale
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
                fig.update_layout(barmode="group", height=350, margin=dict(l=0, r=0, t=10, b=0),
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
    
    # === STORE PERFORMANCE ===
    if metrics.get("Store") and (metrics.get("Pass Flag") or metrics.get("Assessment Score")):
        st.markdown("---")
        st.markdown("### 🏪 Store Performance")
        
        store_col1, store_col2 = st.columns([2, 1])
        
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
            
            store_data = store_data.sort_values("Pass Rate" if "Pass Rate" in store_data.columns else "Records", ascending=False)
            
            col_config = {}
            if "Pass Rate" in store_data.columns:
                col_config["Pass Rate"] = st.column_config.ProgressColumn("Pass Rate %", min_value=0, max_value=100, format="%.1f%%")
            
            st.dataframe(store_data, use_container_width=True, height=400, column_config=col_config)
        
        with store_col2:
            st.metric("Stores Trained", df["Store"].nunique())
            if "Pass Rate" in store_data.columns:
                st.markdown("**🏆 Top Stores**")
                for _, row in store_data.nlargest(5, "Pass Rate").iterrows():
                    st.markdown(f'• {row["Store"]} — **{row["Pass Rate"]:.0f}%**')
                st.markdown("**⚠️ Needs Attention**")
                for _, row in store_data.nsmallest(3, "Pass Rate").iterrows():
                    st.markdown(f'• {row["Store"]} — **{row["Pass Rate"]:.0f}%**')
    
    # === TRAINING VOLUME TREND ===
    if metrics.get("Date"):
        st.markdown("---")
        trend_col, trainer_col = st.columns(2)
        
        with trend_col:
            st.markdown("#### 📅 Training Volume Trend")
            df_trend = df.set_index("Date").resample("W").size().reset_index(name="Sessions")
            fig = px.area(df_trend, x="Date", y="Sessions", color_discrete_sequence=["#00BAC7"])
            fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
        
        if metrics.get("Trainer") and metrics.get("Pass Flag"):
            with trainer_col:
                st.markdown("#### 👤 Trainer Performance")
                t_data = df.groupby("Trainer").agg(
                    sessions=("Date", "count"),
                    pass_rate=("Pass Flag", "mean")
                ).reset_index()
                t_data["Pass Rate (%)"] = (t_data["pass_rate"] * 100).round(1)
                t_data = t_data.sort_values("Pass Rate (%)", ascending=False)
                
                fig = px.bar(t_data, x="Trainer", y="Pass Rate (%)", color="sessions",
                             color_continuous_scale=[[0, "#e6f9fa"], [0.5, "#00BAC7"], [1, "#170F4F"]])
                fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0))
                st.plotly_chart(fig, use_container_width=True)
    
    # === DATA AVAILABILITY SECTION ===
    st.markdown("---")
    with st.expander("📋 Data Availability Report", expanded=False):
        st.markdown("**Which metrics are available in your dataset:**")
        
        avail_col1, avail_col2 = st.columns(2)
        
        metric_groups = {
            "Core Fields": ["Date", "Trainer", "Account", "Country", "Store", "Training Name", "Training Type", "Training ID"],
            "Learner Data": ["Trainee Name", "Trainee Code", "Assessment Score", "Assessment Result", "Pass Flag"],
            "Optional Metrics": ["Total Invited", "Total Attended", "Training Hours", "Attach Rate Before", "Attach Rate After"],
        }
        
        with avail_col1:
            for group, fields in list(metric_groups.items())[:2]:
                st.markdown(f"**{group}**")
                for field in fields:
                    present = metrics.get(field, False)
                    icon = "✅" if present else "❌"
                    # Calculate fill rate
                    if field in COLUMN_ALIASES.values() or field in df.columns:
                        canonical = field
                        if canonical in df.columns:
                            fill = df[canonical].notna().sum() / len(df) * 100
                            fill_str = f" ({fill:.0f}% filled)"
                        else:
                            fill_str = ""
                    else:
                        fill_str = ""
                    
                    color = "data-avail-present" if present else "data-avail-missing"
                    st.markdown(f'<span class="{color}">{icon} {field}{fill_str}</span>', unsafe_allow_html=True)
                st.markdown("")
        
        with avail_col2:
            for group, fields in list(metric_groups.items())[2:]:
                st.markdown(f"**{group}**")
                for field in fields:
                    present = metrics.get(field, False)
                    icon = "✅" if present else "❌"
                    if field in df.columns:
                        fill = df[field].notna().sum() / len(df) * 100
                        fill_str = f" ({fill:.0f}% filled)"
                    else:
                        fill_str = ""
                    color = "data-avail-present" if present else "data-avail-missing"
                    st.markdown(f'<span class="{color}">{icon} {field}{fill_str}</span>', unsafe_allow_html=True)
            
            st.markdown("")
            st.markdown("**Dataset Info**")
            st.markdown(f"• Rows: **{len(df):,}**")
            st.markdown(f"• Columns: **{len(df.columns)}**")
            st.markdown(f"• Column names: {', '.join(df.columns[:15])}{'...' if len(df.columns) > 15 else ''}")
    
    # === RAW DATA TABLE ===
    with st.expander("📋 View Raw Data", expanded=False):
        st.dataframe(df, use_container_width=True, height=400)
    
    # === EXPORT ===
    st.markdown("---")
    exp1, exp2, _ = st.columns([1, 1, 2])
    with exp1:
        st.download_button("⬇️ Download CSV", df.to_csv(index=False), "training_data.csv", "text/csv")
    with exp2:
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            df.to_excel(w, index=False, sheet_name="Data")
        st.download_button("⬇️ Download Excel", buf.getvalue(), "training_dashboard.xlsx",
                          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

else:
    st.markdown("---")
    st.info("👈 Select a data source from the sidebar to get started.")
    
    st.markdown("### 📋 Supported Data Formats")
    st.markdown("""
    The dashboard **auto-detects** your columns. It works with any combination of these fields:
    
    | Field | Aliases Recognized |
    |-------|-------------------|
    | Date | `Date`, `Date of Training`, `Training Date` |
    | Trainer | `Trainer`, `Trainer Name`, `Facilitator` |
    | Account | `Account`, `Partner Name`, `Partner`, `Client` |
    | Country | `Country`, `Market`, `Region` |
    | Store | `Store`, `Store Name`, `Branch`, `Location`, `Outlet` |
    | Training Name | `Training Title`, `Course`, `Program`, `Module` |
    | Training Type | `Training Method`, `Type`, `Delivery Mode` |
    | Assessment | `Training Assessment Score %`, `Score`, `Grade` |
    | Pass/Fail | `Pass Flag`, `Training Assessment Result`, `Status` |
    | Attach Rate | `Attach Rate Before`, `Attach Rate After` |
    | Hours | `Training Hours`, `Duration`, `Duration (Hours)` |
    
    **No mandatory columns** — the dashboard adapts to whatever you upload.
    """)
