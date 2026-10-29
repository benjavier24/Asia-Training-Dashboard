"""Manager commentary storage — swappable backend (Spec 3b).

Lets training managers save written insights that persist across sessions and
build up as historical data. The dashboard talks to this module through a small,
backend-agnostic interface so the underlying store can be swapped later
(Google Sheets now → SharePoint on the bolttech tenant when IT access lands)
WITHOUT changing the dashboard UI code.

Design principles:
- DEGRADE GRACEFULLY. If storage isn't configured (no secret / library missing),
  every function returns a safe value and sets a human-readable reason, so the
  dashboard never crashes — the commentary section just shows "not configured".
- READS are cached briefly so the history view doesn't hit the Sheet on every
  rerun; writes clear that cache.

Expected Streamlit secrets (see the setup guide):
  [gcp_service_account]  -> the service-account JSON fields
  [commentary]
  sheet_url = "https://docs.google.com/spreadsheets/d/<id>/edit"
"""

from __future__ import annotations

import datetime as _dt
import pandas as pd
import streamlit as st

# The canonical columns of the commentary store (must match the Sheet header).
COMMENTARY_COLUMNS = [
    "timestamp", "author", "market", "account", "campaign", "period", "section", "text",
]

# Allowed section tags (kept in sync with the dashboard UI).
SECTIONS = ("went_well", "opportunity", "key_action", "general")

_WORKSHEET_NAME = "Commentary"


def _availability():
    """Return (available: bool, reason: str). Checks config + libraries without
    raising. Safe to call on every rerun."""
    # Secrets present?
    try:
        has_sa = "gcp_service_account" in st.secrets
        has_cfg = "commentary" in st.secrets and "sheet_url" in st.secrets["commentary"]
    except Exception:
        return False, "Streamlit secrets are not available in this environment."
    if not has_sa or not has_cfg:
        return False, "Commentary storage is not configured yet (missing Google Sheets credentials)."
    # Libraries installed?
    try:
        import gspread  # noqa: F401
        from google.oauth2.service_account import Credentials  # noqa: F401
    except Exception:
        return False, "Required libraries (gspread / google-auth) are not installed."
    return True, ""


def is_available():
    """True when commentary storage is ready to read/write."""
    return _availability()[0]


def unavailable_reason():
    """Human-readable reason storage is unavailable (empty string if available)."""
    return _availability()[1]


@st.cache_resource(show_spinner=False)
def _get_worksheet():
    """Open (once) the Commentary worksheet. Cached as a resource so we don't
    re-auth on every rerun. Returns the worksheet or raises — callers guard with
    is_available() first."""
    import gspread
    from google.oauth2.service_account import Credentials

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]), scopes=scopes
    )
    client = gspread.authorize(creds)
    sh = client.open_by_url(st.secrets["commentary"]["sheet_url"])
    try:
        ws = sh.worksheet(_WORKSHEET_NAME)
    except Exception:
        # Create the worksheet with headers if it doesn't exist yet.
        ws = sh.add_worksheet(title=_WORKSHEET_NAME, rows=1000, cols=len(COMMENTARY_COLUMNS))
        ws.update([COMMENTARY_COLUMNS])
    return ws


@st.cache_data(ttl=60, show_spinner=False)
def _load_all_raw():
    """Load all commentary rows as a DataFrame (cached 60s). Internal."""
    ws = _get_worksheet()
    records = ws.get_all_records()  # list of dicts keyed by header row
    if not records:
        return pd.DataFrame(columns=COMMENTARY_COLUMNS)
    df = pd.DataFrame(records)
    # Ensure all expected columns exist even if the sheet is partial.
    for c in COMMENTARY_COLUMNS:
        if c not in df.columns:
            df[c] = ""
    return df[COMMENTARY_COLUMNS]


def load_commentary(market=None, account=None, campaign=None):
    """Return commentary rows (newest first), optionally filtered by scope.

    Returns (df, error). On any failure returns (empty df, reason) — never raises.
    """
    ok, reason = _availability()
    if not ok:
        return pd.DataFrame(columns=COMMENTARY_COLUMNS), reason
    try:
        df = _load_all_raw().copy()
    except Exception as e:
        return pd.DataFrame(columns=COMMENTARY_COLUMNS), f"Could not read commentary store ({type(e).__name__})."

    if market:
        df = df[df["market"].astype(str) == str(market)]
    if account:
        df = df[df["account"].astype(str) == str(account)]
    if campaign:
        df = df[df["campaign"].astype(str) == str(campaign)]

    # Newest first by timestamp (string ISO sorts correctly).
    if "timestamp" in df.columns and len(df) > 0:
        df = df.sort_values("timestamp", ascending=False)
    return df.reset_index(drop=True), ""


def save_commentary(author, market, account, campaign, period, section, text):
    """Append one commentary row. Returns (ok: bool, message: str). Never raises."""
    ok, reason = _availability()
    if not ok:
        return False, reason
    if not (text and str(text).strip()):
        return False, "Please enter some text before saving."
    if not (author and str(author).strip()):
        return False, "Please select who you are (author) before saving."
    if section not in SECTIONS:
        section = "general"
    try:
        ws = _get_worksheet()
        row = [
            _dt.datetime.now().isoformat(timespec="seconds"),
            str(author).strip(),
            str(market or ""),
            str(account or ""),
            str(campaign or ""),
            str(period or ""),
            str(section),
            str(text).strip(),
        ]
        ws.append_row(row, value_input_option="USER_ENTERED")
        _load_all_raw.clear()  # invalidate the read cache so history refreshes
        return True, "Saved."
    except Exception as e:
        return False, f"Could not save to the commentary store ({type(e).__name__})."
