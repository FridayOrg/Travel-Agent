import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import Orchestrator

SCRIPT = [
    "I want to travel for 5 days in September. I want somewhere relaxing, good food, "
    "some nightlife, not too expensive, and suitable for a couple.",
    "We're travelling from Mumbai, India, open to a different country, up to about a 6 hour flight. "
    "Mid-range budget, nothing too fancy. We loved Lisbon last year, found Dubai too flashy for us.",
    "Let's go with your first pick.",
    "What neighbourhood should we stay in?",
    "Let's skip the detailed itinerary for now, just show me hotels.",
    "September 10th to 15th, 2 adults, staying in Ruzafa if possible.",
    "Let's go with your first recommendation.",
    "John Doe, john.doe@example.com, +91 9800000000",
    "Yes, please confirm the booking.",
]


def main():
    orch = Orchestrator()
    print(f"[stage: {orch.context.stage}]\n")
    for turn in SCRIPT:
        print(f"USER: {turn}\n")
        reply = orch.send(turn)
        print(f"AGENT: {reply}\n")
        print(f"[stage: {orch.context.stage}]  [context: {orch.context.summary()}]\n")
        print("-" * 80)


if __name__ == "__main__":
    main()
