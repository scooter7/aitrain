import streamlit as st
import openai
import os
from github import Github
from datetime import datetime
import PyMuPDF

openai.api_key = st.secrets["OPENAI_API_KEY"]
g = Github(st.secrets["GITHUB_TOKEN"])
repo = g.get_repo("scooter7/aitrain")

def extract_text_from_pdf(pdf_path):
    with fitz.open(pdf_path) as pdf:
        text = ""
        for page in pdf:
            text += page.get_text()
    return text

def handle_chat(user_input, pdf_context):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"{user_input}\n\n{pdf_context}",
        max_tokens=150
    )
    return response.choices[0].text.strip()

st.set_page_config(page_title="AI Training Platform")
st.header("Welcome to the AI Training Platform")
st.write("Here you can learn about our marketing strategy plan methodology.")
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
submit_button = st.button("Submit")
pdf_context = extract_text_from_pdf("docs/marketing_strategy_plan_methodology.pdf")
if submit_button and user_input:
    chat_response = handle_chat(user_input, pdf_context)
    st.write(chat_response)

hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)
