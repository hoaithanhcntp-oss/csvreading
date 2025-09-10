import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="CSV Uploader & Downloader", page_icon="📄", layout="wide")

st.title("📄 CSV Uploader & Downloader")
st.caption("Upload a CSV, preview & edit it in your browser, then download it back. Built with Streamlit.")

with st.sidebar:
    st.header("⚙️ Options")
    sep = st.text_input("Delimiter (sep)", value=",", help="Common values: ',', ';', '\\t' for tab")
    encoding = st.text_input("Encoding", value="utf-8", help="Try 'utf-8-sig' or 'latin-1' for some files")
    na_values = st.text_input("NA values (comma-separated)", value="")
    na_list = [s.strip() for s in na_values.split(",")] if na_values.strip() != "" else None
    st.markdown("---")
    st.write("Need a starter file?")
    if st.button("⬇️ Download sample CSV"):
        sample = pd.DataFrame({
            "id": [1,2,3],
            "name": ["Alice","Bob","Charlie"],
            "score": [88.5, 91.0, 79.25]
        })
        buf = io.StringIO()
        sample.to_csv(buf, index=False)
        st.download_button("Download sample.csv", data=buf.getvalue(), file_name="sample.csv", mime="text/csv")

uploaded = st.file_uploader("Upload a CSV file", type=["csv"], accept_multiple_files=False)

def load_csv(file):
    return pd.read_csv(file, sep=sep, encoding=encoding, na_values=na_list)

if uploaded is not None:
    try:
        df = load_csv(uploaded)
        st.success(f"Loaded **{uploaded.name}** - {df.shape[0]} rows × {df.shape[1]} columns")
        st.write("### Preview")
        st.dataframe(df.head(100), use_container_width=True)
        
        st.write("### ✍️ Edit your data (optional)")
        edited_df = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic",
            key="editor",
            hide_index=False,
            )
        
        st.write("### ⬇️ Download your CSV")
        csv_buf = io.StringIO()
        edited_df.to_csv(csv_buf, index=False)
        st.download_button(
            label="Download edited CSV",
            data=csv_buf.getvalue(),
            file_name=f"edited_{uploaded.name}",
            mime="text/csv"
        )

        st.write("### ℹ️ Info")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rows", edited_df.shape[0])
        with col2:
            st.metric("Columns", edited_df.shape[1])
        with col3:
            st.metric("Missing cells", int(edited_df.isna().sum().sum()))

        with st.expander("🧠 Schema & dtypes"):
            dtypes = pd.DataFrame({"column": edited_df.columns, "dtype": edited_df.dtypes.astype(str).values})
            st.table(dtypes)

        with st.expander("🧼 Quick clean"):
            drop_dupes = st.checkbox("Drop duplicate rows")
            strip_space = st.checkbox("Strip leading/trailing spaces in text columns")
            if st.button("Apply cleaning"):
                work = edited_df.copy()
                if drop_dupes:
                    work = work.drop_duplicates()
                if strip_space:
                    for c in work.select_dtypes(include="object").columns:
                        work[c] = work[c].astype("string").str.strip()
                csv_buf2 = io.StringIO()
                work.to_csv(csv_buf2, index=False)
                st.download_button("Download cleaned CSV", data=csv_buf2.getvalue(), file_name=f"cleaned_{uploaded.name}", mime="text/csv")
                st.success("Cleaning applied. Use the button above to download.")

    except Exception as e:
        st.error(f"Could not read file: {e}")
else:
    st.info("Upload a CSV to begin.")
    
st.markdown("---")
st.caption("Tip: If your data looks garbled, try a different **delimiter** or **encoding** in the sidebar.")
