import logging
import streamlit as st
from gpt_index import SimpleDirectoryReader, GPTListIndex, GPTSimpleVectorIndex, LLMPredictor, PromptHelper
from langchain.chat_models import ChatOpenAI
import sys
from datetime import datetime
import os
from github import Github

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Please set the OPENAI_API_KEY secret on the Streamlit dashboard.")
    sys.exit(1)

openai_api_key = st.secrets["OPENAI_API_KEY"]

logging.info(f"OPENAI_API_KEY: {openai_api_key}")

# Set up the GitHub API
g = Github(st.secrets["GITHUB_TOKEN"])
repo = g.get_repo("scooter7/aitrain")

def construct_index(directory_path):
    max_input_size = 4096
    num_outputs = 512
    max_chunk_overlap = 20
    chunk_size_limit = 600

    prompt_helper = PromptHelper(max_input_size, num_outputs, max_chunk_overlap, chunk_size_limit=chunk_size_limit)

    llm_predictor = LLMPredictor(llm=ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo", max_tokens=num_outputs))

    documents = SimpleDirectoryReader(directory_path).load_data()

    index = GPTSimpleVectorIndex(documents, llm_predictor=llm_predictor, prompt_helper=prompt_helper)

    index.directory_path = directory_path

    index.save_to_disk('index.json')

    return index


def chatbot(input_text, first_name, email):
    index = GPTSimpleVectorIndex.load_from_disk('index.json')
    prompt = f"{first_name} ({email}): {input_text}"
    response = index.query(prompt, response_mode="compact")

    # Create the content directory if it doesn't already exist
    content_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content")

    os.makedirs(content_dir, exist_ok=True)

    # Write the user question and chatbot response to a file in the content directory
    filename = st.session_state.filename
    file_path = os.path.join(content_dir, filename)
    with open(file_path, 'a') as f:
        f.write(f"{first_name} ({email}): {input_text}\n")
        f.write(f"Chatbot response: {response.response}\n")
        
    # Write the chat file to GitHub
    with open(file_path, 'rb') as f:
        contents = f.read()
        repo.create_file(f"content/{filename}", f"Add chat file {filename}", contents)

    return response.response


docs_directory_path = "docs"
index = construct_index(docs_directory_path)

st.set_page_config(page_title="3-Year Degree Feedback")

# Create a container to hold the chat messages
chat_container = st.container()

# Initialize last_send_pressed to False in session state
if "last_send_pressed" not in st.session_state:
    st.session_state.last_send_pressed = False

# Create a form to enter a message and submit it
form = st.form(key="my_form", clear_on_submit=True)
if "first_send" not in st.session_state:
    st.session_state.first_send = True

if st.session_state.first_send:
    first_name = form.text_input("Enter your first name:", key="first_name")
    email = form.text_input("Enter your email address:", key="email")
    st.session_state.first_send = False
else:
    first_name = st.session_state.first_name
    email = st.session_state.email

input_text = form.text_input("Enter your message:")
form_submit_button = form.form_submit_button(label="Send")

if form_submit_button and input_text:
    # Set the filename key every time the form is submitted
    filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.docx")
    st.session_state.filename = filename
    
    response = chatbot(input_text, first_name, email)

    # Write the user message and chatbot response to the chat container
    with chat_container:
        st.write(f"{first_name}: {input_text}")
        st.write(f"Chatbot: {response}")

    # Save the first name and email in session state
    st.session_state.first_name = first_name
    st.session_state.email = email

# Clear the input field after sending a message
form.empty()

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)
