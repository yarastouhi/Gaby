import json
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import os

def load_api_keys(filepath='credentials.json'):
    with open('credentials.json', 'r') as file:
        credentials_list = json.load(file)
    for credentials in credentials_list:
        if credentials.get('service_provider')=='openai':
            return credentials.get('key')
    return None

api_keys = load_api_keys()

if api_keys:
    os.environ['OPENAI_API_KEY'] = api_keys

with open('gabysknowledge_final.txt', 'r') as file:
  knowledgeText = file.read()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=500,
                                               chunk_overlap=20)

documents = text_splitter.create_documents([knowledgeText])

embeddings = OpenAIEmbeddings()

store = Chroma("general_guides", embeddings, persist_directory='.chroma')
store.add_documents(documents)