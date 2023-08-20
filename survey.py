import streamlit as st
import sys
from github import Github
import requests

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Please set the OPENAI_API_KEY secret on the Streamlit dashboard.")
    sys.exit(1)

if "GITHUB_TOKEN" not in st.secrets:
    st.error("Please set the GITHUB_TOKEN secret on the Streamlit dashboard.")
    sys.exit(1)

openai_api_key = st.secrets["OPENAI_API_KEY"]
g = Github(st.secrets["GITHUB_TOKEN"])
repo = g.get_repo("scooter7/CXBot")

questions = [
    'Q1: Why did you visit our website today?',
    '',
    'Q2: Where are you in your college decision process?',
    '',
    'Q3: What are you thinking of majoring in?',
    ''
]

st.session_state.setdefault('questions', questions)
st.session_state.setdefault('responses', [])
st.session_state.setdefault('follow_ups', [])

st.title("Survey QA Bot")

st.button("Clear message", on_click=lambda: [st.session_state.responses.clear(), st.session_state.follow_ups.clear()])

with st.container():
    for response, question in zip(st.session_state.responses, st.session_state.questions[1:]):
        st.write("You:", response)
        st.write("Bot:", question)
    for follow_up in st.session_state.follow_ups:
        st.write("Bot:", follow_up)

def save_chat_history_to_github():
    chat_history = ""
    for response, question in zip(st.session_state.responses, st.session_state.questions[1:]):
        chat_history += f"You: {response}\n"
        chat_history += f"Bot: {question}\n"
    for follow_up in st.session_state.follow_ups:
        chat_history += f"Bot: {follow_up}\n"
    repo.create_file(f"content/chat_history_{len(st.session_state.responses)}.txt", "Add chat history", chat_history)

def get_followup_question(response, question):
    headers = {
        'Authorization': f'Bearer {openai_api_key}',
        'Content-Type': 'application/json',
    }
    
    framed_prompt = f"The user was asked: '{question}'. They replied: '{response}'. What would be a good follow-up question?"
    
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": framed_prompt},
            {"role": "assistant", "content": ""}
        ],
        "temperature": 0.7
    }
    
    response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)
    return response.json()['choices'][0]['message']['content'].strip()

def handle_input():
    user_input = st.session_state.user_input
    st.session_state.responses.append(user_input)
    follow_up = get_followup_question(user_input, st.session_state.questions[len(st.session_state.responses) - 1])
    st.session_state.follow_ups.append(follow_up)
    save_chat_history_to_github()

if len(st.session_state.questions) > len(st.session_state.responses):
    next_question = st.session_state.questions[len(st.session_state.responses)]
    if next_question:
        st.write("Bot:", next_question)
        st.text_input("Your Response:", on_change=handle_input, key="user_input")
