import streamlit as st
import fitz  # PyMuPDF
import os
from github import Github
import openai
import difflib

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

# Function to get document titles and URLs from the docs directory in the repository
def get_document_titles_and_urls(repo):
    contents = repo.get_contents("docs")  # Gets the contents of the 'docs' directory
    document_titles = []
    document_urls = {}

    for content_file in contents:
        if content_file.type == "file" and content_file.name.endswith(('.pdf', '.docx', '.xlsx')):
            document_titles.append(content_file.name)
            document_urls[content_file.name] = content_file.download_url

    return document_titles, document_urls

# Fetch the actual document titles and URLs
document_titles, document_urls = get_document_titles_and_urls(repo)

# Display stages and handle file uploads
stages_text = extract_text_by_stages("docs/marketing_strategy_plan_methodology.pdf")

for stage, text in stages_text.items():
    st.subheader(stage)
    st.write(text)

# Chat interface
if "messages" not in st.session_state:
    st.session_state.messages = []

if prompt := st.text_input("Your question"):
    st.session_state.messages.append({"role": "user", "content": prompt})

for message in st.session_state.messages:
    st.write(f"{message['role'].title()}: {message['content']}")

if st.session_state.messages and st.session_state.messages[-1]["role"] != "assistant":
    document_keywords = ['document', 'file', 'download', 'link', 'template', 'worksheet', 'form']

    if any(keyword in prompt.lower() for keyword in document_keywords):
        closest_matches = difflib.get_close_matches(prompt.lower(), [title.lower() for title in document_titles], n=5, cutoff=0.3)
        if closest_matches:
            matching_titles = [title for title in document_titles if title.lower() in closest_matches]
            response_content = "Here are the documents that might match your request:\n"
            for title in matching_titles:
                document_url = document_urls[title]
                response_content += f"- [{title}]({document_url})\n"
        else:
            response_content = "I couldn't find the document you're looking for."
    else:
        formatted_messages = [{"role": message["role"], "content": message["content"]} for message in st.session_state.messages]
        completion = openai.chat.completions.create(
            model="gpt-4",
            messages=formatted_messages
        )
        response_content = completion.choices[0].message.content

    st.session_state.messages.append({"role": "assistant", "content": response_content})
