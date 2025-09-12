
import io
from typing import Optional, List

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Upload Excel/CSV → Download CSV", page_icon="📤", layout="wide")
st.title("📤 Upload Excel/CSV → 📥 Download CSV")
st.caption("Minimal app: upload a .csv / .xlsx / .xls and download as CSV.")

def _read_csv(file) -> pd.DataFrame:
    # Try UTF-8 first; fallback to latin-1; else let pandas sniff the separator.
    try:
        return pd.read_csv(file,skiprows=12)
    except UnicodeDecodeError:
        file.seek(0)
        try:
            return pd.read_csv(file, skiprows=12, encoding="latin-1")
        except Exception:
            file.seek(0)
            return pd.read_csv(file, sep=None, engine="python")

def _read_excel(file, suffix: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
    # Use openpyxl for .xlsx and xlrd for .xls
    if suffix == ".xlsx":
        return pd.read_excel(file, sheet_name=sheet_name, engine="openpyxl")
    return pd.read_excel(file, sheet_name=sheet_name, engine="xlrd")

def _bytes_buffer(uploaded_file) -> io.BytesIO:
    data = uploaded_file.read()
    return io.BytesIO(data)

uploaded = st.file_uploader(
    "Upload a .csv, .xlsx, or .xls file",
    type=["csv", "xlsx", "xls"],
    accept_multiple_files=False,
)

if "df" not in st.session_state:
    st.session_state.df = None

if uploaded:
    name = uploaded.name
    suffix = name[name.rfind("."):].lower() if "." in name else ""
    buf = _bytes_buffer(uploaded)

    if suffix in {".xlsx", ".xls"}:
        # List sheets then read the chosen sheet
        try:
            if suffix == ".xlsx":
                xls = pd.ExcelFile(buf, engine="openpyxl")
            else:
                xls = pd.ExcelFile(buf, engine="xlrd")
            sheets: List[str] = xls.sheet_names
        except Exception as e:
            st.error(f"Failed to read Excel file: {e}")
            sheets = []

        if sheets:
            sheet = st.selectbox("Select sheet to load", sheets, index=0)
            try:
                buf.seek(0)
                df = _read_excel(buf, suffix, sheet)
                st.session_state.df = df
            except Exception as e:
                st.error(f"Error reading sheet '{sheet}': {e}")
        else:
            st.warning("No sheets found or file could not be read.")

    elif suffix == ".csv":
        try:
            df = _read_csv(buf)
            st.session_state.df = df
        except Exception as e:
            st.error(f"Error reading CSV: {e}")
    else:
        st.error("Unsupported file type.")

df = st.session_state.df

if df is not None:
    st.subheader("👀 Preview")
    st.dataframe(df, use_container_width=True)

    st.subheader("📥 Download CSV")
    file_base = uploaded.name.rsplit(".", 1)[0] if uploaded else "data"
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download my_google.csv",
        data=csv_bytes,
        file_name=f"{file_base}.csv",
        mime="text/csv",
    )
else:
    st.info("Upload a file to begin.")
