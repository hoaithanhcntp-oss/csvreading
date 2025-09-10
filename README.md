# CSV Uploader & Downloader (Streamlit)

A tiny web app to upload a CSV, preview/edit it in the browser, then download it back.

## 🔧 Local run

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the URL shown in your terminal (usually http://localhost:8501).

## ☁️ One-click deploy (Streamlit Community Cloud)

1. Push these files to a new **public GitHub repository**.
2. Go to https://share.streamlit.io (Streamlit Community Cloud) and choose **New app**.
3. Select your repo and set **main file path** to `app.py`.
4. Click **Deploy**. That's it—your app will be online and shareable.

## 📝 Notes

- Use the sidebar to change delimiter (`,` `;` or `\t`) and encoding (e.g., `utf-8`, `utf-8-sig`, `latin-1`).
- Use the in-browser **data editor** to add/remove rows and edit cells.
- Download the edited/cleaned data as a CSV right from the app.
