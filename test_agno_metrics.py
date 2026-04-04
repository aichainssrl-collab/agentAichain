from agno.agent import Agent
from agno.models.openai import OpenAIChat
agent = Agent(model=OpenAIChat())
r = agent.run("hi")
print(type(r.metrics))
print(dir(r.metrics))
