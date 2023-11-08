import streamlit as st
from gpt_index import SimpleDirectoryReader, GPTListIndex, GPTSimpleVectorIndex, LLMPredictor, PromptHelper
from langchain.chat_models import ChatOpenAI
import os
from datetime import datetime
from github import Github

# Function to split text into chunks
def split_into_chunks(text, max_chunk_size):
    chunks = []
    while text:
        split_index = (text.rfind(' ', 0, max_chunk_size) + 1) or max_chunk_size
        chunk = text[:split_index].strip()
        chunks.append(chunk)
        text = text[split_index:]
    return chunks

# Construct the index from documents in the directory
def construct_index(directory_path):
    max_input_size = 4096
    num_outputs = 512
    max_chunk_overlap = 20
    chunk_size_limit = 1024

    prompt_helper = PromptHelper(max_input_size, num_outputs, max_chunk_overlap, chunk_size_limit=chunk_size_limit)
    llm_predictor = LLMPredictor(llm=ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo", max_tokens=num_outputs))
    
    documents = SimpleDirectoryReader(directory_path).load_data()
    processed_documents = [split_into_chunks(doc, chunk_size_limit) for doc in documents]
    
    index = GPTSimpleVectorIndex(processed_documents, llm_predictor=llm_predictor, prompt_helper=prompt_helper)
    index.directory_path = directory_path
    index.save_to_disk('index.json')
    return index

# Initialize the Github client with your personal access token
g = Github("your_github_access_token")

# Get the repository object for 'scooter7/aitrain'
repo = g.get_repo("scooter7/aitrain")

docs_directory_path = "docs"
index = construct_index(docs_directory_path)

# Streamlit app code
st.title("AI-powered Chatbot")

# Create a container to hold the chat messages
chat_container = st.container()

# Initialize session state variables
if "last_send_pressed" not in st.session_state:
    st.session_state.last_send_pressed = False

if "first_send" not in st.session_state:
    st.session_state.first_send = True

# Create a form to enter a message and submit it
with st.form(key="my_form", clear_on_submit=True):
    if st.session_state.first_send:
        first_name = st.text_input("Enter your first name:", key="first_name")
        email = st.text_input("Enter your email address:", key="email")
        st.session_state.first_send = False
    else:
        first_name = st.session_state.first_name
        email = st.session_state.email

    input_text = st.text_input("Enter your message:")
    form_submit_button = st.form_submit_button(label="Send")

if form_submit_button and input_text:
    filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.txt")
    st.session_state.filename = filename
    
    # Query the index with the input text
    prompt = f"{first_name} ({email}): {input_text}"
    response = index.query(prompt, response_mode="compact")

    # Write the user message and chatbot response to the chat container
    with chat_container:
        st.write(f"{first_name}: {input_text}")
        st.write(f"Chatbot: {response.response}")

    # Save the first name and email in session state
    st.session_state.first_name = first_name
    st.session_state.email = email

    # Write the chat to a file and push to GitHub
    content_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content")
    os.makedirs(content_dir, exist_ok=True)
    file_path = os.path.join(content_dir, st.session_state.filename)
    with open(file_path, 'a') as f:
        f.write(f"{first_name} ({email}): {input_text}\n")
        f.write(f"Chatbot response: {response.response}\n")
    with open(file_path, 'rb') as f:
        contents = f.read()
        repo.create_file(f"content/{filename}", f"Add chat file {filename}", contents)

# Hide Streamlit branding (optional)
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)
