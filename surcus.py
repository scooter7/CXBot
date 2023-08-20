from github import Github
from google.oauth2.service_account import Credentials
import gspread
import streamlit as st
from datetime import datetime
import requests
import json

def save_to_google_sheet():
    json_url = "https://raw.githubusercontent.com/scooter7/CXBot/main/service_account.json?token=GHSAT0AAAAAACD5LVXVMAWMD7VDJK4MCVDQZHBQTVQ"
    response = requests.get(json_url)
    creds_json = json.loads(response.text)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_json, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1_-R8Vdyiq5nzTWTV21vxEFPalIij__gll36hBXazc7A/edit?usp=sharing").sheet1
    session_data = [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
    for i, resp in enumerate(st.session_state.responses):
        question_text = questions[i // 2] if i % 2 == 0 else st.session_state.follow_ups[i // 2]
        session_data.append(question_text)
        session_data.append(resp)
    for key, value in st.session_state.demographics.items():
        session_data.append(key)
        session_data.append(value)
    sheet.append_row(session_data)

questions = ['Q1: Why did you visit our website today?', 'Q2: Where are you in your college decision process?', 'Q3: What are you thinking of majoring in?']
st.session_state.setdefault('current_question_index', 0)
st.session_state.setdefault('responses', [])
st.session_state.setdefault('follow_ups', [])
st.session_state.setdefault('demographics', {})

if st.session_state.current_question_index < len(questions):
    next_question = questions[st.session_state.current_question_index]
    st.write("Bot:", next_question)
    user_input = st.text_input("Your Response:", value='', key="user_input")
    if user_input:
        st.session_state.responses.append(user_input)
        st.session_state.current_question_index += 1
else:
    st.subheader("We just need a bit more information, especially if you are eligible for an incentive.")
    st.session_state.demographics['Full Name'] = st.text_input("Full Name:")
    st.session_state.demographics['Email Address'] = st.text_input("Email Address:")
    st.session_state.demographics['Gender Identity'] = st.selectbox("Which of these best describes your current gender identity?", ["Cisgender female/woman", "Cisgender male/man", "Non-binary", "Transgender female/woman", "Transgender male/man", "A gender not listed here", "Prefer to not say"])
    st.session_state.demographics['Age'] = st.selectbox("Age", ["17 or under", "18-24 years old", "25-34 years old", "35-44 years old", "45-54 years old", "55-64 years old", "65-74 years old", "75 years or older"])
    st.session_state.demographics['Ethnicity'] = st.selectbox("Which best describes you?", ["Asian or Asian American", "Black or African American", "Hispanic, Latino, or Spanish", "Middle Eastern", "White or Caucasian", "North American Indigenous", "Hawaiian native or Pacific Islander", "Other", "Prefer to not say"])
    st.session_state.demographics['Zip Code'] = st.text_input("What is your 5-digit zip code (if you live in the United States)?")
    if st.button("Finish"):
        save_to_google_sheet()
        st.write("Thank You!")