from langchain.agents import AgentExecutor


def get_agent_executor(agent, tools):
    return AgentExecutor(agent=agent, tools=tools, verbose=True)
