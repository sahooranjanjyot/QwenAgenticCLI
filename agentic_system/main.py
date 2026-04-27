import sys
import os
from qwen_agent import run_agent

ALLOW_INTERACTIVE = False

if __name__ == "__main__":
    if not ALLOW_INTERACTIVE:
        if len(sys.argv) > 1:
            raise Exception("❌ Interactive execution disabled")

    if not os.path.exists("goal.txt"):
        raise Exception("❌ Direct execution disabled. Use Qwen agent loop.")

    goal = open("goal.txt").read()
    run_agent(goal)
