import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import Orchestrator


def main():
    orch = Orchestrator()
    reply = orch.send("When is Vinayaka Chaturthi this year?")
    print(f"AGENT: {reply}\n")


if __name__ == "__main__":
    main()
