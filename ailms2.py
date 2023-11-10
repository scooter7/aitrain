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
        blocks = page.get_text("blocks")
        for block in blocks:
            text = block[4]
            if text.startswith("Stage") and "–" in text:  # Check for stage headings with an en dash
                if current_stage:
                    # Save the text of the current stage before moving to the next
                    stages_text[current_stage] = "\n".join(current_text).strip()
                # Extract the stage title, assuming it's the first line of the block
                current_stage = text.split("\n")[0]
                current_text = [text]
            elif current_stage:
                # Accumulate text for the current stage
                current_text.append(text)
    
    # Save the text of the last stage
    if current_stage:
        stages_text[current_stage] = "\n".join(current_text).strip()

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

# Function to display the current stage and associated documents
def display_current_stage(stage, stages_text, document_urls):
    st.subheader(stage)
    st.write(stages_text[stage])
    # Display links to associated documents
    for title in document_titles:
        if title in stages_text[stage]:
            st.markdown(f"[Download {title}]({document_urls[title]})")

# Function to handle file upload and summarize content
def handle_file_upload():
    uploaded_file = st.file_uploader("Upload your document", type=['docx', 'xlsx'])
    if uploaded_file is not None:
        # Summarize the uploaded document here
        # For now, we just display a placeholder message
        st.write("Document uploaded and summarized. Let's discuss it!")

# Initialize stages and current stage index
if "stages_text" not in st.session_state:
    st.session_state.stages_text = extract_text_by_stages("docs/marketing_strategy_plan_methodology.pdf")
    st.session_state.current_stage_index = 0

# Display current stage and handle file uploads
current_stage_keys = list(st.session_state.stages_text.keys())
current_stage = current_stage_keys[st.session_state.current_stage_index]
display_current_stage(current_stage, st.session_state.stages_text, document_urls)
handle_file_upload()

# Button to go to the next stage
if st.button("Go to Next Stage"):
    if st.session_state.current_stage_index < len(current_stage_keys) - 1:
        st.session_state.current_stage_index += 1
    else:
        st.write("You have reached the final stage.")

# Chat interface
if "messages" not in st.session_state:
    st.session_state.messages = []

# Chat input
if prompt := st.text_input("Your question about the uploaded document:"):
    st.session_state.messages.append({"role": "user", "content": prompt})

# Display chat messages
for message in st.session_state.messages:
    st.write(f"{message['role'].title()}: {message['content']}")

# Generate and display assistant response
if st.session_state.messages and st.session_state.messages[-1]["role"] != "assistant":
    # If no document keywords are present, handle the query normally
    formatted_messages = [{"role": message["role"], "content": message["content"]} for message in st.session_state.messages]
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=formatted_messages
    )
    response_content = response.choices[0].message.content  # Correctly access the content attribute

    # Append the assistant's response to the chat history
    st.session_state.messages.append({"role": "assistant", "content": response_content})
    st.write(f"Assistant: {response_content}")
