import streamlit as st
from github import Github
import PyPDF2
import io
from gpt_index import SimpleDirectoryReader, GPTListIndex, GPTSimpleVectorIndex, LLMPredictor, PromptHelper
from langchain.chat_models import ChatOpenAI

# Check for OpenAI API key in Streamlit secrets
if "OPENAI_API_KEY" not in st.secrets:
    st.error("Please set the OPENAI_API_KEY secret on the Streamlit dashboard.")
    st.stop()

openai_api_key = st.secrets["OPENAI_API_KEY"]

# Check for GitHub token in Streamlit secrets
if "GITHUB_TOKEN" not in st.secrets:
    st.error("Please set the GITHUB_TOKEN secret on the Streamlit dashboard.")
    st.stop()

github_token = st.secrets["GITHUB_TOKEN"]
g = Github(github_token)

# Initialize the GitHub repository
repo = g.get_repo("scooter7/aitrain")

# Function to extract text from PDF
def extract_text_from_pdf(pdf_content):
    pdfReader = PyPDF2.PdfFileReader(io.BytesIO(pdf_content))
    text = ""
    for pageNum in range(pdfReader.numPages):
        pageObj = pdfReader.getPage(pageNum)
        text += pageObj.extractText()
    return text

# Function to construct the index
def construct_index():
    try:
        # Get the content of the PDF file from the repo
        contents = repo.get_contents("docs/marketing_strategy_plan_methodology.pdf")
        if contents.encoding == "base64":
            pdf_content = contents.decoded_content
        else:
            raise ValueError("Unsupported encoding for the PDF content")

        # Extract text from the PDF
        extracted_text = extract_text_from_pdf(pdf_content)

        max_input_size = 4096
        num_outputs = 512
        max_chunk_overlap = 20
        chunk_size_limit = 600

        prompt_helper = PromptHelper(max_input_size, num_outputs, max_chunk_overlap, chunk_size_limit=chunk_size_limit)
        llm_predictor = LLMPredictor(llm=ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo", max_tokens=num_outputs))
        
        # Create a document list with the content of the PDF
        documents = [extracted_text]
        
        index = GPTSimpleVectorIndex(documents, llm_predictor=llm_predictor, prompt_helper=prompt_helper)
        index.save_to_disk('index.json')
        return index
    except Exception as e:
        st.error(f"An error occurred while constructing the index: {e}")
        st.stop()

# Function to handle chat
def chatbot(input_text):
    index = GPTSimpleVectorIndex.load_from_disk('index.json')
    prompt = input_text
    response = index.query(prompt, response_mode="compact")
    return response.response

# Main app logic
def main():
    st.title("AI Marketing Strategy Assistant")

    # Create the index on app startup
    if 'index' not in st.session_state:
        st.session_state.index = construct_index()

    # Create a container to hold the chat messages
    chat_container = st.container()

    # Create a form to enter a message and submit it
    with st.form(key="chat_form"):
        input_text = st.text_area("Enter your question about the marketing strategy:")
        submit_button = st.form_submit_button(label="Ask")

    if submit_button and input_text:
        response = chatbot(input_text)
        with chat_container:
            st.write(f"You: {input_text}")
            st.write(f"AI: {response}")

# Run the main function
if __name__ == "__main__":
    main()
