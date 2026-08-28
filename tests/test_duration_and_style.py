import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import Orchestrator


def main():
    orch = Orchestrator()
    ctx = orch.context

    ctx.destination = "Dubai"
    ctx.profile["destination"] = "Dubai"
    ctx.profile["travellers_type"] = "Couple"
    ctx.profile["month"] = "Oct-Nov"

    reply = orch.enter_llm_stage("DESTINATION_SPOTS")
    print(f"AGENT: {reply}\n[stage: {ctx.stage}]\n" + "-" * 80)

    reply = orch.send("I like these, looks great.")
    print(f"USER: I like these, looks great.\nAGENT: {reply}\n[stage: {ctx.stage}]\n" + "-" * 80)

    reply = orch.send("4-6 days")
    print(f"USER: 4-6 days\nAGENT: {reply}\n[stage: {ctx.stage}] duration_days={ctx.trip_duration_days}\n" + "-" * 80)

    reply = orch.send("Yes")
    print(f"USER: Yes\nAGENT: {reply}\n[stage: {ctx.stage}]\n" + "-" * 80)

    assert ctx.stage == "HOTEL_TRAVELLERS", f"expected HOTEL_TRAVELLERS, got {ctx.stage}"
    assert ctx.trip_duration_days, "trip_duration_days was never set"

    ctx.adults = 2
    ctx.kids = 0
    ctx.stage = "HOTEL_BUDGET"
    ctx.profile["budget_level"] = "Mid-range"
    ctx.stage = "HOTEL_DATES"
    ctx.checkin = "2026-10-10"
    ctx.checkout = "2026-10-15"

    reply = orch.enter_llm_stage("HOTEL_SEARCH")
    print(f"AGENT: {reply}\n[stage: {ctx.stage}]\n" + "-" * 80)

    print("\nALL CHECKS PASSED")


if __name__ == "__main__":
    main()
