
COMPLEX_TRIGGERS = ["explain", "compare", "analyze", "analyse", "why", "how does", "difference between", "describe", "summarize"]

def classify(query: str) -> str:
    q = query.lower().strip()
    word_count = len(q.split())

    for trigger in COMPLEX_TRIGGERS:
        if trigger in q:
            return "complex"

    if word_count < 8:
        return "simple"

    return "complex"

def get_model(complexity: str) -> str:
    if complexity == "simple":
        return "llama-3.1-8b-instant"   
    return "llama-3.3-70b-versatile"    