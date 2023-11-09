import streamlit as st
import fitz  # PyMuPDF
import os
from github import Github
import openai
from pypdf import PdfReader

# Download necessary NLTK data
# nltk.download('popular') # This line should be run separately if needed, not within the app

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
    # Assuming the PDF file is in the same directory as the Streamlit app
    pdf_path = "docs/marketing_strategy_plan_methodology.pdf"
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"The file {pdf_path} was not found.")
    
    # Use PyPDF2 to extract text from the PDF
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    
    return text

report_text = load_data()

# Chat input
if prompt := st.text_input("Your question"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Generate and display assistant response
    with st.spinner("Thinking..."):
        # Check if the user is asking for a document
        if any(title.lower() in prompt.lower() for title in document_titles):
            # Find the matching document title
            matching_titles = [title for title in document_titles if title.lower() in prompt.lower()]
            if matching_titles:
                # Provide the link to the matching document
                matching_title = matching_titles[0]  # Assuming the first match is the desired one
                document_url = document_urls[matching_title]
                response_content = f"I found the document you're looking for: [{matching_title}]({document_url})"
            else:
                response_content = "I couldn't find the document you're looking for."
        else:
            # Handle other types of queries
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "You are a helpful assistant."},
                          *st.session_state.messages,
                          {"role": "user", "content": prompt}]
            )
            response_content = response['choices'][0]['message']['content']
        
        st.session_state.messages.append({"role": "assistant", "content": response_content})

# Display chat messages
for message in st.session_state.messages:
    st.write(f"{message['role'].title()}: {message['content']}")
