from agno.agent import Agent
print("Agent has team parameter?", "team" in Agent.__init__.__code__.co_varnames)
