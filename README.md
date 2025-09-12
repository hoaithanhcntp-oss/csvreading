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
