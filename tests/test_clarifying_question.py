import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import Orchestrator


def main():
    orch = Orchestrator()
    reply1 = orch.send("I want a relaxing trip somewhere warm.")
    print(f"AGENT 1: {reply1}\n")
    reply2 = orch.send("Not sure yet, you tell me who you'd guess.")
    print(f"AGENT 2: {reply2}\n")


if __name__ == "__main__":
    main()
