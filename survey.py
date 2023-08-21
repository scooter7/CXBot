import streamlit as st
import requests

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

def get_followup_question(response, question):
    headers = {
        'Authorization': f'Bearer {openai_api_key}',
        'Content-Type': 'application/json'
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

if st.session_state.current_question_index < len(questions):
    question = questions[st.session_state.current_question_index]
    st.write("Bot:", question)
    user_input = st.text_input("Your Response:")
    if st.button("Submit"):
        st.session_state.responses.append(user_input)
        if len(st.session_state.responses) % 2 == 1:
            follow_up_question = get_followup_question(
                user_input, questions[st.session_state.current_question_index]
            )
            st.session_state.follow_ups.append(follow_up_question)
        st.session_state.current_question_index += 1

with st.container():
    for i in range(len(st.session_state.responses)):
        if i % 2 == 0:
            bot_message = questions[i]
        else:
            if i // 2 < len(st.session_state.follow_ups):
                bot_message = st.session_state.follow_ups[i // 2]
            else:
                bot_message = ""
        st.write("Bot:", bot_message)
        st.write("You:", st.session_state.responses[i])

if st.session_state.current_question_index >= len(questions):
    st.subheader("We just need a bit more information, especially if you are eligible for an incentive.")
    st.session_state.demographics = {
        'Full Name': st.text_input("Full Name:"),
        'Email Address': st.text_input("Email Address:"),
        'Gender Identity': st.selectbox("Which of these best describes your current gender identity?", [
            "Cisgender female/woman", "Cisgender male/man", "Non-binary",
            "Transgender female/woman", "Transgender male/man", "A gender not listed here", "Prefer to not say"
        ]),
        'Age': st.selectbox("Age", [
            "17 or under", "18-24 years old", "25-34 years old", "35-44 years old",
            "45-54 years old", "55-64 years old", "65-74 years old", "75 years or older"
        ]),
        'Ethnicity': st.selectbox("Which best describes you?", [
            "Asian or Asian American", "Black or African American", "Hispanic, Latino, or Spanish",
            "Middle Eastern", "White or Caucasian", "North American Indigenous",
            "Hawaiian native or Pacific Islander", "Other", "Prefer to not say"
        ]),
        'Zip Code': st.text_input("What is your 5-digit zip code (if you live in the United States)?")
    }
    if st.button("Finish"):
        st.write("Thank You!")
