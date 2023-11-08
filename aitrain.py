import streamlit as st
import openai
import base64
from github import Github
from datetime import datetime
import io
import fitz

# Initialize the GitHub and OpenAI API clients
g = Github(st.secrets["GITHUB_TOKEN"])
repo = g.get_repo("scooter7/aitrain")
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Set page configuration
st.set_page_config(page_title="AI-Powered LMS Chat")
st.title('Welcome to the AI-Powered Learning Management System')

# Function to fetch and decode the PDF from GitHub
def fetch_pdf_content():
    contents = repo.get_contents("docs/marketing_strategy_plan_methodology.pdf")
    pdf_data = base64.b64decode(contents.content)
    return pdf_data

# Function to extract text from the PDF
def extract_text_from_pdf(pdf_data):
    with fitz.open("pdf", pdf_data) as doc:
        text = ""
        for page in doc:
            text += page.get_text()
    return text

# Function to interact with the OpenAI chat model
def chat_with_gpt3(analysis_text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "Analyze the following text:"}, {"role": "user", "content": analysis_text}]
    )
    return response.choices[0].message["content"].strip()

# Fetch the PDF content, extract the text, and display it
pdf_data = fetch_pdf_content()
intro_text = extract_text_from_pdf(pdf_data)
st.write(intro_text)

# Chat interface
input_text = st.text_area("Enter your message:")
send_button = st.button("Send")
if send_button and input_text:
    response = chat_with_gpt3(input_text)
    st.write("Analysis: ", response)

# File uploader for users to upload completed materials
uploaded_file = st.file_uploader("Upload your completed material here:", type=['pdf', 'docx', 'xlsx'])
if uploaded_file is not None:
    file_contents = base64.b64encode(uploaded_file.getvalue()).decode()
    upload_path = f"content/completed_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{uploaded_file.name}"
    repo.create_file(upload_path, f"Upload completed material {uploaded_file.name}", file_contents)

# Custom CSS to hide Streamlit's default UI elements
st.markdown("""
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """, unsafe_allow_html=True)
