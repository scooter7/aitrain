import streamlit as st
from github import Github
from llama_index import VectorStoreIndex, ServiceContext, Document
from llama_index.llms import OpenAI
import openai
from pypdf import PdfReader
import nltk
import os

# Download necessary NLTK data
nltk.download('popular')

# Set up Streamlit page configuration
st.set_page_config(page_title="Chat with the Bain Report", page_icon="🦙", layout="centered", initial_sidebar_state="auto", menu_items=None)

# Check if the necessary API keys are set in Streamlit secrets
if "OPENAI_API_KEY" not in st.secrets or "GITHUB_TOKEN" not in st.secrets:
    st.error("Please set the necessary API keys in Streamlit secrets.")
    sys.exit(1)

# Set up API keys from Streamlit secrets
openai_api_key = st.secrets["OPENAI_API_KEY"]
github_token = st.secrets["GITHUB_TOKEN"]

# Initialize GitHub client
g = Github(github_token)
repo_name = "scooter7/aitrain"
repo = g.get_repo(repo_name)

# Function to get the URL for a file in the GitHub repository
def get_github_file_url(file_path):
    return f"https://github.com/{repo_name}/blob/main/{file_path}"

# Function to get a list of files in the docs folder
def get_docs_files():
    contents = repo.get_contents("docs")
    return {content.name: content.path for content in contents if content.type == "file"}

# Function to check if the user's message is a request for a document
def is_request_for_document(message):
    # Simple check for keywords, can be replaced with more complex NLP
    return any(keyword in message.lower() for keyword in ["document", "report", "file", "pdf"])

# Function to search for documents in the docs folder
def search_docs(message, files_dict):
    # Simple search based on file names, can be replaced with more complex search logic
    for name, path in files_dict.items():
        if name.lower() in message.lower():
            return path
    return None

# Initialize chat messages if not already present in session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Ask me a question about the Bain Report!"}
    ]

# Load data function to index documents
@st.cache(allow_output_mutation=True, show_spinner=False)
def load_data():
    with st.spinner(text="Loading and indexing the Bain Report – hang tight!"):
        pdf_path = "docs/marketing_strategy_plan_methodology.pdf"
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"The file {pdf_path} was not found.")
        
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        docs = [Document(text=text, title="Bain Report")]
        service_context = ServiceContext.from_defaults(llm=OpenAI(model="gpt-3.5-turbo", temperature=0.5))
        index = VectorStoreIndex.from_documents(docs, service_context=service_context)
        return index

index = load_data()

# Initialize chat engine if not already present in session state
if "chat_engine" not in st.session_state:
    st.session_state.chat_engine = index.as_chat_engine(chat_mode="condense_question", verbose=True)

# Handle chat input
if prompt := st.chat_input("Your question"):
    st.session_state.messages.append({"role": "user", "content": prompt})

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Generate and handle chat responses
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            user_message = st.session_state.messages[-1]["content"]
            docs_files = get_docs_files()
            if is_request_for_document(user_message):
                doc_path = search_docs(user_message, docs_files)
                if doc_path:
                    file_url = get_github_file_url(doc_path)
                    response_message = f"Here is the document you requested: [link]({file_url})"
                else:
                    response_message = "I couldn't find the document you're looking for."
            else:
                response = st.session_state.chat_engine.chat(user_message)
                response_message = response.response
            
            st.write(response_message)
            message = {"role": "assistant", "content": response_message}
            st.session_state.messages.append(message)
