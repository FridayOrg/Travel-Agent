import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import Orchestrator
from llm import send_with_retry


def main():
    orch = Orchestrator()
    ctx = orch.context

    # --- Stage 1: INTAKE (static, simulated as already answered) ---
    ctx.destination = "Dubai"
    ctx.profile["destination"] = "Dubai"
    ctx.profile["travellers_type"] = "Couple"
    ctx.profile["month"] = "Oct-Nov"
    ctx.profile["origin_location"] = "Mumbai, India"
    print(f"[stage: {ctx.stage}] intake complete\n")

    # --- Stage 2: DESTINATION_SPOTS ---
    reply = orch.enter_llm_stage("DESTINATION_SPOTS")
    print(f"AGENT: {reply}\n[stage: {ctx.stage}]\n" + "-" * 80)

    reply = orch.send("Yes")
    print(f"USER: Yes\nAGENT: {reply}\n[stage: {ctx.stage}]\n" + "-" * 80)

    # --- Static hotel intake (simulate answers) ---
    ctx.adults = 2
    ctx.kids = 0
    ctx.stage = "HOTEL_BUDGET"
    ctx.profile["budget_level"] = "Mid-range"
    ctx.stage = "HOTEL_DATES"
    ctx.checkin = "2026-10-10"
    ctx.checkout = "2026-10-15"
    print(f"[stage: {ctx.stage}] hotel intake complete (2 adults, mid-range, {ctx.checkin} to {ctx.checkout})\n")

    # --- Stage: HOTEL_SEARCH ---
    reply = orch.enter_llm_stage("HOTEL_SEARCH")
    print(f"AGENT: {reply}\n[stage: {ctx.stage}]\n" + "-" * 80)

    reply = orch.send("Let's go with your first recommendation.")
    print(f"USER: Let's go with your first recommendation.\nAGENT: {reply}\n[stage: {ctx.stage}]\n" + "-" * 80)

    if ctx.stage == "BOOKING":
        reply = orch.send("John Doe, john.doe@example.com, +91 9800000000")
        print(f"AGENT: {reply}\n[stage: {ctx.stage}]\n" + "-" * 80)

        reply = orch.send("Yes, please confirm the booking.")
        print(f"AGENT: {reply}\n[stage: {ctx.stage}]  [context: {ctx.summary()}]\n" + "-" * 80)


if __name__ == "__main__":
    main()
