import streamlit as st
import fitz  # PyMuPDF
import os
from github import Github
import openai
from pypdf import PdfReader

# Set up the Streamlit page
st.set_page_config(page_title="Chat with the Bain Report", page_icon="🦙", layout="centered", initial_sidebar_state="auto", menu_items=None)

# Check for necessary secrets
if "OPENAI_API_KEY" not in st.secrets or "GITHUB_TOKEN" not in st.secrets:
    st.error("Please set the necessary secrets (OPENAI_API_KEY and GITHUB_TOKEN) on the Streamlit dashboard.")
    sys.exit(1)

# Set up API keys
openai.api_key = st.secrets["OPENAI_API_KEY"]
github_token = st.secrets["GITHUB_TOKEN"]

# Set up GitHub client
g = Github(github_token)
repo = g.get_repo("scooter7/aitrain")

# Function to extract text by stages from the PDF
def extract_text_by_stages(pdf_path):
    doc = fitz.open(pdf_path)
    stages_text = {}
    current_stage = None
    current_text = []

    for page in doc:
        text = page.get_text()
        # Search for stage headings like "Stage 1 - Values"
        if "Stage" in text and "-" in text:
            if current_stage:
                stages_text[current_stage] = "\n".join(current_text)
            current_stage = text.strip().split("\n")[0]  # Assumes the stage title is at the start of a line
            current_text = []
        else:
            current_text.append(text)
    
    if current_stage:  # Don't forget to save the last stage
        stages_text[current_stage] = "\n".join(current_text)

    return stages_text

# Function to save uploaded file
def save_uploaded_file(uploaded_file):
    with open(os.path.join("tempDir", uploaded_file.name), "wb") as f:
        f.write(uploaded_file.getbuffer())
    return f.name

# Function to upload file to GitHub
def upload_to_github(file_path, repo, path_in_repo):
    with open(file_path, "rb") as f:
        content = f.read()
    repo.create_file(path_in_repo, "commit message", content)

# Display stages and handle file uploads
stages_text = extract_text_by_stages("docs/marketing_strategy_plan_methodology.pdf")

for stage, text in stages_text.items():
    st.subheader(stage)
    st.write(text)
    # Add more logic here to provide links to associated documents

uploaded_file = st.file_uploader("Upload your document", type=['docx', 'xlsx'])
if uploaded_file is not None:
    file_path = save_uploaded_file(uploaded_file)
    upload_to_github(file_path, repo, f"uploads/{uploaded_file.name}")

# Chat interface
if "messages" not in st.session_state:
    st.session_state.messages = []

if prompt := st.text_input("Your question"):
    st.session_state.messages.append({"role": "user", "content": prompt})

for message in st.session_state.messages:
    st.write(f"{message['role'].title()}: {message['content']}")

if st.session_state.messages and st.session_state.messages[-1]["role"] != "assistant":
    # Corrected API call to use openai.ChatCompletions.create
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=st.session_state.messages
    )
    st.session_state.messages.append({"role": "assistant", "content": response.choices[0].message['content']})
