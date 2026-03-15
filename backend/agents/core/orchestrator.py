from typing import Dict, Any, Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.graph.state import StateSchema
from backend.utils.prompt_loader import PromptLoader
from backend.utils.audit_logger import AuditLogger
import json
import time
import uuid

class Orchestrator:
    def __init__(self, prompt_loader: PromptLoader, model_name="gemini-2.0-flash"):
        self.loader = prompt_loader
        self.llm = ChatGoogleGenerativeAI(model=model_name)
        self.max_iterations = 3
        self.audit_logger = AuditLogger()

    def run(self, state: StateSchema) -> Dict[str, Any]:
        start_time = time.time()
        iteration = state.get("iteration", 0)
        
        execution_id = self.audit_logger.log_agent_start(
            state["turn_id"], 
            "orchestrator", 
            iteration, 
            {"iteration": iteration, "verdicts": state["critique_verdicts"]}
        )

        if iteration >= self.max_iterations:
             self.audit_logger.log_agent_end(execution_id, "Max iterations reached", None, int((time.time()-start_time)*1000))
             return {"iteration": iteration, "scratchpad": "Max iterations reached. Exiting."}
        
        if state.get("requires_human"):
            self.audit_logger.log_agent_end(execution_id, "Human escalation triggered", None, int((time.time()-start_time)*1000))
            return {"scratchpad": "Human escalation triggered. Exiting loop."}

        # Simplified decision
        duration_ms = int((time.time() - start_time) * 1000)
        self.audit_logger.log_agent_end(execution_id, "Continuing loop", None, duration_ms)

        return {"iteration": iteration + 1}

    def decide_next_node(self, state: StateSchema) -> Literal["planner", "aggregator"]:
        if state.get("iteration", 0) >= self.max_iterations or state.get("requires_human") or state.get("plan", {}).get("done"):
            return "aggregator"
        
        if all(v == "PASS" for v in state["critique_verdicts"].values()) and len(state["agent_outputs"]) >= len(state["intent"]) and len(state["intent"]) > 0:
             return "aggregator"

        return "planner"
