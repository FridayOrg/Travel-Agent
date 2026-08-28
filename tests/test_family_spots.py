import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from orchestrator import Orchestrator

orch = Orchestrator()
ctx = orch.context
ctx.destination = "Dubai"
ctx.profile["destination"] = "Dubai"
ctx.profile["travellers_type"] = "Family"
ctx.profile["month"] = "Oct-Nov"

reply = orch.enter_llm_stage("DESTINATION_SPOTS")
print(f"AGENT: {reply}\n[stage: {ctx.stage}]")
