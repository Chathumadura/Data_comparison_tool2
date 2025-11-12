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
