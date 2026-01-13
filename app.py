import io
from typing import Optional, List

import pandas as pd
import streamlit as st
import numpy as np

from datetime import datetime, timedelta
import sys

# set up the webpage
st.set_page_config(page_title="Import EGOV schedule to Google calendar", page_icon="📤", layout="wide")
st.title("📤 Upload schedule → 📥 Download google calendar")
st.caption("Hướng dẫn: upload file lịch của trường theo học kỳ và download về file csv để import vào google calendar.")
with st.expander("Need help?"):
    st.write("""
    1. Upload your CSV or Excel file.  
    2. If the file has extra header rows, adjust 'Skip rows'.  
    3. Preview the data in the main panel.  
    4. Click 'Download CSV' to save the cleaned file.
    """)
    
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
    start_date = start_date_str
    # remove this from streamlit
    #parsed = False
    #for fmt in ('%m/%d/%Y', '%m/%d/%y'):
    #    try:
    #        start_date = datetime.strptime(start_date_str, fmt)
    #        parsed = True
    #        break
    #    except ValueError:
    #        pass
    #if not parsed and sys.platform.startswith('win'):
    #    for fmt in ('%#m/%#d/%Y', '%#m/%#d/%y'):
    #        try:
    #            start_date = datetime.strptime(start_date_str, fmt)
    #            parsed = True
    #            break
    #        except ValueError:
    #            pass
    #if not parsed:
    #    raise ValueError(f"Could not parse date string: {start_date_str}")
    # end of remove

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

# Lecture sessions (with 25-min breaks after session 3 and 9)
lecture_array = [
    ("06:30", "07:20"),  # Session 1
    ("07:20", "08:10"),  # Session 2
    ("08:10", "09:00"),  # Session 3
    ("09:30", "10:20"),  # Session 4
    ("10:20", "11:10"),  # Session 5
    ("11:10", "12:00"),  # Session 6
    ("12:30", "13:20"),  # Session 7 (fixed start reset)
    ("13:20", "14:10"),  # Session 8
    ("14:10", "15:00"),  # Session 9
    ("15:30", "16:20"),  # Session 10
    ("16:20", "17:10"),  # Session 11
    ("17:10", "18:00"),  # Session 12
    ("18:10", "19:00"),  # Session 13 (fixed start reset)
    ("19:00", "19:50"),  # Session 14
    ("19:50", "20:40"),  # Session 15
    ("20:40", "21:30"),  # Session 16
    ("21:30", "22:20")   # Session 17
]


