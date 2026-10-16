from __future__ import annotations

import pandas as pd
import streamlit as st

from src.comparison import ComparisonError, compare_datasets, match_columns
from src.reporting import build_pdf_report

st.set_page_config(page_title="Data Comparison Tool", page_icon="🔎", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 2rem; padding-bottom: 3rem;}
.hero {padding: 1.5rem 1.7rem; border: 1px solid #dbeafe; border-radius: 16px;
background: linear-gradient(135deg, #eff6ff 0%, #ffffff 55%, #f5f3ff 100%); margin-bottom: 1.4rem;}
.hero h1 {margin: 0; color: #0f172a; font-size: 2.1rem;}
.hero p {margin: .55rem 0 0; color: #475569;}
[data-testid="stMetric"] {border: 1px solid #e2e8f0; border-radius: 12px; padding: .75rem 1rem; background: #fff;}
</style>
""", unsafe_allow_html=True)

def read_file(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file, low_memory=False)
    if name.endswith(".xlsx"):
        return pd.read_excel(uploaded_file, engine="openpyxl")
    raise ValueError("Upload a CSV or XLSX file.")

def csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8-sig")

st.markdown("""
<div class="hero">
<h1>🔎 Data Comparison Tool</h1>
<p>Compare source and target datasets, identify mismatches, and export verification results.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Comparison Settings")
    trim_whitespace = st.checkbox("Trim text whitespace", True)
    ignore_case = st.checkbox("Ignore text case", True)
    numeric_tolerance = st.number_input("Numeric tolerance", min_value=0.0, value=0.0, step=0.01)
    st.caption("Choose key columns that uniquely identify each record.")

left, right = st.columns(2)
with left:
    st.subheader("Dataset A")
    file_a = st.file_uploader("Upload source/legacy dataset", type=["csv", "xlsx"], key="dataset_a")
with right:
    st.subheader("Dataset B")
    file_b = st.file_uploader("Upload target/replacement dataset", type=["csv", "xlsx"], key="dataset_b")

if not (file_a and file_b):
    st.info("Upload both datasets to begin.")
    st.stop()

try:
    df_a = read_file(file_a)
    df_b = read_file(file_b)
except Exception as exc:
    st.error(f"Could not read the uploaded file: {exc}")
    st.stop()

c1, c2 = st.columns(2)
with c1:
    st.caption(f"{file_a.name} · {len(df_a):,} rows × {len(df_a.columns)} columns")
    st.dataframe(df_a.head(8), use_container_width=True, hide_index=True)
with c2:
    st.caption(f"{file_b.name} · {len(df_b):,} rows × {len(df_b.columns)} columns")
    st.dataframe(df_b.head(8), use_container_width=True, hide_index=True)

matches = match_columns(df_a.columns, df_b.columns)
if not matches:
    st.error("No unambiguous matching columns were found between the datasets.")
    st.stop()

option_map = {
    (m["a"] if m["a"] == m["b"] else f'{m["a"]} ↔ {m["b"]}'): (m["a"], m["b"])
    for m in matches
}

st.markdown("### 🔑 Record Matching")
selected = st.multiselect(
    "Select key column(s) used to identify the same record in both datasets",
    list(option_map.keys())
)

with st.expander("View automatically matched columns"):
    st.dataframe(pd.DataFrame(matches), use_container_width=True, hide_index=True)

if st.button("Run Comparison", type="primary", use_container_width=True):
    try:
        if not selected:
            raise ComparisonError("Select at least one key column before comparing.")
        result = compare_datasets(
            df_a, df_b,
            [option_map[label] for label in selected],
            trim_whitespace=trim_whitespace,
            ignore_case=ignore_case,
            numeric_tolerance=float(numeric_tolerance),
        )
        st.session_state["comparison_result"] = result
    except ComparisonError as exc:
        st.error(str(exc))
    except Exception as exc:
        st.exception(exc)

result = st.session_state.get("comparison_result")
if not result:
    st.stop()

s = result["summary"]
st.markdown("### 📊 Comparison Summary")
metrics = st.columns(6)
metrics[0].metric("Common Keys", f'{s["common_keys"]:,}')
metrics[1].metric("Matched", f'{s["matched_rows"]:,}')
metrics[2].metric("Mismatched", f'{s["mismatched_rows"]:,}')
metrics[3].metric("Only in A", f'{s["only_a"]:,}')
metrics[4].metric("Only in B", f'{s["only_b"]:,}')
metrics[5].metric("Cell Mismatches", f'{s["cell_mismatches"]:,}')

if s["mismatched_rows"] == 0 and s["only_a"] == 0 and s["only_b"] == 0:
    st.success("The compared records match.")
else:
    st.warning("Differences were detected. Review the result tabs before approving the data.")

tabs = st.tabs(["Overview", "Mismatches", "Only in A", "Only in B", "Matched Rows", "Column Mapping"])

with tabs[0]:
    st.write(f'Compared **{s["compared_columns"]} non-key columns** across **{s["common_keys"]:,} common record keys**.')
    if not result["mismatch_breakdown"].empty:
        st.bar_chart(result["mismatch_breakdown"].set_index("Column"))
        st.dataframe(result["mismatch_breakdown"], use_container_width=True, hide_index=True)
    else:
        st.info("No cell-level mismatches were found.")
    pdf = build_pdf_report(s, result["mismatch_breakdown"])
    st.download_button("Download PDF Summary", pdf, "data_comparison_summary.pdf", "application/pdf", use_container_width=True)

with tabs[1]:
    st.dataframe(result["mismatched_rows"], use_container_width=True, hide_index=True)
    st.download_button("Download Mismatched Records (CSV)", csv_bytes(result["mismatched_rows"]), "mismatched_records.csv", "text/csv")
    st.subheader("Cell-Level Details")
    st.dataframe(result["mismatch_details"], use_container_width=True, hide_index=True)
    st.download_button("Download Cell-Level Details (CSV)", csv_bytes(result["mismatch_details"]), "mismatch_details.csv", "text/csv")

with tabs[2]:
    st.dataframe(result["only_a"], use_container_width=True, hide_index=True)
    st.download_button("Download Records Only in A (CSV)", csv_bytes(result["only_a"]), "records_only_in_a.csv", "text/csv")

with tabs[3]:
    st.dataframe(result["only_b"], use_container_width=True, hide_index=True)
    st.download_button("Download Records Only in B (CSV)", csv_bytes(result["only_b"]), "records_only_in_b.csv", "text/csv")

with tabs[4]:
    st.dataframe(result["matched_rows"], use_container_width=True, hide_index=True)
    st.download_button("Download Matched Rows (CSV)", csv_bytes(result["matched_rows"]), "matched_rows.csv", "text/csv")

with tabs[5]:
    st.dataframe(result["column_mapping"], use_container_width=True, hide_index=True)
