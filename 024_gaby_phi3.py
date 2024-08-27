import os
import csv
import re
import json
import streamlit as st
from langchain_community.llms import Ollama
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from datetime import datetime

def load_api_keys(filepath='credentials.json'):
    with open(filepath, 'r') as file:
        credentials_list = json.load(file)
    for credentials in credentials_list:
        if credentials.get('service_provider') == 'openai':
            return credentials.get('key')
    return None

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

def analyze(answer):
    extracted_links = find_urls(answer)
    if extracted_links:
        for url in extracted_links:
            if url in answer:
                answer = delete(answer, extracted_links)
    matched_ans = match(csvall, answer)
    chat_history.append(AIMessage(content=matched_ans))
    return matched_ans

# def write_to_csv(role, content, session_id, directory='logs'):
#     os.makedirs(directory, exist_ok=True)
#     filename = os.path.join(directory, f'conversation_{session_id}.csv')
#     with open(filename, mode='a', newline='', encoding='utf-8') as file:
#         writer = csv.writer(file)
#         writer.writerow([role, content])

def write_to_csv(role, content, session_id, directory='logs_phi3'):
    os.makedirs(directory, exist_ok=True)
    filename = os.path.join(directory, f'conversation_{session_id}.csv')
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([role, content])

def save_feedback(rating, comments, email, filename='surveys/feedback.csv'):
    os.makedirs('surveys', exist_ok=True)
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([rating, comments, email])

def remove_extra_prefixes(response):
    prefixes = ["Gaby:", "AI:", "System:"]
    for prefix in prefixes:
        response = re.sub(f"{prefix} ", "", response)
    return response

csvfilename = 'titles_and_links.csv'
csvall = loader(csvfilename)
titles = csvall.keys()
 
# llm = Ollama(model="llama2", temperature=0.1)
api_keys = load_api_keys()

if api_keys:
    os.environ['OPENAI_API_KEY'] = api_keys
    vector = Chroma("general_guides", OpenAIEmbeddings(), persist_directory='.chroma')
    llm = Ollama(model="phi3", temperature=0.1)
prompt = ChatPromptTemplate.from_messages([
    ("system", """
**For Retrieval:**

<context>
{context}
</context>

**Question to ask Gaby** 
You are Gaby, an AI library assistant at Concordia University Library. Answer the questions from the perspective of the context. Ask follow-up questions for clarification if needed. If you don't know the answer, say that you don't know and suggest speaking to a human librarian. Only provide links that are available in the context. If asked about recommendations for books, articles always provide the link to the Sofia Discovery Tool and never recommend books.
"""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{input}"),
])
 
def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

retriever = vector.as_retriever()
document_chain = create_stuff_documents_chain(llm, prompt)
retrieval_chain = create_retrieval_chain(retriever, document_chain)
chat_history = []
 

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

# session_id = "my_session"

if 'session_id' not in st.session_state:
    st.session_state.session_id = datetime.now().strftime("%Y%m%d%H%M%S")

session_id = st.session_state.session_id

if 'messages' not in st.session_state:
    st.session_state.messages = []

user_input = st.chat_input("Say something")
st.html("""
  <a href="https://library.concordia.ca/"style="color:red;">Visit Concordia Library's Website</a>
   <p style="color:#fefefe;"><b>Gaby</b> can make mistakes, check important information on our website.</p> 
   <p>This version of <b>Gaby</b> uses PHI-3. </p> 
   <hr>
        """)

with st.sidebar:
    st.write("Feedback Survey")
    rating = st.slider("Rate your experience with Gaby", 1, 5)
    comments = st.text_area("Any comments or suggestions?")
    email = st.text_input("Email")
    if st.button("Submit Feedback"):
        save_feedback(rating, comments, email)
        st.write("Thank you for your feedback!")

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
            "chat_history": st.session_state.messages,
            "context": ""
        }

        response = retrieval_chain.invoke(
            chatbot_input,
            config={
                "configurable": {"session_id": session_id}
            },
        )


        if 'answer' in response:
            answer = response['answer']
            enriched_answer = analyze(answer)
            print("First: ", enriched_answer)
            second_prompt = ChatPromptTemplate.from_messages([
                ("system", "Rewrite this to be more grammatically correct. Use clearer language, and remove incomplete sentences. Do not add new links to the response. Do not remove links from the response. If there is a list, use bullet points."),
                ("user", "{input}")
            ])
            chain = second_prompt | llm
            corrected_response = chain.invoke({
                "input": enriched_answer,
                "chat_history": st.session_state.messages,
                "context": ""
            })
            final_response = remove_extra_prefixes(corrected_response)
            print("Second: ",corrected_response)
            # final_response = corrected_response
            # if "AI:" or "Gaby:" or "System:" in final_response:
            #     final_response.replace("AI:" or "Gaby:" or "System:", "")
            st.session_state.messages.append({"role": "assistant", "content": final_response})
            write_to_csv("assistant", final_response, session_id)

# for message in st.session_state.messages:
#     role_prefix = "You:" if message["role"] == "user" else "Gaby:"
#     avatar = "gabyd2.png" if message["role"] == "assistant" else None
#     with st.chat_message(message["role"], avatar=avatar):
#         st.markdown(f"{role_prefix} {message['content']}")

for message in st.session_state.messages:
    if message["role"] == "user":
        role_prefix = "You:"
        avatar = None
    else:  # message["role"] == "assistant"
        role_prefix = "Gaby:"
        avatar = "gabyd2.png"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(f"{role_prefix} {message['content']}")