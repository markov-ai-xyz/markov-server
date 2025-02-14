import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain import hub
from langchain.agents import create_openai_functions_agent

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def get_openai_functions_agent(tools, hub_link):
    prompt = hub.pull(hub_link)
    llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-3.5-turbo", temperature=0)
    agent = create_openai_functions_agent(llm, tools, prompt)
    return agent
