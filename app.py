"""
Streamlit App: Upload Excel/CSV and Download as CSV

Features
- Upload: .csv, .xlsx, .xls (sheet picker for Excel)
- Preview & quick cleaning (drop duplicates / NA)
- Basic column selection & type casting
- Download processed data as CSV
- One-click downloads for **requirements.txt** and **README.md**
- Ready for Streamlit Community Cloud (or Docker) deployment

Deploy on Streamlit Community Cloud
1) Download **requirements.txt** and **README.md** from the app sidebar (or copy from this header).
2) Commit `app.py`, `requirements.txt`, and `README.md` to a GitHub repo.
3) Go to https://share.streamlit.io, connect your repo, select `app.py`, Deploy.

requirements.txt (template)
------------------------------------------------
streamlit>=1.35
pandas>=2.0
openpyxl>=3.1
xlrd==2.0.1
pyarrow>=15.0  # optional, speeds up some pandas ops

Optional: Dockerfile (for any host)
------------------------------------------------
# Use Python slim image
# docker build -t csv-uploader . && docker run -p 8501:8501 csv-uploader
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY app.py ./
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

Local run
- python -m pip install -r requirements.txt
- streamlit run app.py
"""

import io
from textwrap import dedent
from typing import Optional, List

import pandas as pd
import streamlit as st

# ---------- Page setup ----------
st.set_page_config(
    page_title="Excel/CSV Uploader → CSV Downloader",
    page_icon="📤",
    layout="wide",
)

st.title("📤 Upload Excel/CSV → 📥 Download CSV")
st.caption("Upload your data, make quick tweaks, and export a clean CSV. Works with **.csv**, **.xlsx**, and **.xls**.")

# ---------- Sidebar: Options & helper downloads ----------
st.sidebar.header("Options")
keep_index = st.sidebar.checkbox("Keep DataFrame index in preview (not saved)", value=False)

REQ_TXT = dedent(
    """
    streamlit>=1.35
    pandas>=2.0
    openpyxl>=3.1
    xlrd==2.0.1
    pyarrow>=15.0
    """
).strip()

README_MD = dedent(
    """
    # Streamlit Upload Excel/CSV → Download CSV

    This app lets you upload `.csv`, `.xlsx`, `.xls`, preview/clean lightly, and download as a clean CSV.

    ## Deploy (Streamlit Community Cloud)
    1. Put `app.py` and `requirements.txt` into a GitHub repo.
    2. Go to https://share.streamlit.io and deploy with `app.py` as the entry.

    ## Run locally
    ```bash
    pip install -r requirements.txt
    streamlit run app.py
    ```

    ## Notes
    - `.xlsx` uses **openpyxl**; `.xls` uses **xlrd==2.0.1**.
    - If your CSV has weird separators/encodings, the app falls back to auto-detection.
    """
).strip()

st.sidebar.download_button(
    "Download requirements.txt",
    data=REQ_TXT,
    file_name="requirements.txt",
    mime="text/plain",
)
st.sidebar.download_button(
    "Download README.md",
    data=README_MD,
    file_name="README.md",
    mime="text/markdown",
)


def _read_csv(file) -> pd.DataFrame:
    """Read CSV with a couple of fallbacks for encoding/dialect."""
    try:
        return pd.read_csv(file)
    except UnicodeDecodeError:
        file.seek(0)
        try:
            return pd.read_csv(file, encoding="latin-1")
        except Exception:
            file.seek(0)
            return pd.read_csv(file, sep=None, engine="python")


