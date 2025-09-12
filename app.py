
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
        return pd.read_csv(file)
    except UnicodeDecodeError:
        file.seek(0)
        try:
            return pd.read_csv(file, encoding="latin-1")
        except Exception:
            file.seek(0)
            return pd.read_csv(file, sep=None, engine="python")

def _read_excel(file, suffix: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
    # Use openpyxl for .xlsx and xlrd for .xls
    if suffix == ".xlsx":
        return pd.read_excel(file,skiprows=12, sheet_name=sheet_name, engine="openpyxl")
    return pd.read_excel(file,skiprows=12, sheet_name=sheet_name, engine="xlrd")

def _bytes_buffer(uploaded_file) -> io.BytesIO:
    data = uploaded_file.read()
    return io.BytesIO(data)

from datetime import datetime, timedelta
import sys

# parse week pattern
def parse_week_pattern(week_pattern):
    """Parses the 'Week pattern' string and returns a list of active week numbers."""
    active_weeks = []
    for i, char in enumerate(week_pattern):
        if char.isdigit():
            active_weeks.append(i + 1) # Week number corresponds to index + 1
    return active_weeks

# extract date from the pattern
def get_dates_for_pattern(start_date_str, day_of_week, active_weeks):
    """Calculates the dates for each active week based on the start date and day of the week."""
    dates = []
    parsed = False
    for fmt in ('%m/%d/%Y', '%m/%d/%y'):
        try:
            start_date = datetime.strptime(start_date_str, fmt)
            parsed = True
            break
        except ValueError:
            pass
    if not parsed and sys.platform.startswith('win'):
        for fmt in ('%#m/%#d/%Y', '%#m/%#d/%y'):
            try:
                start_date = datetime.strptime(start_date_str, fmt)
                parsed = True
                break
            except ValueError:
                pass
    if not parsed:
        raise ValueError(f"Could not parse date string: {start_date_str}")


    # Adjust start date to the correct day of the week if needed
    start_day_of_week = start_date.isoweekday() + 1 if start_date.isoweekday() != 7 else 8 # Monday is 2, Sunday is 8
    days_difference = day_of_week - start_day_of_week
    if days_difference < 0:
      days_difference += 7
    adjusted_start_date = start_date + timedelta(days=days_difference)

    if not active_weeks:
        return dates # Return empty list if no active weeks

    firstweek = active_weeks[0]


    for week_num in active_weeks:
        # Calculate the date for the specific day of the week in the given week number
        # Assuming the first week in the pattern corresponds to the week of the start date
        date_of_week = adjusted_start_date + timedelta(weeks=week_num - firstweek)
        dates.append(date_of_week)
    return dates
    
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
    my_list = df
    
    #Display data section
    st.subheader("👀 Your EGOV Schedule")    
    st.dataframe(df, use_container_width=True)

    # Convert my schedule to google calendar schedule ---------------------------------------
    
    # Apply the helper functions to the DataFrame
    my_list_2 = my_list.copy()
    my_list_2['active_weeks'] = my_list_2['Week Pattern'].apply(parse_week_pattern)
    my_list_2['class_dates'] = my_list_2.apply(lambda row: get_dates_for_pattern(row['Ngày bắt đầu'], row['Thứ'], row['active_weeks']), axis=1)

    # Download section
    st.subheader("📥 Download Google Calendar")
    file_base = uploaded.name.rsplit(".", 1)[0] if uploaded else "data"
    csv_bytes = my_list_2.to_csv(index=False).encode("utf_8_sig")
    st.download_button(
        label="Download my_google.csv",
        data=csv_bytes,
        #file_name=f"{file_base}.csv",
        file_name=f"my_google.csv",
        mime="text/csv",
    )
else:
    st.info("Upload a file to begin.")
