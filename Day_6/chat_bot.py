import os
import json
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

# --- Setup ---
load_dotenv('.env')

API_KEY = os.getenv('GROQ_API_KEY')
if not API_KEY:
    print("Error: GROQ_API_KEY missing from .env")
    exit(1)

client = Groq(api_key=API_KEY)

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('chatbot.log')]
)
log = logging.getLogger(__name__)

# --- Config ---
MODEL_NAME = 'llama-3.3-70b-versatile'
SYSTEM     = """You are a sharp AI automation assistant.
Help developers build Python automation scripts and work with APIs.
Be concise and always include code examples when relevant."""


def save_session(messages: list, session_file: str) -> None:
    conversation = [m for m in messages if m['role'] != 'system']
    
    if not conversation:
        print("Nothing to save — no conversation yet.")
        return

    with open(session_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'model'    : MODEL_NAME,
            'messages' : messages
        }, f, indent=2)
    log.info(f"Session saved to {session_file}")
    print(f"Session saved to {session_file}")


def load_session(session_file: str) -> list:
    """Load previous conversation from JSON file."""
    path = Path(session_file)
    if not path.exists():
        print("No previous session found.")
        return []
    with open(session_file, 'r') as f:
        data = json.load(f)
    print(f"Loaded {len(data['messages'])} messages.")
    return data['messages']


def main():
    print("\n" + "="*50)
    print("  AI Automation Assistant — Groq/LLaMA")
    print("  'quit' — exit | 'save' — save session")
    print("  'clear' — reset | 'load' — load session")
    print("="*50 + "\n")

    session_file = f"session_{datetime.now().strftime('%Y%m%d')}.json"

    # System message is always first in history
    messages = [
        {"role": "system", "content": SYSTEM}
    ]

    while True:
        try:
            user_input = input("You: ").strip()
        except KeyboardInterrupt:
            print("\nExiting...")
            save_session(messages, session_file)
            break

        if not user_input:
            continue

        if user_input.lower() == 'quit':
            save_session(messages, session_file)
            print("Goodbye.")
            break

        if user_input.lower() == 'clear':
            messages = [{"role": "system", "content": SYSTEM}]
            print("Conversation cleared.\n")
            continue

        if user_input.lower() == 'save':
            save_session(messages, session_file)
            continue

        if user_input.lower() == 'load':
            messages = load_session(session_file)
            continue

        # Add user message to history
        messages.append({"role": "user", "content": user_input})

        print("\nAssistant: ", end='', flush=True)

        try:
            stream = client.chat.completions.create(
                model    = MODEL_NAME,
                messages = messages,
                stream   = True,
                max_tokens = 1024
            )

            full_response = ""
            input_tokens  = 0
            output_tokens = 0

            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    print(delta.content, end='', flush=True)
                    full_response += delta.content

                # Capture token usage from last chunk
                if chunk.x_groq and chunk.x_groq.usage:
                    input_tokens  = chunk.x_groq.usage.prompt_tokens
                    output_tokens = chunk.x_groq.usage.completion_tokens

            print(f"\n[Input: {input_tokens} | Output: {output_tokens} tokens]\n")

            # Add assistant response to history
            messages.append({"role": "assistant", "content": full_response})

            log.info(f"User: {user_input[:50]} | Tokens in: {input_tokens} out: {output_tokens}")

        except Exception as e:
            print(f"\nError: {e}\n")
            messages.pop()


if __name__ == '__main__':
    main()