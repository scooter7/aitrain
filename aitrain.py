import streamlit as st
import os
import sys
from github import Github
from gpt_index import SimpleDirectoryReader, GPTListIndex, GPTSimpleVectorIndex, LLMPredictor, PromptHelper
from langchain.chat_models import ChatOpenAI
import logging

# Check for OpenAI API key in Streamlit secrets
if "OPENAI_API_KEY" not in st.secrets:
    st.error("Please set the OPENAI_API_KEY secret on the Streamlit dashboard.")
    sys.exit(1)

openai_api_key = st.secrets["OPENAI_API_KEY"]
logging.info(f"OPENAI_API_KEY: {openai_api_key}")

# Check for GitHub token in Streamlit secrets
if "GITHUB_TOKEN" not in st.secrets:
    st.error("Please set the GITHUB_TOKEN secret on the Streamlit dashboard.")
    sys.exit(1)

github_token = st.secrets["GITHUB_TOKEN"]
g = Github(github_token)

# Initialize the GitHub repository
repo = g.get_repo("scooter7/aitrain")

# Function to construct the index
def construct_index(directory_path):
    max_input_size = 4096
    num_outputs = 512
    max_chunk_overlap = 20
    chunk_size_limit = 600

    prompt_helper = PromptHelper(max_input_size, num_outputs, max_chunk_overlap, chunk_size_limit=chunk_size_limit)
    llm_predictor = LLMPredictor(llm=ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo", max_tokens=num_outputs))
    documents = SimpleDirectoryReader(directory_path).load_data()
    index = GPTSimpleVectorIndex(documents, llm_predictor=llm_predictor, prompt_helper=prompt_helper)
    index.save_to_disk('index.json')
    return index

# Function to handle chat
def chatbot(input_text, first_name, email):
    index = GPTSimpleVectorIndex.load_from_disk('index.json')
    prompt = f"{first_name} ({email}): {input_text}"
    response = index.query(prompt, response_mode="compact")
    return response.response

# Main app logic
def main():
    st.title("AI Marketing Strategy Assistant")

    # Create a container to hold the chat messages
    chat_container = st.container()

    # Create a form to enter a message and submit it
    with st.form(key="chat_form"):
        first_name = st.text_input("Enter your first name:")
        email = st.text_input("Enter your email address:")
        input_text = st.text_area("Enter your message:")
        submit_button = st.form_submit_button(label="Send")

    if submit_button and input_text:
        response = chatbot(input_text, first_name, email)
        with chat_container:
            st.write(f"{first_name}: {input_text}")
            st.write(f"Chatbot: {response}")

# Run the main function
if __name__ == "__main__":
    main()
