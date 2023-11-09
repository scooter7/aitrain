import streamlit as st
from llama_index import VectorStoreIndex, ServiceContext, Document
from llama_index.llms import OpenAI
import openai
from pypdf import PdfReader
import nltk
import logging
import os
from github import Github

# Download necessary NLTK data
nltk.download('popular')

st.set_page_config(page_title="Learn about Marketing Straegy", page_icon="🦙", layout="centered", initial_sidebar_state="auto", menu_items=None)
if "OPENAI_API_KEY" not in st.secrets:
    st.error("Please set the OPENAI_API_KEY secret on the Streamlit dashboard.")
    sys.exit(1)

openai_api_key = st.secrets["OPENAI_API_KEY"]
g = Github(st.secrets["GITHUB_TOKEN"])

logging.info(f"OPENAI_API_KEY: {openai_api_key}")
st.title("Learn about Marekting Strategy Planning")
st.info("This app allows you to ask questions about the Bain Report.", icon="📃")

def get_docs_files():
    repo = g.get_repo("scooter7/aitrain")
    contents = repo.get_contents("docs")
    return contents

def create_download_link(file_info):
    return f"[{file_info.name}]({file_info.download_url})"

st.sidebar.title("Download Docs")
try:
    docs_files = get_docs_files()
    for file_info in docs_files:
        if file_info.type == "file":
            st.sidebar.markdown(create_download_link(file_info), unsafe_allow_html=True)
except Exception as e:
    st.sidebar.error("Error fetching files")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Ask me a question about the Bain Report!"}
    ]

@st.cache_resource(show_spinner=False)
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

if "chat_engine" not in st.session_state:
    st.session_state.chat_engine = index.as_chat_engine(chat_mode="condense_question", verbose=True)

if prompt := st.chat_input("Your question"):
    st.session_state.messages.append({"role": "user", "content": prompt})

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = st.session_state.chat_engine.chat(prompt)
            st.write(response.response)
            message = {"role": "assistant", "content": response.response}
            st.session_state.messages.append(message)
