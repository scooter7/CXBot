import streamlit as st
from gpt_index import SimpleDirectoryReader, GPTListIndex, GPTSimpleVectorIndex, LLMPredictor, PromptHelper
from langchain.chat_models import ChatOpenAI
from datetime import datetime
import os
from github import Github

openai_api_key = st.secrets["OPENAI_API_KEY"]
g = Github(st.secrets["GITHUB_TOKEN"])
repo = g.get_repo("scooter7/CXBot")

def construct_index(directory_path):
    prompt_helper = PromptHelper(4096, 512, 20, chunk_size_limit=600)
    llm_predictor = LLMPredictor(llm=ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo", max_tokens=512))
    documents = SimpleDirectoryReader(directory_path).load_data()
    index = GPTSimpleVectorIndex(documents, llm_predictor=llm_predictor, prompt_helper=prompt_helper)
    index.directory_path = directory_path
    index.save_to_disk('index.json')
    return index

def chatbot(input_text, first_name, email):
    index = GPTSimpleVectorIndex.load_from_disk('index.json')
    if not st.session_state.answered_admin_question:
        prompt = f"The user said: '{input_text}'. What's a relevant follow-up question I should ask?"
    else:
        prompt = f"{first_name} ({email}): {input_text}"
    response = index.query(prompt, response_mode="compact")
    content_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content")
    os.makedirs(content_dir, exist_ok=True)
    if "filename" not in st.session_state:
        st.session_state.filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.docx")
    filename = st.session_state.filename
    file_path = os.path.join(content_dir, filename)
    with open(file_path, 'a') as f:
        f.write(f"{first_name} ({email}): {input_text}\n")
        f.write(f"Chatbot response: {response.response}\n")
    with open(file_path, 'rb') as f:
        contents = f.read()
        repo.create_file(f"content/{filename}", f"Add chat file {filename}", contents)
    return response.response

docs_directory_path = "docs"
index = construct_index(docs_directory_path)
st.set_page_config(page_title="3-Year Degree Feedback")
chat_container = st.container()

if "last_send_pressed" not in st.session_state:
    st.session_state.last_send_pressed = False

if "admin_question" not in st.session_state:
    st.session_state.admin_question = "What is your main reason for visiting our website today?"

if "answered_admin_question" not in st.session_state:
    st.session_state.answered_admin_question = False

if "follow_up_question" not in st.session_state:
    st.session_state.follow_up_question = ""

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

if not st.session_state.answered_admin_question:
    input_text = form.text_input(st.session_state.admin_question)
elif st.session_state.follow_up_question:
    input_text = form.text_input(st.session_state.follow_up_question)
else:
    input_text = form.text_input("Enter your message:")

if form.form_submit_button() and input_text:
    if not st.session_state.answered_admin_question:
        st.session_state.answered_admin_question = True
        response = chatbot(input_text, first_name, email)
        st.session_state.follow_up_question = response
    elif st.session_state.follow_up_question:
        response = chatbot(input_text, first_name, email)
        st.session_state.follow_up_question = ""
    else:
        response = chatbot(input_text, first_name, email)
    with chat_container:
        st.write(f"{first_name}: {input_text}")
        st.write(f"Chatbot: {response}")

form.empty()

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)
