import os
import sys
import json
import faiss
import logging
import numpy as np
from groq import Groq
from pathlib import Path
from pypdf import PdfReader
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - %(levelname)s - %(message)s',
    handlers = [
        logging.FileHandler('rag_chatbot.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

model = SentenceTransformer('all-MiniLM-L6-v2')
CHAT_MODEL = 'llama-3.3-70b-versatile'
API_KEY = os.getenv('GROQ_API_KEY')
if not API_KEY:
    log.error('GROQ_API_KEY not found')
    sys.exit(1)
client = Groq(api_key=API_KEY)

PROMPT = """You are a helpful assistant similar to Tony Stark's JARVIS. Use the following context to answer the question. If you don't know the answer, say you don't know. Be concise and concrete.
context: {search_results}"""


# -------- Extracting Text ---------
def extract_text(file):
    extracted_text = ''
    reader = PdfReader(file)
    try:
        for page in reader.pages:
            text = page.extract_text()
            extracted_text += text
        log.info('Text extracted')    
        return extracted_text
    except Exception as e:
        log.error(f'Error extracting the text from the pdf: {e}')
        sys.exit(1)

# ---------- Chunking Text ----------
def chunk_text(extracted_text ,chunk_size=500, overlap=50):

    chunks = []
    start = 0

    while start < len(extracted_text):
        end = start + chunk_size
        chunk = extracted_text[start:end]
        chunks.append(chunk)
        start = end - overlap
    return chunks
    
# ------------ Vector Store -------------
def build_vector_store(chunks, model):
    embeddings = model.encode(chunks, convert_to_numpy=True).astype(np.float32)
    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    return index

#  ---------- Embedding and Searching query ----------
def search(query, index, chunks, model, k = 5):
    query_embedding = model.encode(query)
    query_embedding= np.array(query_embedding, dtype=np.float32).reshape(1, -1)
    distances, indices = index.search(query_embedding, k)
    return [chunks[i] for i in indices[0]]
     
def chatbot_answer(query, search_results, messages):
    system_message = {"role": "system", "content": PROMPT.format(search_results=search_results)}
    user_message = {"role": "user", "content": query}
    full_messages = [system_message] + messages + [user_message]
    stream = client.chat.completions.create(
        model = CHAT_MODEL,
        messages = full_messages,
        stream =True,
        max_tokens = 1024
    )
    full_response = ""
    for bit in stream:
        delta = bit.choices[0].delta
        if delta.content:
            print(delta.content, end='', flush=True)
            full_response += delta.content
    return(full_response)

def save_session(messages, session_file):
    try:
        with open(session_file, "w") as f:
            json.dump(messages, f, indent = 2)
    except Exception as e:
        log.error(f'Error saving the session: {e}')
        sys.exit(1)   

if __name__ == '__main__':    
    try:
        messages = []
        try: 
            document = input('Enter the file path of the document: ').strip('"')
            if Path(document).exists():
                extracted_text = extract_text(document)
                chunked_text = chunk_text(extracted_text)
                vector_store = build_vector_store(chunked_text, model)
            else:
                print('No document provided. Exiting...')
                log.info('No document provided.')
        except Exception as e:
            log.error(f'Error processing the document: {e}')
            sys.exit(1)
        while True:
            query = input('\nEnter your query: ')
            if query.lower() == 'quit':
                print("Goodbye")
                log.info('Session ended and saved to chat_session.json')
                break
            if query.lower() == 'save':
                save_session(messages, 'chat_session.json')
                log.info('Session saved to chat_session.json')
                print("Session saved to chat_session.json")
            messages.append({"role": "user", "content": query})
            search_results = search(query, vector_store, chunked_text, model)
            answer = chatbot_answer(query, search_results, messages)
            messages.append({"role": "assistant", "content": answer})
        try:
            save_session(messages, 'chat_session.json')
        except Exception as e:
            log.error(f'Error saving the session: {e}')
    except Exception as e:
        log.error(f'Error: {e}')
        sys.exit(1)