# Practice sessions (no breaks)
practice_array = [
    ("07:00", "07:50"),  # Session 1
    ("07:50", "08:40"),  # Session 2
    ("08:40", "09:30"),  # Session 3
    ("09:30", "10:20"),  # Session 4
    ("10:20", "11:10"),  # Session 5
    ("11:10", "12:00"),  # Session 6
    ("12:30", "13:20"),  # Session 7 (reset start)
    ("13:20", "14:10"),  # Session 8
    ("14:10", "15:00"),  # Session 9
    ("15:00", "15:50"),  # Session 10
    ("15:50", "16:40"),  # Session 11
    ("16:40", "17:30"),  # Session 12
    ("18:00", "18:50"),  # Session 13 (reset start)
    ("18:50", "19:40"),  # Session 14
    ("19:40", "20:30"),  # Session 15
    ("20:30", "21:20"),  # Session 16
]

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
    my_list_2['active_weeks'] = my_list_2['Tuần học'].apply(parse_week_pattern)
    my_list_2['class_dates'] = my_list_2.apply(lambda row: get_dates_for_pattern(row['Ngày bắt đầu'], row['Thứ'], row['active_weeks']), axis=1)

    # Create an empty list to store the expanded schedule data
    schedule_data = []

    # Iterate through each row in the original DataFrame (my_list_2)
    for index, row in my_list_2.iterrows():
        # For each date in the 'class_dates' list for this row
        for class_date in row['class_dates']:
            # Create a new row for the expanded schedule
            new_row = {
                'STT': row['STT'],
                'Mã lớp học phần': row['Mã lớp học phần'],
                'Nhóm': row['Nhóm'],
                'Lớp': row['Lớp'],
                'Tên môn học': row['Tên môn học'],
                'Sỉ số': row['Sỉ số'],
                'Thứ': row['Thứ'],
                'Từ tiết': row['Từ tiết'],
                'Đến tiết': row['Đến tiết'],
                'Tiết học': row['Tiết học'],
                'Tên phòng': row['Tên phòng'],
                'Ngày': class_date # Add the specific date for this class session
            }
            # Append the new row to the schedule_data list
            schedule_data.append(new_row)

    # Create the new DataFrame from the list of dictionaries
    my_schedule = pd.DataFrame(schedule_data)
    
    # Check practice or lecture session
    my_schedule['IsPractice'] = 0
    my_schedule.loc[my_schedule['Tên môn học'].str.contains('Thực hành', na=False), 'IsPractice'] = 1
    #my_schedule.loc[my_schedule['Tên môn học'].str.contains('Ứng dụng tin học', na=False), 'IsPractice'] = 1

    # Check schedule is online or offline
    my_schedule['IsOnline'] = 0
    my_schedule.loc[my_schedule['Tên phòng'].str.contains('Zoom', na=False), 'IsOnline'] = 1

    # Convert 'Từ tiết' to 'From_time' and 'Đến tiết' to 'End_time' based on 'IsPractice'

    # Convert to Start time and End time
    my_schedule['Start time'] = my_schedule.apply(lambda row: practice_array[row['Từ tiết'] - 1][0] if row['IsPractice'] == 1 else lecture_array[row['Từ tiết'] - 1][0], axis=1)
    my_schedule['End time'] = my_schedule.apply(lambda row: practice_array[row['Đến tiết'] - 1][1] if row['IsPractice'] == 1 else lecture_array[row['Đến tiết'] - 1][1], axis=1)

    # Create the my_google dataframe
    my_google = pd.DataFrame()

    # Create the 'Subject' column by combining 'Tên môn học' and 'Mã lớp học phần' and Status online or not
    base_subject = my_schedule['Tên môn học'] + ' - ' + my_schedule['Mã lớp học phần'].astype(str) + ' - ' + my_schedule['Lớp']
    my_google['Subject'] = np.where(my_schedule['IsOnline'] == 1, '(Online) ' + base_subject, base_subject)

    # Create the 'Start Date' column from the 'Ngày' column
    my_google['Start Date'] = my_schedule['Ngày'].dt.strftime('%m/%d/%Y')

    my_google['Start Time'] = my_schedule['Start time']
    my_google['End Date'] = my_google['Start Date']
    my_google['End Time'] = my_schedule['End time']

    # Create the 'Location' column from the 'Tên phòng' column
    my_google['Location'] = my_schedule['Tên phòng']
    my_google['Description'] = my_schedule['Tên phòng'] + ';\r\nTiết:' + my_schedule['Từ tiết'].astype(str) + '-' + my_schedule['Đến tiết'].astype(str) + ';\r\n' + my_google['Subject']

    # Get today's date
    today = datetime.now().date()

    # Convert 'Start Date' column to datetime objects
    my_google['Start Date'] = pd.to_datetime(my_google['Start Date'], format='%m/%d/%Y').dt.date

    # Filter the DataFrame to keep only rows with 'Start Date' on or after today
    my_google = my_google[my_google['Start Date'] >= today]

    # Download section
    st.subheader("📥 Download Google Calendar")
    file_base = uploaded.name.rsplit(".", 1)[0] if uploaded else "data"
    csv_bytes = my_google.to_csv(index=False).encode("utf_8_sig")
    st.download_button(
        label="Download my_google.csv",
        data=csv_bytes,
        #file_name=f"{file_base}.csv",
        file_name=f"my_google.csv",
        mime="text/csv",
    )
else:
    st.info("Upload a file to begin.")
    
st.markdown("---")
st.caption("© Copyright by **Trinh Hoai Thanh**")
