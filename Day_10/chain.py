import os
import logging
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()
log = logging.getLogger(__name__)
MODEL = "llama-3.3-70b-versatile"

def build_chain(documents):

    # ---------------- Splitter ----------------

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = splitter.split_documents(
        documents
    )

    # ---------------- Embeddings ----------------

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # ---------------- Vector Store ----------------

    vector_store = FAISS.from_documents(
        chunks,
        embeddings
    )

    # ---------------- Retriever ----------------

    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5}
    )

    # ---------------- Memory ----------------

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )

    # ---------------- LLM ----------------

    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model=MODEL,
        temperature = 0
    )

    # ---------------- Chain ----------------

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory
    )

    return chain