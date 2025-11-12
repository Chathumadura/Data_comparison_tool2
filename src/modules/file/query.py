import streamlit as st
from dotenv import load_dotenv
import os
# from langchain_experimental.agents import create_pandas_dataframe_agent
# from langchain_openai import ChatOpenAI

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")


# Query CSV using LangChain PandasDataFrameAgent
def query_csv_transformers(df, user_question, api):
    if api:
        # llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo", openai_api_key=openai_api_key)
        # agent = create_pandas_dataframe_agent(llm, df, verbose=True, allow_dangerous_code=True)
        # try:
        #     response = agent.run(user_question)
        #     print(response)
        #     return {"answer": response}
        # except Exception as e:
        #     return {"answer": f"Error processing query: {str(e)}"}
        return {"answer": "LangChain integration temporarily disabled due to version conflicts."}
    return {"answer": None}
