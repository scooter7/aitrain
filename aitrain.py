import logging
import streamlit as st
from github import Github
import os
from datetime import datetime
import openai
from langchain.chat_models import ChatOpenAI
from gpt_index import SimpleDirectoryReader, GPTListIndex, GPTSimpleVectorIndex, LLMPredictor, PromptHelper

# Setup OpenAI and GitHub
openai_api_key = st.secrets["OPENAI_API_KEY"]
g = Github(st.secrets["GITHUB_TOKEN"])
repo = g.get_repo("scooter7/aitrain")

# Initialize chat model
chat_model = ChatOpenAI(api_key=openai_api_key)

# Function to display an introduction message
def display_introduction():
    st.header("Welcome to the AI Training Platform")
    st.write("Here you can learn about our marketing strategy plan methodology.")

# Function to upload files to GitHub
def upload_file_to_github(file, filename):
    content_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content")
    os.makedirs(content_dir, exist_ok=True)
    file_path = os.path.join(content_dir, filename)
    with open(file_path, 'wb') as f:
        f.write(file.getbuffer())
    repo.create_file(f"content/{filename}", f"Add file {filename}", file.getbuffer())

# Function to handle chat interactions
def handle_chat(user_input):
    response = chat_model.generate_response(user_input)
    return response

# Streamlit app
st.set_page_config(page_title="AI Training Platform")

display_introduction()

st.subheader("Downloadable Resources")
st.markdown("[Marketing Strategy Scorecard (Excel)](https://github.com/scooter7/aitrain/blob/main/docs/marketing_strategy_scorecard.xlsx)")
st.markdown("[Market Requirements Document (Word)](https://github.com/scooter7/aitrain/blob/main/docs/market_requirements_document.docx)")

st.subheader("Upload Your Completed Files")
uploaded_files = st.file_uploader("Choose files", accept_multiple_files=True, type=['xlsx', 'docx'])
if uploaded_files:
    for uploaded_file in uploaded_files:
        filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_" + uploaded_file.name
        upload_file_to_github(uploaded_file, filename)
        st.success(f"Uploaded {uploaded_file.name}")

st.subheader("Ask a Question")
user_input = st.text_input("What would you like to know?")
if user_input:
    chat_response = handle_chat(user_input)
    st.write(chat_response)

hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)
