import streamlit as st
import openai
from github import Github
from datetime import datetime

# Set up GitHub API
g = Github(st.secrets["GITHUB_TOKEN"])
repo = g.get_repo("scooter7/aitrain")

# Set OpenAI key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Set page config
st.set_page_config(page_title="AI-Powered LMS Chat")
st.title('Welcome to the AI-Powered Learning Management System')

# Function to analyze text with GPT-3
def analyze_with_gpt3(text):
    response = openai.Completion.create(
        engine="text-davinci-003",  # Update to the latest engine version
        prompt=f"Please analyze the following text and identify who would likely find it compelling:\n\n{text}",
        max_tokens=100
    )
    return response.choices[0].text.strip()

# Chatbot function
def chatbot(input_text):
    analysis = analyze_with_gpt3(input_text)
    filename = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
    file_path = f"content/{filename}"
    repo.create_file(file_path, f"Add chat log {filename}", f"Analysis: {analysis}")
    return analysis

# User input form
input_text = st.text_area("Enter your message:")
send_button = st.button("Send")

# Process user input
if send_button and input_text:
    response = chatbot(input_text)
    st.write("Analysis: ", response)

# Upload completed files
uploaded_file = st.file_uploader("Upload your completed material here:", type=['pdf', 'docx', 'xlsx'])
if uploaded_file is not None:
    file_contents = uploaded_file.read()
    upload_path = f"content/completed_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{uploaded_file.name}"
    repo.create_file(upload_path, f"Upload completed material {uploaded_file.name}", file_contents.decode('utf-8'))

# Hide Streamlit style elements
st.markdown("""
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """, unsafe_allow_html=True)
