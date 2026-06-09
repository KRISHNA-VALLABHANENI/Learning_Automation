import json
import time
from datetime import datetime
from pathlib import Path

from groq import Groq
from dotenv import load_dotenv

import cache
import router
import compressor

load_dotenv()

LOG_FILE = Path("optimizer_log.json")
client = Groq()  

total_queries = 0
cache_hits = 0
model_usage = {}  

def log_entry(entry: dict):
    if LOG_FILE.exists():
        with open(LOG_FILE, "r") as f:
            logs = json.load(f)
    else:
        logs = []

    logs.append(entry)

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)

def print_stats():
    print("\n" + "="*40)
    print("SESSION STATS")
    print("="*40)
    print(f"Total queries    : {total_queries}")
    print(f"Cache hits       : {cache_hits}")
    print(f"API calls made   : {total_queries - cache_hits}")
    print("Model usage:")
    for model, count in model_usage.items():
        print(f"  {model}: {count} call(s)")
    print("="*40)

def run():
    global total_queries, cache_hits

    print("Cost Optimizer CLI")
    print("Type your query. Type 'quit' to exit.\n")

    while True:
        query = input("You: ").strip()

        if not query:
            continue

        if query.lower() == "quit":
            print_stats()
            break

        total_queries += 1

        complexity = router.classify(query)
        model = router.get_model(complexity)

        # Step 1: Cache Check 
        cached_response = cache.get(query)
        if cached_response:
            cache_hits += 1
            print(f"\nAssistant: {cached_response}")
            print("[CACHE HIT]\n")

            # Log the cache hit — no model or time info needed.
            log_entry({
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "query": query,
                "cache_hit": True,
                "model_used": None,
                "complexity": None,
                "prompt_compressed": False,
                "response_time_ms": 0
            })
            continue

        # Step 2: Classify + Route 


        # Track model usage for session stats.
        model_usage[model] = model_usage.get(model, 0) + 1

        # Step 3: Compress if Needed 
        original_length = len(query)
        compressed_prompt = compressor.compress(query)
        was_compressed = len(compressed_prompt) != original_length

        # Step 4: Call Groq API 
        start = time.time()

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": compressed_prompt}],
            stream = True
        )      

        answer = ""
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                print(content, end="", flush=True)
                answer += content
        end = time.time()
        response_time_ms = round((end - start) * 1000)
        print()
        # Step 5: Cache the Response
        cache.setting(query, answer)

        # Step 6: Log the Decision 
        log_entry({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "query": query,
            "cache_hit": False,
            "model_used": model,
            "complexity": complexity,
            "prompt_compressed": was_compressed,
            "response_time_ms": response_time_ms
        })

        # Print Result 
        print(f"[Model: {model} | Complexity: {complexity} | Time: {response_time_ms}ms | Compressed: {was_compressed}]\n")

if __name__ == "__main__":
    run()