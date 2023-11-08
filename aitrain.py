import streamlit as st
import openai
import os
from github import Github
from datetime import datetime
from gpt_index import SimpleDirectoryReader, GPTSimpleVectorIndex, LLMPredictor, PromptHelper
from langchain.chat_models import ChatOpenAI

# Setup OpenAI and GitHub
openai.api_key = st.secrets["OPENAI_API_KEY"]
g = Github(st.secrets["GITHUB_TOKEN"])
repo = g.get_repo("scooter7/aitrain")

# Construct the index from documents in the directory
def construct_index(directory_path):
    max_input_size = 4096  # This is the token limit for the model
    num_outputs = 512
    max_chunk_overlap = 20
    # Set a safe chunk size limit, considering the token limit of the model
    chunk_size_limit = 1024  # Adjust this number as needed

    prompt_helper = PromptHelper(max_input_size, num_outputs, max_chunk_overlap, chunk_size_limit=chunk_size_limit)

    llm_predictor = LLMPredictor(llm=ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo", max_tokens=num_outputs))

    documents = SimpleDirectoryReader(directory_path).load_data()

    index = GPTSimpleVectorIndex(documents, llm_predictor=llm_predictor, prompt_helper=prompt_helper)

    index.directory_path = directory_path

    index.save_to_disk('index.json')

    return index

# Chatbot function that uses the constructed index
def chatbot(input_text, first_name, email):
    index = GPTSimpleVectorIndex.load_from_disk('index.json')
    prompt = f"{first_name} ({email}): {input_text}"
    response = index.query(prompt, response_mode="compact")
    return response.response

# Streamlit app
st.set_page_config(page_title="AI Training Platform")
st.header("Welcome to the AI Training Platform")

# Initialize the index
docs_directory_path = "docs"
index = construct_index(docs_directory_path)

# Chat container
chat_container = st.container()

# Form for user input
with st.form(key="chat_form"):
    first_name = st.text_input("Enter your first name:")
    email = st.text_input("Enter your email address:")
    input_text = st.text_input("Enter your message:")
    submit_button = st.form_submit_button(label="Send")

if submit_button and input_text:
    filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.txt")
    response = chatbot(input_text, first_name, email)
    with chat_container:
        st.write(f"{first_name}: {input_text}")
        st.write(f"Chatbot: {response}")

# Style hiding
hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)
