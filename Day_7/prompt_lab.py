import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

# --- Setup ---
load_dotenv()

client = Groq(api_key=os.getenv('GROQ_API_KEY'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('prompt_lab.log')]
)
log = logging.getLogger(__name__)

MODEL      = 'llama-3.3-70b-versatile'
TEST_INPUT = """
Meeting transcript:
John: We need to finish the API integration by Friday.
Sarah: I'll handle the database migration tomorrow.
John: Can you also review the security audit report?
Sarah: Sure. Also, we need to send the client update by EOD today.
John: Right, and someone needs to schedule the team retrospective.
"""


# --- Prompt Variants ---
# Each variant is a different prompting strategy for the same task
PROMPTS = {
    'zero_shot': """ Extract all action items from this meeting transcript. {input} """,

    'role_prompt': """ You are a professional project manager known for precise, structured meeting summaries. Extract all action items
                        from this transcript. {input} """,

    'few_shot': """ Extract action items from meeting transcripts.
                    Example transcript:
                    "Mike: Send the report by Tuesday. Lisa: I'll update the docs."
                    Example output:
                    - Mike: Send report (Due: Tuesday)
                    - Lisa: Update documentation

                    Now extract from this transcript: {input} """,

    'chain_of_thought': """ Extract all action items from this meeting transcript. 
                            Think step by step:
                            1. First identify who is speaking
                            2. Then identify what each person committed to do
                            3. Then check if any deadlines were mentioned
                            4. Finally format as a clean action item list
                            {input} """,

    'output_constrained': """ Extract action items from this meeting transcript.
                                Return ONLY a JSON array. No explanation. No markdown fences.
                                Each item must have: owner, task, deadline (or "not specified").

                                Example format:
                                [{{"owner": "John", "task": "Send report", "deadline": "Tuesday"}}]

                                {input} """,
    'hybrid': """ You are a professional project manager with 10 years of experience running agile teams. You never miss action items     and always assign clear ownership.

                    Extract all action items from this transcript.
                    Return ONLY a JSON array. No explanation. No markdown.
                    Each item must have: owner, task, deadline (null if not specified).

                    Example:
                    [{{"owner": "Sarah", "task": "Update docs", "deadline": null}}]

                    {input}
"""
}


def run_prompt(prompt_name: str, prompt_template: str, input_text: str) -> dict:
    """
    Run a single prompt variant and return results with metadata.
    """
    prompt = prompt_template.format(input=input_text)

    start_time = time.time()

    try:
        response = client.chat.completions.create(
            model    = MODEL,
            messages = [{"role": "user", "content": prompt}],
            max_tokens = 512
        )

        elapsed       = time.time() - start_time
        output        = response.choices[0].message.content
        input_tokens  = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens

        log.info(f"Ran '{prompt_name}' | {input_tokens}+{output_tokens} tokens | {elapsed:.2f}s")

        return {
            'prompt_name'  : prompt_name,
            'output'       : output,
            'input_tokens' : input_tokens,
            'output_tokens': output_tokens,
            'elapsed_sec'  : round(elapsed, 2),
            'success'      : True
        }

    except Exception as e:
        log.error(f"Failed '{prompt_name}': {e}")
        return {
            'prompt_name': prompt_name,
            'output'     : str(e),
            'success'    : False
        }


def score_output(result: dict) -> dict:
    """
    Score each output on 3 criteria (1-5 scale each):
    - Completeness: did it find all action items?
    - Structure: is the output organized and readable?
    - Parseable: could a script extract data from this output?
    """
    output = result.get('output', '')

    # Completeness — check if all 5 action items are mentioned
    keywords   = ['api', 'database', 'security', 'client', 'retrospective']
    found      = sum(1 for k in keywords if k.lower() in output.lower())
    completeness = round((found / len(keywords)) * 5)

    # Structure — check for formatting markers
    has_bullets  = '-' in output or '•' in output or '*' in output
    has_numbers  = any(f"{i}." in output for i in range(1, 6))
    has_newlines = output.count('\n') > 2
    structure    = min(5, (has_bullets + has_numbers + has_newlines) * 2)

    # Parseable — check if output is structured data
    is_json = False
    try:
        json.loads(output.strip())
        is_json = True
    except Exception:
        pass

    parseable = 5 if is_json else (3 if has_bullets else 1)

    total = completeness + structure + parseable

    return {
        **result,
        'scores': {
            'completeness': completeness,
            'structure'   : structure,
            'parseable'   : parseable,
            'total'       : total
        }
    }


def display_results(results: list) -> None:
    """Print formatted comparison table of all prompt variants."""
    print("\n" + "="*65)
    print(f"  PROMPT TESTING LAB RESULTS")
    print(f"  Task: Extract action items from meeting transcript")
    print("="*65)

    # Sort by total score descending
    sorted_results = sorted(
        results,
        key=lambda x: x['scores']['total'],
        reverse=True
    )

    for i, r in enumerate(sorted_results, 1):
        scores = r['scores']
        print(f"\n#{i} — {r['prompt_name'].upper()}")
        print(f"  Total Score    : {scores['total']}/15")
        print(f"  Completeness   : {scores['completeness']}/5")
        print(f"  Structure      : {scores['structure']}/5")
        print(f"  Parseable      : {scores['parseable']}/5")
        print(f"  Tokens used    : {r.get('input_tokens',0)} in / {r.get('output_tokens',0)} out")
        print(f"  Response time  : {r.get('elapsed_sec', 0)}s")
        print(f"  Output preview : {r['output'][:100].strip()}...")

    print("\n" + "="*65)
    print(f"  WINNER: {sorted_results[0]['prompt_name'].upper()}")
    print("="*65 + "\n")


def save_results(results: list) -> None:
    """Save full results to JSON for analysis."""
    filename = f"prompt_results_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Full results saved to {filename}")


if __name__ == '__main__':
    print("\nPrompt Testing Lab")
    print(f"Testing {len(PROMPTS)} prompt variants...\n")

    results = []

    for name, template in PROMPTS.items():
        print(f"Running: {name}...")
        result  = run_prompt(name, template, TEST_INPUT)
        scored  = score_output(result)
        results.append(scored)
        time.sleep(1)  # avoid rate limiting

    display_results(results)
    save_results(results)