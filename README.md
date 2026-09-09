# Asia-Training-Dashboard

Regional training performance dashboard for all bolttech markets, built with Streamlit.

## Live app

**https://benjavier24-asia-training-dashboard-app-pgqezi.streamlit.app/**

The app is deployed on Streamlit Cloud and auto-deploys from the `main` branch of this
repository — every push to `main` triggers a rebuild.

## Data source

The dashboard runs in **upload mode** on the cloud (it cannot read local or OneDrive file
paths directly). Load the data through the app's upload control each time.

Master file (SharePoint):
https://bolttechio.sharepoint.com/:x:/s/SEATrainingSite/IQCmb4CztJcmTq5QCPy-h54KAbUdZARp7SWeZDL-c9frFnE

> **Always upload a fresh, complete export from OneDrive.** The export must contain **all
> markets** and must not be truncated. An older master file had hit Excel's ~1,048,576-row
> limit, which pushed most non-Indonesia markets out of the sheet (e.g. only 12 Philippines
> rows survived). Uploading a truncated file makes those markets look nearly empty and the
> numbers unreliable.

## Passing standard

Pass/fail is derived from each learner's normalized assessment score (not the source
pass/fail flags, which are inconsistent). The bar is **tiered by training type**:

| Training type            | Passing threshold |
|--------------------------|-------------------|
| Foundation               | 70%               |
| Activation               | 80%               |
| Reinforcement            | 80%               |
| Unspecified / blank type | 70% (default)     |

Applied uniformly across all markets. Learners with **no assessment score** are excluded
from the pass rate (not counted as fails). Rows with a blank training type default to 70%
today and will automatically pick up their correct tier once the raw training-type data is
cleaned up — no code change needed.

## Tests

Regression tests live in `test_session_logic.py`:

```
python test_session_logic.py
```
