import json
from qwen_agent import QwenAgent
from agent_memory import AgentMemory

agent = QwenAgent()
memory = AgentMemory()

with open("goal.txt", "r") as f:
    goal = f.read().strip()

print("Fetching from Qwen...")
action = agent.next_action(goal, memory.get_all(), None)
print(f"Action parsed: {action}")
