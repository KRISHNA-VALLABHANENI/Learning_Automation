import os
from dotenv import load_dotenv
from langchain import hub
from langchain_groq import ChatGroq
from langchain.agents import create_react_agent, AgentExecutor

MODEL = "llama-3.3-70b-versatile"
load_dotenv()

def build_agent(tools):
    llm = ChatGroq(
        api_key = os.getenv('GROQ_API_KEY'),
        model = MODEL,
        temperature = 0  
    )
    prompt = hub.pull("hwchase17/react")
    agent = create_react_agent(llm, tools, prompt)
    return AgentExecutor(
        agent = agent,
        tools = tools,
        verbose = True,
        handle_parsing_errors = True,
        max_iterations = 4
    )

