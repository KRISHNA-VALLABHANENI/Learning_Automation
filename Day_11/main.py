from pathlib import Path
from langchain.tools import tool
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS    
from agent import build_agent
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from tools import calculator, get_datetime

MODEL = "llama-3.3-70b-versatile"

def load_document(file_path):
    extension = Path(file_path).suffix
    if extension == '.pdf':
        loader = PyPDFLoader(file_path)
    elif extension == '.docx':
        loader = Docx2txtLoader(file_path)
    elif extension == '.txt':
        loader = TextLoader(file_path)
    else:

        return loader
    try:
        document = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size = 500,
            chunk_overlap = 50
        )
        chunks = splitter.split_documents(document)
        embeddings = HuggingFaceEmbeddings(
            model_name = "sentence-transformers/all-MiniLM-L6-v2"
        )
        vector_store = FAISS.from_documents(
            chunks,
            embeddings
        )
        retriever = vector_store.as_retriever(
            search_type = 'similarity',
            search_kwargs = {'k': 5}
        )
    except Exception as e:
        return f'Error occured: {e}'
    return retriever





if __name__ == '__main__':

    file_path = input('Enter the file path: ').strip().strip('"')
    retriever = load_document(file_path)

    @tool
    def extract_document(query: str) -> str:
        '''
        extracts and searches a document.
        use when user asks to search a topic or serach the document or when needed.
        return the extracted text's summary.
        '''
        docs = retriever.invoke(query)
        return "\n".join([doc.page_content for doc in docs])
    
    
    tools = [calculator, get_datetime, extract_document]
    agent = build_agent(tools)

    while True:
        query = input('Enter the query: ')
        if query.lower() == 'quit':
            break
        response = agent.invoke({'input': query})
        print(response['output'])
