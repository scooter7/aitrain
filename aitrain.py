import streamlit as st
import openai
import fitz  # PyMuPDF
import os
from github import Github
from datetime import datetime

# Setup OpenAI and GitHub
openai.api_key = st.secrets["OPENAI_API_KEY"]
g = Github(st.secrets["GITHUB_TOKEN"])
repo = g.get_repo("scooter7/aitrain")

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    with fitz.open(pdf_path) as pdf:
        text = ""
        for page in pdf:
            text += page.get_text()
    return text

# Function to handle chat interactions with context from a PDF file
def handle_chat(user_input, pdf_context):
    response = openai.Completion.create(
        engine="text-davinci-003",  # or another appropriate engine
        prompt=f"{user_input}\n\n{pdf_context}",  # Combine user input with PDF context
        max_tokens=150
    )
    return response.choices[0].text.strip()

# Streamlit app
st.set_page_config(page_title="AI Training Platform")

# Display an introduction message
st.header("Welcome to the AI Training Platform")
st.write("Here you can learn about our marketing strategy plan methodology.")

# Provide links to Word and Excel resources
st.subheader("Downloadable Resources")
st.markdown("[Marketing Strategy Scorecard (Excel)](https://github.com/scooter7/aitrain/blob/main/docs/marketing_strategy_scorecard.xlsx)")
st.markdown("[Market Requirements Document (Word)](https://github.com/scooter7/aitrain/blob/main/docs/market_requirements_document.docx)")

# File uploader for user to upload completed files
st.subheader("Upload Your Completed Files")
uploaded_files = st.file_uploader("Choose files", accept_multiple_files=True, type=['xlsx', 'docx'])
if uploaded_files:
    for uploaded_file in uploaded_files:
        filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_" + uploaded_file.name
        # Assuming you have a function to upload files to GitHub
        # upload_file_to_github(uploaded_file, filename)
        st.success(f"Uploaded {uploaded_file.name}")

# User question area with a submit button
st.subheader("Ask a Question")
user_input = st.text_input("What would you like to know?")
submit_button = st.button("Submit")

# Assuming the PDF file is stored locally in the 'docs' directory
pdf_context = extract_text_from_pdf("docs/marketing_strategy_plan_methodology.pdf")

if submit_button and user_input:
    chat_response = handle_chat(user_input, pdf_context)
    st.write(chat_response)

# Hide Streamlit style
hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)
