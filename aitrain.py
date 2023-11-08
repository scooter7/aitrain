import streamlit as st
from github import Github
from langchain.chat_models import ChatOpenAI
from datetime import datetime
import base64
import fitz
import io

# Initialize OpenAI and GitHub API
openai_api_key = st.secrets["OPENAI_API_KEY"]
github_token = st.secrets["GITHUB_TOKEN"]
github_repo = "scooter7/aitrain"

# Set up GitHub API
g = Github(github_token)
repo = g.get_repo(github_repo)

# Initialize Chat model
chat_model = ChatOpenAI(api_key=openai_api_key)

# Set page config
st.set_page_config(page_title="AI-Powered LMS Chat")

st.title('Welcome to the AI-Powered Learning Management System')

# Function to fetch and display the introduction PDF
def display_introduction():
    contents = repo.get_contents("docs/marketing_strategy_plan_methodology.pdf")
    pdf_base64 = base64.b64decode(contents.content)
    pdf_reader = fitz.open(stream=io.BytesIO(pdf_base64), filetype="pdf")
    intro_text = ""
    for page in pdf_reader:
        intro_text += page.get_text()
    pdf_reader.close()
    return intro_text

# Display the introduction text
intro_text = display_introduction()
st.write(intro_text)

# Chatbot function
def chatbot(input_text, first_name, email):
    prompt = f"{first_name} ({email}): {input_text}"
    response = chat_model.generate(prompt)
    
    # Prepare directory path for content
    content_dir = "content"
    filename = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
    file_path = f"{content_dir}/{filename}"
    
    # Log the conversation to a file and upload to GitHub
    repo.create_file(file_path, f"Add chat log {filename}", response)

    return response

# User input form
first_name = st.text_input("Enter your first name:")
email = st.text_input("Enter your email address:")
input_text = st.text_input("Enter your message:")
send_button = st.button("Send")

# Process user input
if send_button and input_text:
    response = chatbot(input_text, first_name, email)
    st.write(f"{first_name}: {input_text}")
    st.write(f"Chatbot: {response}")

# Upload completed files
uploaded_file = st.file_uploader("Upload your completed material here:", type=['pdf', 'docx', 'xlsx'])
if uploaded_file is not None:
    # Convert to base64
    file_contents = base64.b64encode(uploaded_file.getvalue())
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
