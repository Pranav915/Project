# src/

This folder contains all source code for the Group 7 Streamlit dashboard.

## Folder Purpose

| File | Purpose |
|---|---|
| `app.py` | Main Streamlit entry point — run this to launch the dashboard |
| `example.py` | Annotated walkthrough of coding conventions (not part of live dashboard) |
| `clean.py` | Data cleaning script — reads raw xlsx from `../data/`, outputs cleaned CSVs |
| `pages/` | (optional) Additional Streamlit pages if multi-page layout is used |
| `utils/` | (optional) Helper modules for chart builders and shared transforms |

## How to Run the Dashboard

### Prerequisites

- Python 3.8 or higher

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs: `streamlit`, `pandas`, `plotly`, and `openpyxl`.

### 2. Run the Dashboard

```bash
cd src
streamlit run app.py
```

The dashboard will open automatically in your browser at **http://localhost:8501**.

### 3. Required Data Files

Ensure the following Excel files exist in the `data/` directory (relative to the project root):

| File Path | Description |
|---|---|
| `data/CPI-Capital-cities/640109.xlsx` | Table 9 — Monthly CPI index numbers by group and city |
| `data/CPI-Capital-cities/6401011.xlsx` | Table 11 — Annual percentage change by group and city |
| `data/CPI-Quarterly/6401017.xlsx` | Table 17 — Quarterly historical CPI (back to 1948) |

---

## Who works here

**Dhrishita** — Dashboard Developer: `app.py`, `pages/`, `utils/`  
**Desmond** — Data Analyst: `clean.py` (produces cleaned CSVs loaded by the dashboard)

