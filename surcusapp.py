from github import Github
import streamlit as st
import boto3
import pandas as pd
from io import StringIO
from datetime import datetime
import requests

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Please set the OPENAI_API_KEY secret on the Streamlit dashboard.")
    return

openai_api_key = st.secrets["OPENAI_API_KEY"]

s3 = boto3.client('s3', aws_access_key_id=st.secrets["AWS"]["aws_access_key_id"], aws_secret_access_key=st.secrets["AWS"]["aws_secret_access_key"])
bucket_name = st.secrets["AWS"]["bucket_name"]
object_key = st.secrets["AWS"]["object_key"]

def upload_csv_to_s3(df):
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    s3.put_object(Bucket=bucket_name, Key=object_key, Body=csv_buffer.getvalue())

def get_followup_question(response, question):
    headers = {'Authorization': f'Bearer {openai_api_key}', 'Content-Type': 'application/json'}
    framed_prompt = f"The user was asked: '{question}'. They replied: '{response}'. What would be a good follow-up question?"
    data = {"model": "gpt-3.5-turbo", "messages": [{"role": "system", "content": "You are a helpful assistant."},{"role": "user", "content": framed_prompt},{"role": "assistant", "content": ""}],"temperature": 0.7}
    response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)
    response_data = response.json()
    if 'choices' in response_data:
        follow_up = response_data['choices'][0]['message']['content'].strip()
        return follow_up.replace("A good follow-up question could be:", "").strip()
    else:
        st.error(f"Error in getting follow-up question: {response_data.get('error', 'Unknown error')}")
        return "Could not generate a follow-up question at this time."

def handle_input():
    user_input = st.session_state.user_input
    st.session_state.responses.append(user_input)
    if len(st.session_state.responses) % 2 == 1:
        follow_up = get_followup_question(user_input, questions[st.session_state.current_question_index])
        st.session_state.follow_ups.append(follow_up)
    else:
        st.session_state.current_question_index += 1
    st.session_state.user_input = ""

def save_chat_history():
    columns = ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Full Name", "Email Address", "Gender", "Age", "Describes", "Zip Code"]
    data = {}
    q_and_a = st.session_state.responses
    q_and_a = q_and_a + [None] * (6 - len(q_and_a))
    data.update({columns[i]: q_and_a[i] for i in range(6)})
    data.update(st.session_state.demographics)
    df = pd.DataFrame([data], columns=columns)
    upload_csv_to_s3(df)
    st.write("Data saved to S3 bucket.")

questions = ['Q1: Why did you visit our website today?', 'Q2: Where are you in your college decision process?', 'Q3: What are you thinking of majoring in?']

st.session_state.setdefault('current_question_index', 0)
st.session_state.setdefault('responses', [])
st.session_state.setdefault('follow_ups', [])
st.session_state.setdefault('demographics', {})

st.title("SurCus: Half Survey, Half Focus Group")

with st.container():
    for i in range(len(st.session_state.responses)):
        question_text = questions[i // 2] if i % 2 == 0 else st.session_state.follow_ups[i // 2]
        st.write("Bot:", question_text)
        st.write("You:", st.session_state.responses[i])

if st.session_state.current_question_index < len(questions):
    next_question = questions[st.session_state.current_question_index] if len(st.session_state.responses) % 2 == 0 else st.session_state.follow_ups[-1]
    st.write("Bot:", next_question)
    st.text_input("Your Response:", value=st.session_state.get('user_input', ''), on_change=handle_input, key="user_input")
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