def _read_excel(file, suffix: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
    """Read Excel handling .xlsx vs .xls engines explicitly; show friendly errors if engines missing."""
    try:
        if suffix == ".xlsx":
            return pd.read_excel(file, sheet_name=sheet_name, engine="openpyxl")
        return pd.read_excel(file, sheet_name=sheet_name, engine="xlrd")
    except ImportError as e:
        st.error(
            "Missing Excel engine. Add the right dependency to requirements.txt — "
            "`openpyxl` for .xlsx or `xlrd==2.0.1` for .xls.

" + str(e)
        )
        raise


def _bytes_to_buffer(uploaded_file) -> io.BytesIO:
    """Return a BytesIO so we can seek multiple times safely."""
    data = uploaded_file.read()
    return io.BytesIO(data)


# ---------- File Uploader ----------
uploaded = st.file_uploader(
    "Upload a .csv, .xlsx, or .xls file",
    type=["csv", "xlsx", "xls"],
    accept_multiple_files=False,
    help="Large files may take a few seconds to load. For Excel, you'll choose a sheet after upload.",
)

if "df" not in st.session_state:
    st.session_state.df = None

if uploaded:
    name = uploaded.name
    suffix = name[name.rfind(".") :].lower() if "." in name else ""
    buffer = _bytes_to_buffer(uploaded)

    # Excel: let user choose sheet first
    if suffix in {".xlsx", ".xls"}:
        try:
            if suffix == ".xlsx":
                xls = pd.ExcelFile(buffer, engine="openpyxl")
            else:
                xls = pd.ExcelFile(buffer, engine="xlrd")
            sheets: List[str] = xls.sheet_names
        except Exception as e:
            st.error(f"Failed to read Excel sheets: {e}")
            sheets = []

        if sheets:
            sheet_choice = st.selectbox("Select sheet", sheets, index=0)
            try:
                buffer.seek(0)
                df = _read_excel(buffer, suffix, sheet_choice)
                st.session_state.df = df
            except Exception as e:
                st.error(f"Error reading Excel sheet '{sheet_choice}': {e}")
        else:
            st.warning("No sheets found or file could not be read.")

    elif suffix == ".csv":
        try:
            df = _read_csv(buffer)
            st.session_state.df = df
        except Exception as e:
            st.error(f"Error reading CSV: {e}")
    else:
        st.error("Unsupported file type.")

# ---------- Data Preview & Quick Ops ----------
df = st.session_state.df

if df is not None:
    st.subheader("👀 Preview")

    # Column selection
    with st.expander("Select columns to keep", expanded=False):
        cols = st.multiselect("Columns", options=list(df.columns), default=list(df.columns))
        if cols:
            df = df[cols]
            st.session_state.df = df

    # Quick cleaning options
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.checkbox("Drop duplicate rows"):
            before = len(df)
            df = df.drop_duplicates()
            st.session_state.df = df
            st.write(f"Removed **{before - len(df)}** duplicates.")
    with col2:
        if st.checkbox("Drop rows with any NA"):
            before = len(df)
            df = df.dropna(how="any")
            st.session_state.df = df
            st.write(f"Removed **{before - len(df)}** rows with NA.")
    with col3:
        if st.checkbox("Strip whitespace in string columns"):
            obj_cols = df.select_dtypes(include=["object", "string"]).columns
            df[obj_cols] = df[obj_cols].apply(lambda s: s.str.strip())
            st.session_state.df = df
            st.write(f"Stripped whitespace in **{len(obj_cols)}** columns.")

    # Type casting helper
    with st.expander("Type casting (optional)"):
        cast_col = st.selectbox("Choose a column to cast", options=["(none)"] + list(df.columns))
        if cast_col != "(none)":
            cast_to = st.selectbox("Cast to", options=["string", "int", "float", "datetime"])
            if st.button("Apply cast"):
                try:
                    if cast_to == "string":
                        df[cast_col] = df[cast_col].astype("string")
                    elif cast_to == "int":
                        df[cast_col] = pd.to_numeric(df[cast_col], errors="coerce").astype("Int64")
                    elif cast_to == "float":
                        df[cast_col] = pd.to_numeric(df[cast_col], errors="coerce").astype(float)
                    else:
                        df[cast_col] = pd.to_datetime(df[cast_col], errors="coerce")
                    st.session_state.df = df
                    st.success(f"Cast '{cast_col}' → {cast_to}")
                except Exception as e:
                    st.error(f"Casting error: {e}")

    st.dataframe(df if keep_index else df.reset_index(drop=True), use_container_width=True)

    # ---------- Download CSV ----------
    st.subheader("📥 Download")
    suggested = (uploaded.name.rsplit(".", 1)[0] if uploaded else "data") + "_clean.csv"
    csv_bytes = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download CSV",
        data=csv_bytes,
        file_name=suggested,
        mime="text/csv",
    )
else:
    st.info("Upload a file to begin.")

# ---------- Footer ----------
st.markdown("---")
st.caption(
    "Tip: For old **.xls** files, make sure `xlrd==2.0.1` is in **requirements.txt**. For **.xlsx**, `openpyxl` is required."
)
