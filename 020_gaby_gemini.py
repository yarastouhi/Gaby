import os
import csv
import re
import json
import streamlit as st
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain_google_genai import GoogleGenerativeAI
import google.generativeai as genai
from datetime import datetime

def load_api_keys(filepath='credentials.json'):
    with open(filepath, 'r') as file:
        credentials_list = json.load(file)
    keys = {}
    for credentials in credentials_list:
        if credentials.get('service_provider') == 'google':
            keys['google'] = credentials.get('key')
        elif credentials.get('service_provider') == 'openai':
            keys['openai'] = credentials.get('key')
    return keys

def loader(csvfilename):
    links = {}
    with open(csvfilename, 'r', encoding='utf-8') as csvfile:
        datareader = csv.DictReader(csvfile)
        for row in datareader:
            links[row['Title']] = row['Link']
    return links

def find_urls(sentence):
    url_pattern = r'https?://\S+'
    return re.findall(url_pattern, sentence)

def match(csvall, ans):
    for title, link in csvall.items():
        if title.lower() in ans.lower():
            ans = ans.replace(title, f"{title}: {link}")
    return ans

def delete(answer, extracted_links):
    for url in extracted_links:
        if url in answer:
            answer = answer.replace(url, " ")
    return answer

def clean_urls(answer):
    return re.sub(r'[\[\]()]', '', answer)

def analyze(answer):
    extracted_links = find_urls(answer)
    if extracted_links:
        for url in extracted_links:
            if url in answer:
                answer = delete(answer, extracted_links)
    matched_ans = match(csvall, answer)
    # cleaned_ans = clean_urls(matched_ans)
    return matched_ans 

def write_to_csv(role, content, session_id, directory='logs_gemini'):
    os.makedirs(directory, exist_ok=True)
    filename = os.path.join(directory, f'conversation_{session_id}.csv')
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([role, content])

csvfilename = 'titles_and_links.csv'
csvall = loader(csvfilename)
titles = csvall.keys()
api_keys = load_api_keys()

if api_keys:
    os.environ['OPENAI_API_KEY'] = api_keys.get('openai')
    llm = GoogleGenerativeAI(model="gemini-pro", google_api_key=api_keys.get('google'), temperature=0.5)
    vector = Chroma("general_guides", OpenAIEmbeddings(), persist_directory='.chroma')

retriever = vector.as_retriever()

store = {}

contextualize_q_system_prompt = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
)

contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", contextualize_q_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}")
])

system_prompt = (
    """You are Gaby, a helpful AI library assistant at Concordia University Library. 
    Answer the questions from the perspective of Concordia University Library. 
    Ask follow-up questions for clarification if needed. If you don't know the answer, say that you don't know 
    and suggest speaking to a human librarian. Only provide links that are available in the context.
    If asked about recommendations for books or articles always provide the link to the Sofia Discovery Tool and never recommend books
    """
    "\n\n"
    "{context}"
)
qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder("store"),
        ("human", "{input}"),
    ]
)

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

conversational_chat = RunnableWithMessageHistory(
    create_retrieval_chain(
        create_history_aware_retriever(llm, retriever, contextualize_q_prompt),
        create_stuff_documents_chain(llm, qa_prompt)
    ),
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
    output_messages_key="answer"
)

concordia_logo = "conco-logo.png"
st.html("""
  <style>
    [alt=Logo] {
      height: 10rem;
    }
  </style>
        """)

st.logo(concordia_logo, link='https://library.concordia.ca/')
st.title("Concordia University Library Chatbot")

if 'session_id' not in st.session_state:
    st.session_state.session_id = datetime.now().strftime("%Y%m%d%H%M%S")

session_id = st.session_state.session_id

if 'messages' not in st.session_state:
    st.session_state.messages = []

user_input = st.chat_input("Say something")
st.html("""
  <a href="https://library.concordia.ca/"style="color:red;">Visit Concordia Library's Website</a>
   <p style="color:red;"><b>FlameGPT can make mistakes, check important information on our website. This version of Gaby uses Gemini. <b/></p> 
   <hr>
        """)

with st.sidebar:
    with st.form("Ask Us!"):
        st.write("Not satisfied? Ask us a question, we will get back to you shortly!")
        
        contact_method = st.selectbox(
            "How would you like to be contacted?",
            ("Email", "Mobile phone")
        )
        
        if contact_method is not None:
            contact_info = st.text_input("Enter your email" if contact_method == "Email" else "Enter your mobile phone number")
        
        inquiry = st.text_area("Enter your inquiry or question")
        
        submitted = st.form_submit_button("Submit")

if user_input:
    if user_input.lower() == "bye":
        st.write("Gaby: Goodbye!")
        st.session_state.messages.append({"role": "assistant", "content": "Goodbye!"})
        write_to_csv("assistant", "Goodbye!", session_id)
    else:
        st.session_state.messages.append({"role": "user", "content": user_input})
        write_to_csv("user", user_input, session_id)

        chatbot_input = {
            "input": user_input,
            "store": st.session_state.messages
        }

        response = conversational_chat.invoke(
            chatbot_input,
            config={
                "configurable": {"session_id": session_id}
            },
        )

        if 'answer' in response:
            answer = response['answer']
            enriched_answer = analyze(answer)

            second_prompt = ChatPromptTemplate.from_messages([
                ("system", "Rewrite this to be more grammatically correct. Use clearer language, and remove incomplete sentences. Do not add new links to the response. Do not remove links from the response. If there is a list, use bullet points."),
                ("user", "{input}")
            ])
            chain = second_prompt | llm
            corrected_response = chain.invoke({
                "input": enriched_answer,
                "store": st.session_state.messages,
                "context": ""
            })
            
            final_response = corrected_response
            print(final_response)
            st.session_state.messages.append({"role": "assistant", "content": final_response})
            write_to_csv("assistant", final_response, session_id)

for message in st.session_state.messages:
    role_prefix = "You:" if message["role"] == "user" else "Gaby:"
    avatar = "gabyd2.png" if message["role"] == "assistant" else None
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(f"{role_prefix} {message['content']}")
