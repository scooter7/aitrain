import streamlit as st
from github import Github
from llama_index import VectorStoreIndex, ServiceContext, Document
from llama_index.llms import OpenAI
import openai
from pypdf import PdfReader
import nltk
import os

nltk.download('popular')

st.set_page_config(page_title="Chat with the Bain Report", page_icon="🦙", layout="centered", initial_sidebar_state="auto", menu_items=None)

if "OPENAI_API_KEY" not in st.secrets or "GITHUB_TOKEN" not in st.secrets:
    st.error("Please set the necessary secrets (OPENAI_API_KEY and GITHUB_TOKEN) on the Streamlit dashboard.")
    sys.exit(1)

openai.api_key = st.secrets["OPENAI_API_KEY"]
github_token = st.secrets["GITHUB_TOKEN"]

g = Github(github_token)
repo = g.get_repo("scooter7/aitrain")

contents = repo.get_contents("docs")
document_titles = [content.name for content in contents if content.name.endswith(('.docx', '.doc', '.xlsx', '.xls'))]
document_urls = {title: content.download_url for title, content in zip(document_titles, contents) if title.endswith(('.docx', '.doc', '.xlsx', '.xls'))}

st.title("Learn about Marketing Plan Development")
st.info("This app allows you learn about developing a marketing plan.", icon="📃")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Ask me a question about developing a marketing plan!"}
    ]

@st.cache_resource(show_spinner=False)
def load_data():
    with st.spinner(text="Loading and indexing the material – hang tight!"):
        pdf_path = "docs/marketing_strategy_plan_methodology.pdf"
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"The file {pdf_path} was not found.")
        
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        docs = [Document(text=text, title="Marketing Plan Development)]
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
            if any(title.lower() in prompt.lower() for title in document_titles):
                matching_titles = [title for title in document_titles if title.lower() in prompt.lower()]
                if matching_titles:
                    matching_title = matching_titles[0]
                    document_url = document_urls[matching_title]
                    response_content = f"I found the document you're looking for: [{matching_title}]({document_url})"
                else:
                    response_content = "I couldn't find the document you're looking for."
            else:
                response = st.session_state.chat_engine.chat(prompt)
                response_content = response.response
            
            st.write(response_content)
            message = {"role": "assistant", "content": response_content}
            st.session_state.messages.append(message)
