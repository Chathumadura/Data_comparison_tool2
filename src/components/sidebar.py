# sidebar.py

import streamlit as st


def create_sidebar():
    # Add a sidebar for navigation

    with st.sidebar:
        st.title("CSVDash")
        page = st.selectbox(
            "Pages:",
            ["Home", "File"],
        )

        # Create a sidebar for file upload and data conversion options
        uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

    return page, uploaded_file
