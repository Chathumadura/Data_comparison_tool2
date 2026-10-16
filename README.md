# Data Comparison Tool

A practical **Streamlit-based data verification application** for comparing two structured datasets during migration, synchronization, or master-data validation work.

This project was rebuilt from an earlier CSV analytics prototype into a focused comparison tool that identifies matching records, mismatched values, and records that exist in only one dataset.

## Key Features

- Upload **CSV** or **XLSX** datasets
- Automatically match columns while ignoring case, spaces, underscores, and punctuation
- Select one or more **key columns** to identify the same record across datasets
- Detect duplicate keys and require safer record matching before comparison
- Optional whitespace trimming and case-insensitive text comparison
- Configurable **numeric tolerance**
- Identify matched rows, mismatched rows, records only in A, and records only in B
- Show cell-level mismatch details and mismatch counts by column
- Export results as **CSV**
- Generate a compact **PDF summary report**

## Tech Stack

Python · Streamlit · Pandas · ReportLab · OpenPyXL · Pytest

## Project Structure

```text
Data_comparison_tool2/
├── app.py
├── src/
│   ├── __init__.py
│   ├── comparison.py
│   └── reporting.py
├── tests/
│   └── test_comparison.py
├── sample_data/
│   ├── dataset_a.csv
│   └── dataset_b.csv
├── .streamlit/
│   └── config.toml
├── requirements.txt
├── run.bat
├── run.ps1
└── README.md
```

## Getting Started

```bash
git clone https://github.com/Chathumadura/Data_comparison_tool2.git
cd Data_comparison_tool2
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## How to Use

1. Upload Dataset A and Dataset B.
2. Review the automatically matched columns.
3. Select the key column or combination of key columns that uniquely identifies each record.
4. Configure text normalization or numeric tolerance if required.
5. Run the comparison.
6. Review results in the separate tabs.
7. Export CSV files or the PDF summary.

## Example

Demo files are available in `sample_data/`. Use `record_id` as the key.

## Testing

```bash
pytest -q
```

## Project Context

This project is based on data verification work carried out during my internship at the **Sri Lanka Tea Board**. The public repository contains only generic demo data and no organizational datasets.

## Author

**Kavishka Chathumadura**
