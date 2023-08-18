import streamlit as st
from gpt_index import SimpleDirectoryReader, GPTSimpleVectorIndex, LLMPredictor, PromptHelper
from langchain.chat_models import ChatOpenAI
import os
from docx import Document

def construct_index(directory_path):
    prompt_helper = PromptHelper(4096, 512, 20, chunk_size_limit=600)
    llm_predictor = LLMPredictor(llm=ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo", max_tokens=512))
    documents = SimpleDirectoryReader(directory_path).load_data()
    index = GPTSimpleVectorIndex(documents, llm_predictor=llm_predictor, prompt_helper=prompt_helper)
    index.save_to_disk('index.json')
    return index

def chatbot(input_text):
    index = GPTSimpleVectorIndex.load_from_disk('index.json')
    prompt = f"How should I follow-up based on the user's response: '{input_text}'?"
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

if "interaction_step" not in st.session_state:
    st.session_state.interaction_step = 0
if "follow_up" not in st.session_state:
    st.session_state.follow_up = ""

if st.session_state.interaction_step % 2 == 0:
    current_question = questions[st.session_state.interaction_step // 2]
else:
    current_question = st.session_state.follow_up

input_text = form.text_input(current_question)

if form.form_submit_button() and input_text:
    with chat_container:
        st.write(f"{first_name}: {input_text}")

        if st.session_state.interaction_step % 2 == 0:
            st.session_state.follow_up = chatbot(input_text)
        st.session_state.interaction_step += 1

form.empty()

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)
