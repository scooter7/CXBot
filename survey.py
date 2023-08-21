from github import Github
import streamlit as st
from datetime import datetime
import sys
import requests

openai_api_key = st.secrets["OPENAI_API_KEY"]
g = Github(st.secrets["GITHUB_TOKEN"])
repo = g.get_repo("scooter7/CXBot")

questions = ['Q1: Why did you visit our website today?', 'Q2: Where are you in your college decision process?', 'Q3: What are you thinking of majoring in?']

st.session_state.setdefault('current_question_index', 0)
st.session_state.setdefault('responses', [])
st.session_state.setdefault('follow_ups', [])
st.session_state.setdefault('demographics', {})

st.title("Survey QA Bot")

with st.container():
    for i in range(len(st.session_state.responses)):
        question_text = questions[i // 2] if i % 2 == 0 else st.session_state.follow_ups[i // 2]
        st.write("Bot:", question_text)
        st.write("You:", st.session_state.responses[i])

def get_followup_question(response, question):
    headers = {'Authorization': f'Bearer {openai_api_key}', 'Content-Type': 'application/json'}
    framed_prompt = f"The user was asked: '{question}'. They replied: '{response}'. What would be a good follow-up question?"
    data = {"model": "gpt-3.5-turbo", "messages": [{"role": "system", "content": "You are a helpful assistant."},{"role": "user", "content": framed_prompt},{"role": "assistant", "content": ""}],"temperature": 0.7}
    response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)
    follow_up = response.json()['choices'][0]['message']['content'].strip()
    return follow_up.replace("A good follow-up question could be:", "").strip()

def handle_input(user_input):
    st.session_state.responses.append(user_input)
    if len(st.session_state.responses) % 2 == 1:
        follow_up = get_followup_question(user_input, questions[st.session_state.current_question_index])
        st.session_state.follow_ups.append(follow_up)
    else:
        st.session_state.current_question_index += 1

def save_chat_history():
    chat_history = "\n".join([f"Bot: {questions[i // 2] if i % 2 == 0 else st.session_state.follow_ups[i // 2]}\nYou: {resp}" for i, resp in enumerate(st.session_state.responses)])
    demographics_data = "\n".join([f"{key}: {value}" for key, value in st.session_state.demographics.items()])
    complete_history = f"{chat_history}\n\n--- Demographics ---\n{demographics_data}"
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = f"content/chat_history_{current_time}.txt"
    repo.create_file(file_path, "Add chat history", complete_history)

if st.session_state.current_question_index < len(questions):
    next_question = questions[st.session_state.current_question_index] if len(st.session_state.responses) % 2 == 0 else st.session_state.follow_ups[-1]
    st.write("Bot:", next_question)
    user_input = st.text_input("Your Response:", value=st.session_state.get('user_input', ''), key="user_input")
    if st.button("Submit"):
        handle_input(user_input)
else:
    st.subheader("We just need a bit more information, especially if you are eligible for an incentive.")
    st.session_state.demographics['Full Name'] = st.text_input("Full Name:")
    st.session_state.demographics['Email Address'] = st.text_input("Email Address:")
    st.session_state.demographics['Gender Identity'] = st.selectbox("Which of these best describes your current gender identity?", ["Cisgender female/woman", "Cisgender male/man", "Non-binary", "Transgender female/woman", "Transgender male/man", "A gender not listed here", "Prefer to not say"])
    st.session_state.demographics['Age'] = st.selectbox("Age", ["17 or under", "18-24 years old", "25-34 years old", "35-44 years old", "45-54 years old", "55-64 years old", "65-74 years old", "75 years or older"])
    st.session_state.demographics['Ethnicity'] = st.selectbox("Which best describes you?", ["Asian or Asian American", "Black or African American", "Hispanic, Latino, or Spanish", "Middle Eastern", "White or Caucasian", "North American Indigenous", "Hawaiian native or Pacific Islander", "Other", "Prefer to not say"])
    st.session_state.demographics['Zip Code'] = st.text_input("What is your 5-digit zip code (if you live in the United States)?")
    if st.button("Finish"):
        save_chat_history()
        st.write("Thank You!")
