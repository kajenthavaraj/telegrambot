import os
import requests
import openai
from langchain.vectorstores import FAISS
#pip install -qU langchain-openai
from langchain_openai import OpenAIEmbeddings

import time
from io import StringIO

import pandas as pd
import csv

from typing import List, Callable


# def load_qa_csv_faq(csv_files: List[str]):
#     faq_vectors = []

#     for csv_file in csv_files:
#         df = pd.read_csv(csv_file)

#         questions = df.iloc[:, 0].tolist()
#         answers = df.iloc[:, 1].tolist()

#         print(answers)

#         for question, answer in zip(questions, answers):
#             faq_vector = f"Question: {question}\nAnswer: {answer}"
#             faq_vectors.append(faq_vector)

#     return faq_vectors

def load_qa_csv_faq(csv_urls: List[str]):
    faq_vectors = []
    for csv_url in csv_urls:
        # Send a GET request to the URL
        response = requests.get(csv_url)
        # print(response.text)
        # Check if the request was successful
        response.raise_for_status()

        # Use StringIO to make the response content look like a file
        csvfile = StringIO(response.text)
        
        # Use the csv reader to parse this "file"
        reader = csv.reader(csvfile)
        next(reader)  # Skip the header row
        for row in reader:
            # Make sure there is a question and an answer before appending
            if len(row) >= 2:
                faq_vector = f"Question: {row[0]}\nAnswer: {row[1]}"
                faq_vectors.append(faq_vector)
    
    return faq_vectors


def load_generated_csv_faq(csv_urls: List[str]) -> List[str]:
    answers = []
    for csv_url in csv_urls:
        response = requests.get(csv_url)
        response.raise_for_status()  # This will ensure that an HTTPError is raised for certain status codes

        csv_data = StringIO(response.text)
        df = pd.read_csv(csv_data)

        answers.extend(df.iloc[:, 0].tolist())

    return answers




def build_knowledge_base(faq_vectors, index_name):
    OPENAI_API_KEY = "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"
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

    start = time.time()
    print(f"Now you have {len(faq_vectors)} faq documents")

    db = FAISS.from_texts(faq_vectors, embeddings)
    end = time.time()
    print("KB Base Population Time: ", end - start)

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



def create_answers_knowledge_base(gdrive_urls, index_name):
    documents = []
    for url in gdrive_urls:
        # ####### Create Knowledge Base #######
        # Extract the file ID from the Google Drive URL
        file_id = url.split('/d/')[1].split('/view')[0]
        # Construct the direct CSV download URL for Google Sheets
        download_url = f'https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv'
        print(download_url)
        faq_vectors = load_generated_csv_faq([download_url])
        documents.extend(faq_vectors)
    
    knowledge_base = build_knowledge_base(documents, index_name)

    return knowledge_base


def create_qa_knowledge_base(gdrive_urls, index_name):
    documents = []
    for url in gdrive_urls:
        # ####### Create Knowledge Base #######
        # Extract the file ID from the Google Drive URL
        if("/view" in url):
            file_id = url.split('/d/')[1].split('/view')[0]
        elif("/edit" in url):
            file_id = url.split('/d/')[1].split('/edit')[0]
        else:
            print("INCORRECT URL, must have /view or /edit inside the URL path")
        
        # Construct the direct CSV download URL for Google Sheets
        download_url = f'https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv'
        print(download_url)
        faq_vectors = load_qa_csv_faq([download_url])
        # print("faq_vectors")
        # print(faq_vectors)
        documents.extend(faq_vectors)
    
    knowledge_base = build_knowledge_base(documents, index_name)

    return knowledge_base




def load_knowledge_base(index_name):
    OPENAI_API_KEY = "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"
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    
    try:
        db = FAISS.load_local(index_name, embeddings)
        return db
    
    except:
        return False




if __name__ == "__main__":
    # Build Veronica Knowledge Base:
    gdrive_urls = ["https://docs.google.com/spreadsheets/d/1f4awYjjNY28nSd7v-niigCBkO7jI6HMagvX7Fa6_Seg/view?usp=sharing"]
    knowledge_base = create_answers_knowledge_base(gdrive_urls, "veronica_kb")


    # Build Texting Performance Base:
    gdrive_urls = ["https://docs.google.com/spreadsheets/d/1g4vhty-OIhHhaVgEFgcnWYx-MRxpcuul1eZEC7MjvdQ/view?usp=sharing"]
    knowledge_base = create_qa_knowledge_base(gdrive_urls, "texting_performance")


# knowledge_base_info = retrieve_info(knowledge_base, "milk", 3)
# print("knowledge_base_info: ", knowledge_base_info)

# knowledge_base = load_knowledge_base("faq_db")
# knowledge_base_info = retrieve_info(knowledge_base, "milk", 3)
# print(knowledge_base_info)