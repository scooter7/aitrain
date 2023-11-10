import streamlit as st
import fitz  # PyMuPDF
import os
from github import Github
import openai
import difflib

st.set_page_config(page_title="Chat with the Bain Report", page_icon="🦙", layout="centered", initial_sidebar_state="auto", menu_items=None)

if "OPENAI_API_KEY" not in st.secrets or "GITHUB_TOKEN" not in st.secrets:
    st.error("Please set the necessary secrets (OPENAI_API_KEY and GITHUB_TOKEN) on the Streamlit dashboard.")
    sys.exit(1)

openai.api_key = st.secrets["OPENAI_API_KEY"]
github_token = st.secrets["GITHUB_TOKEN"]

g = Github(github_token)
repo = g.get_repo("scooter7/aitrain")

def extract_text_by_stages(pdf_path):
    doc = fitz.open(pdf_path)
    stages_text = {}
    current_stage = None
    current_text = []

    for page in doc:
        blocks = page.get_text("blocks")
        for block in blocks:
            if block[0] == fitz.TEXT_BLOCK_TYPE_TEXT:
                text = block[4].strip()
                if text.startswith("Stage") and "-" in text:
                    if current_stage:
                        stages_text[current_stage] = "\n".join(current_text)
                    current_stage = text.split("\n")[0]
                    current_text = []
                else:
                    current_text.append(text)
    
    if current_stage:
        stages_text[current_stage] = "\n".join(current_text)

    return stages_text

def save_uploaded_file(uploaded_file):
    with open(os.path.join("tempDir", uploaded_file.name), "wb") as f:
        f.write(uploaded_file.getbuffer())
    return f.name

def upload_to_github(file_path, repo, path_in_repo):
    with open(file_path, "rb") as f:
        content = f.read()
    repo.create_file(path_in_repo, "commit message", content)

def get_document_titles_and_urls(repo):
    contents = repo.get_contents("docs")
    document_titles = []
    document_urls = {}

    for content_file in contents:
        if content_file.type == "file" and content_file.name.endswith(('.pdf', '.docx', '.xlsx')):
            document_titles.append(content_file.name)
            document_urls[content_file.name] = content_file.download_url

    return document_titles, document_urls

document_titles, document_urls = get_document_titles_and_urls(repo)

stages_text = extract_text_by_stages("docs/marketing_strategy_plan_methodology.pdf")

if 'current_stage_index' not in st.session_state:
    st.session_state.current_stage_index = 0

current_stage_keys = list(stages_text.keys())

if st.button("Go to next stage"):
    st.session_state.current_stage_index += 1
    if st.session_state.current_stage_index >= len(current_stage_keys):
        st.session_state.current_stage_index = 0

current_stage = current_stage_keys[st.session_state.current_stage_index]
st.subheader(current_stage)
st.write(stages_text[current_stage])

uploaded_file = st.file_uploader("Upload your document", type=['docx', 'xlsx'])
if uploaded_file is not None:
    file_path = save_uploaded_file(uploaded_file)
    upload_to_github(file_path, repo, f"uploads/{uploaded_file.name}")

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
            response_content = "Here are the documents that might match your request:\n"
            for title in closest_matches:
                document_url = document_urls[title]
                response_content += f"- [{title}]({document_url})\n"
        else:
            response_content = "I couldn't find the document you're looking for. Please make sure to use the exact title of the document or provide more context."
    else:
        formatted_messages = [{"role": message["role"], "content": message["content"]} for message in st.session_state.messages]
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=formatted_messages
        )
        response_content = response.choices[0].message['content']

    st.session_state.messages.append({"role": "assistant", "content": response_content})
    st.write(f"Assistant: {response_content}")
