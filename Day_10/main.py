import sys
import logging
from pathlib import Path
from loader import load_document
from chain import build_chain


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chain.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


def main():

    file_path = input('Enter the file path (.pdf/.docx/.txt): ').strip('"')
    if not Path(file_path).exists():
        log.error(f'File not found: {file_path}')
        sys.exit(1)

    try:
        documents = load_document(file_path)
        chain = build_chain(documents)
    except Exception as e:
        log.error(f'Initialization failed: {e}')
        sys.exit(1)
    print('\n----------- LangChain RAG Chatbot -----------')
    print('Type "quit" to exit the chat.\n')

    while True:

        query = input("Ask: ")
        if query.lower() == "quit":
            print("Goodbye!")
            log.info("Chat session ended by user.")
            break
        try:
            response = chain.invoke({"question": query})
            print(f"\nAnswer: {response['answer']}\n")
        except Exception as e:
            log.error(f"Query failed: {e}")

if __name__ == "__main__":
    main()