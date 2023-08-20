import streamlit as st
import sys
import requests

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Please set the OPENAI_API_KEY secret on the Streamlit dashboard.")
    sys.exit(1)

openai_api_key = st.secrets["OPENAI_API_KEY"]

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

if len(st.session_state.questions) > len(st.session_state.responses):
    next_question = st.session_state.questions[len(st.session_state.responses)]
    if next_question:
        st.write("Bot:", next_question)
        st.text_input("Your Response:", on_change=handle_input, key="user_input")
