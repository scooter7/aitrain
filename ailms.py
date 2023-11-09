import streamlit as st
import os
from github import Github
import openai
from pypdf import PdfReader

# Set up the Streamlit page
st.set_page_config(page_title="Chat with the Bain Report", page_icon="🦙", layout="centered", initial_sidebar_state="auto", menu_items=None)

# Check for necessary secrets
if "OPENAI_API_KEY" not in st.secrets or "GITHUB_TOKEN" not in st.secrets:
    st.error("Please set the necessary secrets (OPENAI_API_KEY and GITHUB_TOKEN) on the Streamlit dashboard.")
    st.stop()

# Set up API keys
openai.api_key = st.secrets["OPENAI_API_KEY"]
github_token = st.secrets["GITHUB_TOKEN"]

# Set up GitHub client
g = Github(github_token)
repo = g.get_repo("scooter7/aitrain")

# Fetch the list of files in the docs directory
contents = repo.get_contents("docs")
document_titles = [content.name for content in contents if content.name.endswith(('.docx', '.xlsx'))]
document_urls = {title: content.download_url for title, content in zip(document_titles, contents) if title.endswith(('.docx', '.xlsx'))}

# Streamlit title and info
st.title("Chat with Bain Report")
st.info("This app allows you to ask questions about the Bain Report.", icon="📃")

# Initialize session state for messages if not already present
if "messages" not in st.session_state:
    st.session_state.messages = []

# Function to load and index the Bain Report
@st.experimental_singleton
def load_data():
    pdf_path = "docs/marketing_strategy_plan_methodology.pdf"
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"The file {pdf_path} was not found.")
    
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    
    return text

report_text = load_data()

# Chat input
if 'user_input' not in st.session_state:
    st.session_state['user_input'] = ''

user_input = st.text_input("Your question", key="user_input_key")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state['user_input'] = ''

    # Generate and display assistant response
    with st.spinner("Thinking..."):
        if any(title.lower() in user_input.lower() for title in document_titles):
            matching_titles = [title for title in document_titles if title.lower() in user_input.lower()]
            if matching_titles:
                matching_title = matching_titles[0]
                document_url = document_urls[matching_title]
                response_content = f"I found the document you're looking for: [{matching_title}]({document_url})"
            else:
                response_content = "I couldn't find the document you're looking for."
        else:
            chat_messages = [{"role": "system", "content": "You are a helpful assistant. Answer the user's questions accurately."}]
            for message in st.session_state.messages:
                chat_messages.append({"role": message["role"], "content": message["content"]})
            
            completion = openai.ChatCompletion.create(
                model="gpt-4",
                messages=chat_messages
            )
            response_content = completion.choices[0].message['content']
        
        st.session_state.messages.append({"role": "assistant", "content": response_content})
        st.session_state['user_input'] = ''

# Display chat messages
for message in st.session_state.messages:
    st.write(f"{message['role'].title()}: {message['content']}")
