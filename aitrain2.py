import streamlit as st
from llama_index import VectorStoreIndex, ServiceContext, Document
from llama_index.llms import OpenAI
import openai
from pypdf import PdfReader
import nltk
import logging
import os
import difflib

# Download necessary NLTK data
nltk.download('popular')

# Set up the Streamlit app configuration
st.set_page_config(page_title="Chat with the Bain Report", page_icon="🦙", layout="centered", initial_sidebar_state="auto", menu_items=None)

# Check for the OpenAI API key in the Streamlit secrets
if "OPENAI_API_KEY" not in st.secrets:
    st.error("Please set the OPENAI_API_KEY secret on the Streamlit dashboard.")
    sys.exit(1)

# Retrieve the OpenAI API key from the Streamlit secrets
openai_api_key = st.secrets["OPENAI_API_KEY"]
logging.info(f"OPENAI_API_KEY: {openai_api_key}")

# Set up the title and information for the Streamlit app
st.title("Chat with Bain Report")
st.info("This app allows you to ask questions about the Bain Report.", icon="📃")

# Initialize the chat messages history if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Ask me a question about the Bain Report!"}
    ]

# Function to load and index the Bain Report
@st.cache_resource(show_spinner=False)
def load_data():
    with st.spinner(text="Loading and indexing the Bain Report – hang tight!"):
        # Assuming the PDF file is in the same directory as the Streamlit app
        pdf_path = "docs/marketing_strategy_plan_methodology.pdf"
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"The file {pdf_path} was not found.")
        
        # Use PyPDF2 to extract text from the PDF
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        # Create a document object with the extracted text
        docs = [Document(text=text, title="Bain Report")]
        service_context = ServiceContext.from_defaults(llm=OpenAI(model="gpt-3.5-turbo", temperature=0.5))
        index = VectorStoreIndex.from_documents(docs, service_context=service_context)
        return index

# Load the indexed data
index = load_data()

# Initialize the chat engine if it doesn't exist
if "chat_engine" not in st.session_state:
    st.session_state.chat_engine = index.as_chat_engine(chat_mode="condense_question", verbose=True)

# Function to determine if the user is requesting a document
def is_requesting_document(user_query):
    document_request_keywords = ['document', 'file', 'pdf', 'download', 'view']
    return any(keyword in user_query.lower() for keyword in document_request_keywords)

# Function to find the best matching document for a given query
def find_matching_document(user_query, list_of_document_titles):
    match = difflib.get_close_matches(user_query, list_of_document_titles, n=1, cutoff=0.6)
    return match[0] if match else None

# Function to handle the user query
def handle_user_query(user_query):
    if is_requesting_document(user_query):
        document_title = find_matching_document(user_query, list_of_document_titles)
        if document_title:
            document_url = document_title_to_url_map[document_title]
            return f"Here is the document you requested: [Link to {document_title}]({document_url})"
        else:
            return "I couldn't find the document you're looking for."
    else:
        response = st.session_state.chat_engine.chat(user_query)
        return response.response

# Prompt for user input and save to chat history
if prompt := st.chat_input("Your question"):
    st.session_state.messages.append({"role": "user", "content": prompt})

# Display the prior chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# If the last message is not from the assistant, generate a new response
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = handle_user_query(prompt)
            st.write(response)
            message = {"role": "assistant", "content": response}
            st.session_state.messages.append(message)
