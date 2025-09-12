import io
from typing import Optional, List

import pandas as pd
import streamlit as st

# ---------- Page setup ----------
st.set_page_config(page_title="Upload Excel/CSV → Download CSV (Unicode)", page_icon="📤", layout="wide")
st.title("📤 Upload Excel/CSV → 📥 Download CSV (Unicode)")
st.caption("Upload .csv / .xlsx / .xls, choose the starting row (skip initial rows), preview data, and download as Unicode CSV (utf-8-sig).")

# ---------- Helpers ----------
def _read_csv(file, skiprows: int) -> pd.DataFrame:
    \"\"\"Read CSV with skiprows and robust encoding/separator fallbacks.\"\"\"
    try:
        return pd.read_csv(file, skiprows=skiprows)
    except UnicodeDecodeError:
        file.seek(0)
        try:
            return pd.read_csv(file, skiprows=skiprows, encoding=\"latin-1\")
        except Exception:
            file.seek(0)
            # Let pandas sniff separator when everything else fails
            return pd.read_csv(file, skiprows=skiprows, sep=None, engine=\"python\")

def _read_excel(file, suffix: str, sheet_name: Optional[str], skiprows: int) -> pd.DataFrame:
    \"\"\"Read Excel with the proper engine and skiprows.\"\"\"
    if suffix == \".xlsx\":
        return pd.read_excel(file, sheet_name=sheet_name, engine=\"openpyxl\", skiprows=skiprows)
    # .xls uses xlrd
    return pd.read_excel(file, sheet_name=sheet_name, engine=\"xlrd\", skiprows=skiprows)

def _bytes_buffer(uploaded_file) -> io.BytesIO:
    data = uploaded_file.read()
    return io.BytesIO(data)

# ---------- Sidebar options ----------
st.sidebar.header(\"Options\")
skiprows = st.sidebar.number_input(
    \"Skip this many rows before reading (0 = read from first row)\",
    min_value=0, value=0, step=1
)

# ---------- Uploader ----------
uploaded = st.file_uploader(
    \"Upload a .csv, .xlsx, or .xls file\",
    type=[\"csv\", \"xlsx\", \"xls\"],
    accept_multiple_files=False,
)

# Persistent state for df
if \"df\" not in st.session_state:
    st.session_state.df = None

if uploaded:
    name = uploaded.name
    suffix = name[name.rfind(\".\"):].lower() if \".\" in name else \"\"
    buf = _bytes_buffer(uploaded)

    if suffix in {\".xlsx\", \".xls\"}:
        # Allow the user to pick a sheet
        try:
            if suffix == \".xlsx\":
                xls = pd.ExcelFile(buf, engine=\"openpyxl\")
            else:
                xls = pd.ExcelFile(buf, engine=\"xlrd\")
            sheets: List[str] = xls.sheet_names
        except Exception as e:
            st.error(f\"Failed to read Excel file: {e}\")
            sheets = []

        if sheets:
            sheet = st.selectbox(\"Select sheet to load\", sheets, index=0)
            try:
                buf.seek(0)
                df = _read_excel(buf, suffix, sheet, skiprows=skiprows)
                st.session_state.df = df
            except Exception as e:
                st.error(f\"Error reading sheet '{sheet}': {e}\")
        else:
            st.warning(\"No sheets found or file could not be read.\")

    elif suffix == \".csv\":
        try:
            df = _read_csv(buf, skiprows=skiprows)
            st.session_state.df = df
        except Exception as e:
            st.error(f\"Error reading CSV: {e}\")
    else:
        st.error(\"Unsupported file type.\")

# ---------- Preview & Download ----------
df = st.session_state.df

if df is not None:
    st.subheader(\"👀 Preview\")
    st.dataframe(df, use_container_width=True)

    st.subheader(\"📥 Download CSV (Unicode utf-8-sig)\")
    file_base = uploaded.name.rsplit(\".\", 1)[0] if uploaded else \"data\"
    # Use utf-8-sig (includes BOM) so Excel recognizes Unicode properly
    csv_bytes = df.to_csv(index=False).encode(\"utf-8-sig\")
    st.download_button(
        label=\"Download CSV\",\n        data=csv_bytes,\n        file_name=f\"{file_base}.csv\",\n        mime=\"text/csv\",\n    )\nelse:\n    st.info(\"Upload a file to begin.\")\n
