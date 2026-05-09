"""
data_loader.py — DVN Group 7
Loads and parses ABS 6401.0 Consumer Price Index Excel files.
ABS format: Rows 0-9 = metadata, Row 9 = Series IDs, Row 10+ = data.
"""

import pandas as pd
import os
import streamlit as st

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

# ──────────────────────────────────────────────────────────────────────
# Helper: read a single ABS Data sheet
# ──────────────────────────────────────────────────────────────────────

def _read_data_sheet(filepath, sheet_name="Data1"):
    """Read one ABS Time-Series data sheet → (DataFrame, {series_id: description})."""
    raw = pd.read_excel(filepath, sheet_name=sheet_name, header=None, engine="openpyxl")
    descriptions = raw.iloc[0, 1:].tolist()
    series_ids = [str(s).strip() for s in raw.iloc[9, 1:].tolist()]

    data = raw.iloc[10:].copy()
    data.columns = ["date"] + series_ids
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data = data.dropna(subset=["date"]).set_index("date").sort_index()

    for col in data.columns:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    id_desc = {sid: str(d) for sid, d in zip(series_ids, descriptions) if pd.notna(d)}
    return data, id_desc


def _read_index_sheet(filepath):
    """Read Index sheet → {series_id: full_description}."""
    raw = pd.read_excel(filepath, sheet_name="Index", header=None, engine="openpyxl")
    mapping = {}
    for i in range(10, len(raw)):
        parts = []
        for j in range(3):
            v = raw.iloc[i, j]
            if pd.notna(v) and str(v).strip():
                parts.append(str(v).strip())
        sid = raw.iloc[i, 4]
        if pd.notna(sid) and parts:
            mapping[str(sid).strip()] = " > ".join(parts)
    return mapping


def _parse_desc(desc):
    """Split ABS description 'Measure ; Group ; City ; ...' → dict.
    Handles both ';' (Data sheet) and ' > ' (Index sheet) separators."""
    desc_str = str(desc)
    # Normalise: Index sheet uses ' > ', Data sheet uses ' ; '
    if " > " in desc_str and ";" not in desc_str:
        parts = [p.strip() for p in desc_str.split(" > ")]
    else:
        parts = [p.strip() for p in desc_str.split(";")]
    return {
        "measure": parts[0] if len(parts) > 0 else "",
        "group": parts[1] if len(parts) > 1 else "",
        "city": parts[2] if len(parts) > 2 else "",
    }



@st.cache_data(ttl=3600)
def load_table9():
    """Monthly CPI index numbers by expenditure group and city."""
    fp = os.path.join(DATA_DIR, "CPI-Capital-cities", "640109.xlsx")
    data, desc_map = _read_data_sheet(fp, "Data1")
    index_map = _read_index_sheet(fp)

    # Merge descriptions (Index sheet has full text)
    full_map = {**desc_map, **index_map}

    records = []
    for sid in data.columns:
        desc = full_map.get(sid, "")
        info = _parse_desc(desc)
        group = info["group"]
        city = info["city"]
        if not group or not city:
            continue
        series = data[sid].dropna()
        for date, value in series.items():
            records.append({
                "date": date, "group": group, "city": city,
                "index_value": value, "series_id": sid,
            })

    df = pd.DataFrame(records)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df


# ──────────────────────────────────────────────────────────────────────
# Table 11 — Annual % Change (from corresponding period of prev year)
# ──────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def load_table11():
    """Annual percentage change by group and city."""
    fp = os.path.join(DATA_DIR, "CPI-Capital-cities", "6401011.xlsx")
    all_data = []
    all_desc = {}

    for sheet in ["Data1", "Data2", "Data3", "Data4", "Data5"]:
        try:
            data, desc = _read_data_sheet(fp, sheet)
            all_data.append(data)
            all_desc.update(desc)
        except Exception:
            continue

    index_map = _read_index_sheet(fp)
    full_map = {**all_desc, **index_map}

    combined = pd.concat(all_data, axis=1) if all_data else pd.DataFrame()
    # Remove duplicate columns
    combined = combined.loc[:, ~combined.columns.duplicated()]

    records = []
    for sid in combined.columns:
        desc = full_map.get(sid, "")
        info = _parse_desc(desc)
        group = info["group"]
        city = info["city"]
        if not group or not city:
            continue
        series = combined[sid].dropna()
        for date, value in series.items():
            records.append({
                "date": date, "group": group, "city": city,
                "annual_change_pct": value, "series_id": sid,
            })

    df = pd.DataFrame(records)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df

# ──────────────────────────────────────────────────────────────────────
# Table 17 — Quarterly Historical CPI (All Cities, back to 1948)
# ──────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def load_table17():
    """Quarterly CPI by city (historical, from 1948)."""
    fp = os.path.join(DATA_DIR, "CPI-Quarterly", "6401017.xlsx")
    data, desc_map = _read_data_sheet(fp, "Data1")
    index_map = _read_index_sheet(fp)
    full_map = {**desc_map, **index_map}

    records = []
    for sid in data.columns:
        d = full_map.get(sid, desc_map.get(sid, ""))
        info = _parse_desc(d)
        series = data[sid].dropna()
        for date, value in series.items():
            records.append({
                "date": date, "description": d,
                "measure": info["measure"],
                "city": info["group"],  # For Table 17 structure
                "value": value, "series_id": sid,
            })

    df = pd.DataFrame(records)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df
