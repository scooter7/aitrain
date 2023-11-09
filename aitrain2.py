import streamlit as st
from github import Github
import difflib
from llama_index import VectorStoreIndex, ServiceContext, Document
from llama_index.llms import OpenAI
import openai
from pypdf import PdfReader
import nltk
import os

# Download necessary NLTK data
nltk.download('popular')

# Set up the Streamlit page
st.set_page_config(page_title="Develop a Marketing Plan", page_icon="🦙", layout="centered", initial_sidebar_state="auto", menu_items=None)

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

# Fetch the list of files in the docs directory
contents = repo.get_contents("docs")
document_titles = [content.name for content in contents if content.name.endswith(('.docx', '.xlsx'))]
document_urls = {title: content.download_url for title, content in zip(document_titles, contents) if title.endswith(('.docx', '.xlsx'))}

# Streamlit title and info
st.title("Chat with Bain Report")
st.info("This app will guide you through developing a marketing plan.", icon="📃")

# Initialize session state for messages if not already present
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Ask me a question about developing a marketing plan!"}
    ]

# Function to load and index the Bain Report
@st.cache_resource(show_spinner=False)
def load_data():
    with st.spinner(text="Loading and indexing the marketing strategy methodology – hang tight!"):
        # Assuming the PDF file is in the same directory as the Streamlit app
        pdf_path = "docs/marketing_strategy_plan_methodology.pdf"
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"The file {pdf_path} was not found.")
        
        # Use PyPDF2 to extract text from the PDF
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        docs = [Document(text=text, title="Marketing Plan Development")]
        service_context = ServiceContext.from_defaults(llm=OpenAI(model="gpt-3.5-turbo", temperature=0.5))
        index = VectorStoreIndex.from_documents(docs, service_context=service_context)
        return index

index = load_data()

# Initialize chat engine if not already present
if "chat_engine" not in st.session_state:
    st.session_state.chat_engine = index.as_chat_engine(chat_mode="condense_question", verbose=True)

# Chat input
if prompt := st.chat_input("Your question"):
    st.session_state.messages.append({"role": "user", "content": prompt})

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Generate and display assistant response
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Define keywords that suggest the user is asking for a document
            document_keywords = ['document', 'file', 'download', 'link']
            
            # Check if the user's query contains any of the document keywords
            if any(keyword in prompt.lower() for keyword in document_keywords):
                # Attempt to find a close match for the document title in the user's query
                closest_matches = difflib.get_close_matches(prompt, document_titles, n=1, cutoff=0.1)
                if closest_matches:
                    document_title = closest_matches[0]
                    document_url = document_urls[document_title]
                    response_content = f"I found the document you're looking for: [{document_title}]({document_url})"
                else:
                    response_content = "I couldn't find the document you're looking for. Please make sure to use the exact title of the document or provide more context."
            else:
                # If no document keywords are present, handle the query normally
                response = st.session_state.chat_engine.chat(prompt)
                response_content = response.response
            
            st.write(response_content)
            message = {"role": "assistant", "content": response_content}
            st.session_state.messages.append(message)
