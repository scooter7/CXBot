import streamlit as st
import sys
import requests

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Please set the OPENAI_API_KEY secret on the Streamlit dashboard.")
    sys.exit(1)

openai_api_key = st.secrets["OPENAI_API_KEY"]

questions = [
    'Q1: Why did you visit our website today?',
    'Q2: Where are you in your college decision process?',
    'Q3: What are you thinking of majoring in?'
]

st.session_state.setdefault('current_question_index', 0)
st.session_state.setdefault('responses', [])
st.session_state.setdefault('follow_ups', [])

st.title("Survey QA Bot")
st.button("Clear message", on_click=lambda: [st.session_state.current_question_index, st.session_state.responses.clear(), st.session_state.follow_ups.clear()])

with st.container():
    for question, response in zip(st.session_state.questions, st.session_state.responses):
        st.write("Bot:", question)
        st.write("You:", response)
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
    follow_up = response.json()['choices'][0]['message']['content'].strip()
    return follow_up.replace("A good follow-up question could be:", "").strip()

def handle_input():
    user_input = st.session_state.user_input
    st.session_state.responses.append(user_input)
    if len(st.session_state.responses) % 2 == 1:
        follow_up = get_followup_question(user_input, questions[st.session_state.current_question_index])
        st.session_state.follow_ups.append(follow_up)
    else:
        st.session_state.current_question_index += 1

if st.session_state.current_question_index < len(questions):
    next_question = questions[st.session_state.current_question_index]
    st.write("Bot:", next_question if len(st.session_state.responses) % 2 == 0 else st.session_state.follow_ups[-1])
    st.text_input("Your Response:", on_change=handle_input, key="user_input")
