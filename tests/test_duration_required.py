import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import Orchestrator

SCRIPT = [
    "I need to travel with my friends, uh, for September second week",
    "Somewhere else",
    "Bangalore",
    "Different state or country",
]


def main():
    orch = Orchestrator()
    for turn in SCRIPT:
        print(f"USER: {turn}\n")
        reply = orch.send(turn)
        print(f"AGENT: {reply}\n")
        if orch.context.profile:
            print(f"[profile: {orch.context.profile}]")
        print("-" * 80)


if __name__ == "__main__":
    main()
