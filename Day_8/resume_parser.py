import os 
import sys
import json
import re
import logging
from dotenv import load_dotenv
from groq import Groq
from typing import Optional, List, Any
from pydantic import BaseModel

load_dotenv()

logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - %(levelname)s - %(message)s',
    handlers = [logging.FileHandler('parser.log'),
                logging.StreamHandler()]
)
log = logging.getLogger(__name__)

client = Groq(api_key=os.getenv('GROQ_API_KEY'))

MODEL= 'llama-3.3-70b-versatile'

class ResumeData (BaseModel):
    name : str
    phone: str
    email: str
    skills: list[Any]
    experience: list[Any]
    education: list[Any]
    achievements: Optional[str] = None
    summary: Optional[str] = None

# ----------- Building Prompt ------------
def build_prompt(resume_text: str) -> str: 
    prompt = f"""
        You are an expert resume parser. Extract all relevant information from the resume text below.

        Return ONLY a valid JSON object — no explanation, no markdown, no code fences.
        If a field is missing, set it to null or an empty list.

        Target JSON structure:
        {{
        "name": "string",
        "email": "string",
        "phone": "string",
        "location": "string",
        "summary": "string",
        "skills": ["list"],
        "education": [
            {{
            "institution": "string",
            "field_of_study": "string",
            "year": "string",
            "score": "string"
            }}
        ],
        "experience": [
            {{
            "role": "string or null",
            "company": "string or null",
            "duration": "string or null",
            "description": "string or null"
            }}
        ],
        "links": {{
            "linkedin": "string or null",
            "github": "string or null",
            "portfolio": "string or null"
        }}
        }}

        Resume:
        {resume_text}
        """
    return prompt

# ---------- Calling LLM ------------
def parse_resume(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model = MODEL,
            messages = [{"role": "user", "content": prompt}],
            max_tokens = 1024,
        )
        log.info('Parsing the resume...')
        return response.choices[0].message.content
    except Exception as e:
        log.error(f'Error with Groq: {e}')
        print(f"Save failed: {e}")

def extract_json(raw_response):
    try:
        return json.loads(raw_response.strip())
    except json.JSONDecodeError as e:
        log.error(f'Error parsing the raw response: {e}')

def validate_resume(parsed_resume):
    try:
        validated = ResumeData(**parsed_resume)
        log.info('Validation Passed')
        return validated
    except Exception as e:
        log.error(f'Error validating the resume: {e}')


def save_data(parsed_resume):
    try:
        with open('parsed_resume.json', "w") as f:
            json.dump({'resume': parsed_resume},f,indent=2)
        print("File saved successfully")  # add this
        log.info("Resume saved to parsed_resume.json")
    except Exception as e:
        log.error(f'Error saving the file: {e}')

def display_data(parsed_resume):
    Name = parsed_resume['name']
    Email = parsed_resume['email']
    contact_no = parsed_resume['phone']

    print('-'*50)

    print(f'Name: {Name}\nEmail: {Email}\nContact no.: {contact_no}\n')
    print('\nEducation:')
    for edu in parsed_resume['education']:
        print(f"Institution: {edu['institution']}, Field of Study: {edu['field_of_study']}, Year: {edu['year']}")
    print('\nExperience: ')
    for exp in parsed_resume['experience']:
        try:
            print(f"Company: {exp['company']},\nRole: {exp['role']},\nDuration: {exp['duration']}\n\n")
        except Exception as e:
            log.error(f'Error in displaying experience: {e}')
    print('-'*50)

SAMPLE_RESUME = """
John Smith
Email: john.smith@email.com | Phone: +1-555-0123

SUMMARY
Experienced Python developer with 5 years building automation tools and APIs.

SKILLS
Python, FastAPI, PostgreSQL, Docker, AWS, REST APIs, Git

EXPERIENCE
Senior Python Developer — TechCorp (2021-Present)
- Built automation pipeline reducing manual work by 60%
- Designed REST APIs serving 10k daily requests

Python Developer — StartupXYZ (2019-2021)  
- Developed web scraping tools for market research
- Maintained CI/CD pipelines using GitHub Actions

EDUCATION
B.Tech Computer Science — JNTU Hyderabad (2019)

"""

if __name__ == '__main__':
    prompt = build_prompt(SAMPLE_RESUME)
    raw_response = parse_resume(prompt)
    parsed_resume = extract_json(raw_response)
    validate_resume(parsed_resume)
    save_data(parsed_resume)
    display_data(parsed_resume)
