from datetime import datetime
import streamlit as st


# Custom Dependencies
import pandas as pd
from src.modules.file.chart_gen import generate_charts
from src.modules.file.edit_data import edit_data
from src.modules.file.mongodb import push_to_mongodb
from src.modules.file.query import query_csv_transformers


# Initialize session state variables if they don't exist
if 'df' not in st.session_state:
    st.session_state.df = None
if 'history' not in st.session_state:
    st.session_state.history = []
if 'counter' not in st.session_state:
    st.session_state.counter = 0
if 'current_file_name' not in st.session_state:
    st.session_state.current_file_name = None


def page_file(uploaded_file):
    # Create tabs for single file analysis and dataset comparison
    tab1, tab2 = st.tabs(["📄 Single File Analysis", "🔄 Dataset Comparison"])

    with tab1:
        # Original single file functionality
        if uploaded_file is not None:
            # Check if this is a new file upload
            if st.session_state.current_file_name != uploaded_file.name:
                # New file uploaded, reload the dataframe
                try:
                    st.session_state.df = pd.read_csv(uploaded_file, index_col=False)
                    st.session_state.df.dropna(how="all", inplace=True)
                    st.session_state.current_file_name = uploaded_file.name
                    st.session_state.history = []  # Clear history for new file
                    st.session_state.counter = 0
                except Exception as e:
                    st.error(f"Error reading CSV file: {str(e)}")
                    return

            df = st.session_state.df
            # ? Get the current time
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            st.write(f"DataFrame Created at: {current_time}")

            # ? Genrate Charts
            generate_charts(df)

            # ? Editable Dataframe
            df = edit_data(df)
            # Update session state with edited dataframe
            st.session_state.df = df

            # ? Querier
            question = st.text_area("Your Query")

            # ? query
            if question:
                ans = query_csv_transformers(df, question, True)
                print(ans)
                # ? Store the question and answer in the history
                st.session_state.history.append(
                    {
                        "question": question,
                        "answer": ans["answer"]
                        if ans["answer"] is not None
                        else "Plot Shown",
                    }
                )
                # ? Display the answer in Streamlit
                st.success(ans["answer"] if ans["answer"] is not None else "Plot Shown")
                st.session_state.counter += 1

                # Button to push records to MongoDB
                if st.button("Push to MongoDB", disabled=True):
                    if st.session_state.df is not None:
                        # Call the push_to_mongodb function
                        push_to_mongodb(st.session_state.df, "files", uploaded_file.name.split(".")[0])
                        st.success("Records pushed to MongoDB successfully")
                    else:
                        st.warning("DataFrame is empty. Upload a file first")

                # ? Display history in Streamlit
                if st.session_state.history:
                    st.subheader("Question-Answer History:")
                    for i, entry in enumerate(st.session_state.history[::-1], 1):
                        with st.status(f"Question {i}", expanded=False) as status:
                            status.write(f"Question: {entry['question']}")
                            status.write(f"Answer: {entry['answer']}")

        else:
            st.error("File not uploaded or present")
            st.session_state.history.clear()
            st.session_state.current_file_name = None

    with tab2:
        # Dataset Comparison functionality
        st.header("🔄 Dataset Comparison")
        st.write("Compare two datasets to find records present in Dataset A but missing in Dataset B.")

        # File uploaders for two datasets
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Dataset A")
            file_a = st.file_uploader("Upload Dataset A (CSV)", type=["csv"], key="file_a")

        with col2:
            st.subheader("📈 Dataset B")
            file_b = st.file_uploader("Upload Dataset B (CSV)", type=["csv"], key="file_b")

        if file_a and file_b:
            try:
                # Load datasets
                df_a = pd.read_csv(file_a, index_col=False)
                df_b = pd.read_csv(file_b, index_col=False)

                # Display dataset previews
                st.subheader("📋 Dataset Previews")

                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Dataset A Preview:**")
                    st.dataframe(df_a.head(), use_container_width=True)
                    st.caption(f"Total rows: {len(df_a)} | Total columns: {len(df_a.columns)}")

                with col2:
                    st.write("**Dataset B Preview:**")
                    st.dataframe(df_b.head(), use_container_width=True)
                    st.caption(f"Total rows: {len(df_b)} | Total columns: {len(df_b.columns)}")

                # Find common columns
                common_cols = list(set(df_a.columns) & set(df_b.columns))

                if not common_cols:
                    st.error("❌ No common columns found between the datasets. Cannot perform comparison.")
                    return

                st.success(f"✅ Found {len(common_cols)} common column(s): {', '.join(common_cols)}")

                # Column selection for comparison
                st.subheader("🔑 Select Key Columns for Comparison")
                key_cols = st.multiselect(
                    "Choose key column(s) to match records between datasets:",
                    common_cols,
                    default=[common_cols[0]] if common_cols else []
                )

                if key_cols:
                    try:
                        # Perform merge to find unique rows in A not in B
                        merged = df_a.merge(df_b, on=key_cols, how='left', indicator=True, suffixes=('_A', '_B'))

                        # Filter rows only in A (not in B)
                        unique_rows_a = merged[merged['_merge'] == 'left_only'].drop(columns=['_merge'])

                        # Remove suffix from column names for display
                        unique_rows_a.columns = [col.replace('_A', '') for col in unique_rows_a.columns]

                        # Summary statistics in table format
                        st.subheader("📊 Summary Statistics")
                        summary_data = {
                            "Details": ["Total rows in df1", "Total rows in df2", "Number of rows in df1 but not in df2"],
                            "Count": [len(df_a), len(df_b), len(unique_rows_a)]
                        }
                        summary_df = pd.DataFrame(summary_data)
                        st.table(summary_df)

                        # Display unique rows
                        st.subheader("📋 Records Present in Dataset A but Missing in Dataset B")
                        if len(unique_rows_a) > 0:
                            st.dataframe(unique_rows_a, use_container_width=True)

                            # Download button
                            csv_data = unique_rows_a.to_csv(index=False)
                            st.download_button(
                                label="📥 Download Unique Rows as CSV",
                                data=csv_data,
                                file_name=f"unique_rows_A_not_in_B_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                help="Download the table of records present in Dataset A but missing in Dataset B"
                            )
                        else:
                            st.info("ℹ No unique rows found. All records in Dataset A are present in Dataset B.")

                    except Exception as e:
                        st.error(f"❌ Error during comparison: {str(e)}")
                        st.info("💡 Tip: Ensure the selected key columns have compatible data types and no missing values.")
                else:
                    st.warning("⚠ Please select at least one key column to perform the comparison.")

            except Exception as e:
                st.error(f"❌ Error loading datasets: {str(e)}")
                st.info("💡 Tip: Make sure both files are valid CSV files.")
        else:
            st.info("ℹ Please upload both Dataset A and Dataset B to start the comparison.")
