# home.py
import streamlit as st
import pandas as pd
import os


def page_home():
    # Page title and introduction
    st.title("CSVdash - Convert & Visualize CSV Data")
    st.write("Welcome to CSVdash, your tool for converting and visualizing CSV data!")

    # Link to Anime_CSV
    st.write("### Anime_CSV link")
    st.write(
        "Anime_CSV [link](https://github.com/Otherwa/CSVDash/blob/Otherwa/data/Anime_Analysis.csv)"
    )

    # UI Changes
    st.write("### UI Changes:")
    st.write("- Updated the color scheme for a more modern look.")
    st.write("- Reorganized the navigation menu for better user flow.")
    st.write("- Increased font size for improved readability.")

    # User Acceptance Testing (UAT) Progress
    st.write("### User Acceptance Testing (UAT) Progress:")
    st.write("- Invited stakeholders to test the application.")
    st.write("- Received feedback on UI and functionality.")
    st.write("- Identified and fixed several issues reported by users.")

    # What you can do with CSVdash
    st.write("### What you can do with CSVdash:")
    st.write(
        "- **Query the CSV:** Use the search functionality to query and filter data."
    )
    st.write(
        "- **Change the data:** Modify and update the CSV data within the application."
    )

    # Example: Displaying a CSV file using pandas
    try:
        # Get the directory of the current file, go up to CSVDash, then to data
        current_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(current_dir, "..", "..", "data", "Anime_Analysis.csv")
        csv_path = os.path.normpath(csv_path)
        
        if os.path.exists(csv_path):
            csv_data = pd.read_csv(csv_path)
            st.write("### Example CSV Data:")
            st.dataframe(csv_data.head())
        else:
            st.write("### Example CSV Data:")
            st.write("Sample CSV file not found. Please upload a CSV file to view data.")
    except Exception as e:
        st.write("### Example CSV Data:")
        st.write(f"Error loading sample CSV: {str(e)}. Please upload a CSV file to view data.")

    # Add any other sections or features as needed

    # Footer
    st.write("Thank you for using CSVdash!")
