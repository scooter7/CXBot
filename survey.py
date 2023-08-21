from github import Github
import streamlit as st
from datetime import datetime
import sys
import requests

class SurveyApp:
    def __init__(self):
        self.openai_api_key = st.secrets["OPENAI_API_KEY"]
        self.g = Github(st.secrets["GITHUB_TOKEN"])
        self.repo = self.g.get_repo("scooter7/CXBot")
        self.questions = ['Q1: Why did you visit our website today?', 'Q2: Where are you in your college decision process?', 'Q3: What are you thinking of majoring in?']
        self.current_question_index = st.session_state.setdefault('current_question_index', 0)
        self.responses = st.session_state.setdefault('responses', [])
        self.follow_ups = st.session_state.setdefault('follow_ups', [])
        self.demographics = st.session_state.setdefault('demographics', {})
        self.user_input_temp = ""

    def get_followup_question(self, response, question):
        headers = {'Authorization': f'Bearer {self.openai_api_key}', 'Content-Type': 'application/json'}
        framed_prompt = f"The user was asked: '{question}'. They replied: '{response}'. What would be a good follow-up question?"
        data = {"model": "gpt-3.5-turbo", "messages": [{"role": "system", "content": "You are a helpful assistant."},{"role": "user", "content": framed_prompt},{"role": "assistant", "content": ""}],"temperature": 0.7}
        response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)
        follow_up = response.json()['choices'][0]['message']['content'].strip()
        return follow_up.replace("A good follow-up question could be:", "").strip()

    def handle_input(self):
        user_input = self.user_input_temp
        self.responses.append(user_input)
        if len(self.responses) % 2 == 1:
            if len(self.follow_ups) <= len(self.responses) // 2:
                follow_up = self.get_followup_question(user_input, self.questions[self.current_question_index])
                self.follow_ups.append(follow_up)
        else:
            self.current_question_index += 1
        self.user_input_temp = ""

    def run(self):
        st.title("Survey QA Bot")
        
        with st.container():
            for i in range(len(self.responses)):
                question_text = self.questions[i // 2] if i % 2 == 0 else self.follow_ups[i // 2]
                st.write("Bot:", question_text)
                st.write("You:", self.responses[i])
        
        if self.current_question_index < len(self.questions):
            next_question = self.questions[self.current_question_index] if len(self.responses) % 2 == 0 else self.follow_ups[-1]
            st.write("Bot:", next_question)
            
            self.user_input_temp = st.text_area("Your Response:", value=self.user_input_temp, key="user_input")
            if st.button("Submit"):
                self.handle_input()
        else:
            st.subheader("We just need a bit more information, especially if you are eligible for an incentive.")
            
            if st.button("Finish"):
                self.save_chat_history()
                st.write("Thank You!")
    
    def save_chat_history(self):
        chat_history = "\n".join([f"Bot: {self.questions[i // 2] if i % 2 == 0 else self.follow_ups[i // 2]}\nYou: {resp}" for i, resp in enumerate(self.responses)])
        demographics_data = "\n".join([f"{key}: {value}" for key, value in self.demographics.items()])
        complete_history = f"{chat_history}\n\n--- Demographics ---\n{demographics_data}"
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = f"content/chat_history_{current_time}.txt"
        self.repo.create_file(file_path, "Add chat history", complete_history)

app = SurveyApp()
app.run()
