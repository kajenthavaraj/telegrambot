import os
import openai
from langchain.vectorstores import FAISS
#pip install -qU langchain-openai
from langchain_openai import OpenAIEmbeddings

import time

import pandas as pd
from typing import List, Callable


def load_qa_csv_faq(csv_files: List[str]):
    faq_vectors = []

    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        questions = df.iloc[:, 0].tolist()
        answers = df.iloc[:, 1].tolist()

        for question, answer in zip(questions, answers):
            faq_vector = f"Question: {question}\nAnswer: {answer}"
            faq_vectors.append(faq_vector)

    return faq_vectors

def load_generated_csv_faq(csv_files: List[str]):

    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        answers = df.iloc[:, 0].tolist()

    return answers

def build_knowledge_base(faq_vectors):
    OPENAI_API_KEY = "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"
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

    start = time.time()
    print(f"Now you have {len(faq_vectors)} faq documents")

    db = FAISS.from_texts(faq_vectors, embeddings)
    end = time.time()
    print("KB Base Population Time: ", end - start)

    index_name = "faq_db"
    db.save_local(index_name)

    return FAISS.load_local(index_name, embeddings)



# Inputs: vector_db_instance, query, num_vectors
def retrieve_info(db, query, k):
    start = time.time()
    similar_response = db.similarity_search(query, k=k)
    page_contents_array = [doc.page_content for doc in similar_response]
    end = time.time()

    print("Retrieval Time: ", end - start)
    return page_contents_array



def create_answers_knowledge_base(gdrive_urls):
    documents = []
    for url in gdrive_urls:
        # ####### Create Knowledge Base #######
        # Extract the file ID from the Google Drive URL
        file_id = url.split('/d/')[1].split('/view')[0]
        # Construct the direct CSV download URL for Google Sheets
        download_url = f'https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv'
        faq_vectors = load_generated_csv_faq([download_url])
        documents.extend(faq_vectors)
    
    knowledge_base = build_knowledge_base(documents)

    return knowledge_base


def create_qa_knowledge_base(gdrive_urls):
    documents = []
    for url in gdrive_urls:
        # ####### Create Knowledge Base #######
        # Extract the file ID from the Google Drive URL
        file_id = url.split('/d/')[1].split('/view')[0]
        # Construct the direct CSV download URL for Google Sheets
        download_url = f'https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv'
        faq_vectors = load_qa_csv_faq([download_url])
        documents.extend(faq_vectors)
    
    knowledge_base = build_knowledge_base(documents)

    return knowledge_base


# Usage:

# gdrive_urls = ["https://docs.google.com/spreadsheets/d/1f4awYjjNY28nSd7v-niigCBkO7jI6HMagvX7Fa6_Seg/view?usp=sharing"]
# knowledge_base = create_answers_knowledge_base(gdrive_urls)

# knowledge_base_info = retrieve_info(knowledge_base, "milf", 3)
# print("knowledge_base_info: ", knowledge_base_info)