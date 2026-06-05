#---------------- Loader -----------------
import logging
import sys
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader

log = logging.getLogger(__name__)

def load_document(file_path: str):
    extension = Path(file_path).suffix.lower()
    if extension == ".pdf":
        loader = PyPDFLoader(file_path)
    elif extension == ".docx":
        loader = Docx2txtLoader(file_path)
    elif extension == ".txt":
        loader = TextLoader(file_path)
    else:
        log.error(f'Unsupported file format {extension}. Use ".pdf" or ".docx" or ".txt".')
        sys.exit(1)
    return loader.load()