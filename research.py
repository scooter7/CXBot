import streamlit as st
from gpt_index import SimpleDirectoryReader, GPTSimpleVectorIndex, LLMPredictor, PromptHelper
from langchain.chat_models import ChatOpenAI
from datetime import datetime
import os
from docx import Document

def construct_index(directory_path):
    prompt_helper = PromptHelper(4096, 512, 20, chunk_size_limit=600)
    llm_predictor = LLMPredictor(llm=ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo", max_tokens=512))
    documents = SimpleDirectoryReader(directory_path).load_data()
    index = GPTSimpleVectorIndex(documents, llm_predictor=llm_predictor, prompt_helper=prompt_helper)
    index.directory_path = directory_path
    index.save_to_disk('index.json')
    return index

def chatbot(input_text):
    index = GPTSimpleVectorIndex.load_from_disk('index.json')
    prompt = f"The user said: '{input_text}'. How should I follow-up based on their response?"
    response = index.query(prompt, response_mode="compact")
    return response.response

docs_directory_path = "docs"
index = construct_index(docs_directory_path)
st.set_page_config(page_title="3-Year Degree Feedback")
chat_container = st.container()

doc = Document(os.path.join(docs_directory_path, "questions.docx"))
questions = [para.text for para in doc.paragraphs if para.text]

form = st.form(key="my_form", clear_on_submit=True)
first_name = form.text_input("Enter your first name:", key="first_name")
email = form.text_input("Enter your email address:", key="email")

if "current_question_index" not in st.session_state:
    st.session_state.current_question_index = 0
if "awaiting_follow_up" not in st.session_state:
    st.session_state.awaiting_follow_up = False

if st.session_state.awaiting_follow_up:
    current_question = chatbot(st.session_state.last_user_response)
else:
    current_question = questions[st.session_state.current_question_index].strip()

input_text = form.text_input(current_question)

if form.form_submit_button() and input_text:
    with chat_container:
        st.write(f"{first_name}: {input_text}")

        if st.session_state.awaiting_follow_up:
            st.session_state.awaiting_follow_up = False
            st.session_state.current_question_index += 1
        else:
            st.session_state.awaiting_follow_up = True
        st.session_state.last_user_response = input_text

form.empty()

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)
