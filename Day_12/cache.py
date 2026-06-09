import json
from pathlib import Path

CACHE_FILE = Path("cache_store.json")

def _load() -> dict:
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def _save(data: dict):
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get(query: str):
    key = query.lower().strip()
    cache = _load()
    return cache.get(key)  

def setting(query: str, response: str):
    key = query.lower().strip()
    cache = _load()
    cache[key] = response  
    _save(cache)           