import streamlit as st
from github import Github
from datetime import datetime
import os
import openai

# Check for necessary secrets
if "OPENAI_API_KEY" not in st.secrets or "GITHUB_TOKEN" not in st.secrets:
    st.error("Please set the OPENAI_API_KEY and GITHUB_TOKEN secrets on the Streamlit dashboard.")
    st.stop()

# Initialize GitHub API
github_token = st.secrets["GITHUB_TOKEN"]
github_repo = "scooter7/aitrain"
g = Github(github_token)
repo = g.get_repo(github_repo)

# Set page config
st.set_page_config(page_title="AI-Powered LMS Chat")
st.title('Welcome to the AI-Powered Learning Management System')

# Function to analyze text with GPT-3
def analyze_with_gpt3(text, api_key):
    openai.api_key = api_key
    prompt = f"Please analyze the following text and identify who would likely find it compelling:\n\n{text}"
    response = openai.Completion.create(engine="text-davinci-002", prompt=prompt, max_tokens=100)
    return response.choices[0].text.strip()

# Chatbot function
def chatbot(input_text, first_name, email, api_key):
    analysis = analyze_with_gpt3(input_text, api_key)
    
    # Prepare directory path for content
    content_dir = "content"
    filename = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
    file_path = f"{content_dir}/{filename}"
    
    # Log the conversation to a file and upload to GitHub
    repo.create_file(file_path, f"Add chat log {filename}", f"User: {input_text}\nAnalysis: {analysis}")
    
    return analysis

# User input form
first_name = st.text_input("Enter your first name:")
email = st.text_input("Enter your email address:")
input_text = st.text_area("Enter your message:")
send_button = st.button("Send")

# Process user input
if send_button and input_text:
    response = chatbot(input_text, first_name, email, st.secrets["OPENAI_API_KEY"])
    st.write(f"{first_name}: {input_text}")
    st.write(f"Analysis: {response}")

# Upload completed files
uploaded_file = st.file_uploader("Upload your completed material here:", type=['pdf', 'docx', 'xlsx'])
if uploaded_file is not None:
    file_contents = uploaded_file.getvalue()
    upload_path = f"content/completed_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{uploaded_file.name}"
    repo.create_file(upload_path, f"Upload completed material {uploaded_file.name}", file_contents)

# Hide Streamlit style elements
st.markdown("""
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """, unsafe_allow_html=True)
