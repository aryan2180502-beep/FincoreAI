from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from backend.graph.state import StateSchema
from backend.utils.prompt_loader import PromptLoader
from backend.utils.audit_logger import AuditLogger
import json
import uuid
import time

class Plan(BaseModel):
    agents_to_call: list[str] = Field(description="List of specialist agents to invoke: loan_agent, fraud_agent, account_agent, compliance_agent")
    rationale: str = Field(description="Reasoning for choosing these agents")
    parallel: bool = Field(description="Whether these agents can be called in parallel")
    done: bool = Field(description="Whether the task is complete")

class Planner:
    def __init__(self, prompt_loader: PromptLoader, model_name="gemini-2.0-flash"):
        self.loader = prompt_loader
        self.llm = ChatGoogleGenerativeAI(model=model_name).with_structured_output(Plan)
        self.audit_logger = AuditLogger()

    def run(self, state: StateSchema) -> Dict[str, Any]:
        start_time = time.time()
        execution_id = self.audit_logger.log_agent_start(
            state["turn_id"], 
            "planner", 
            state["iteration"], 
            {"iteration": state["iteration"]}
        )
        
        system_msg = self.loader.load("planner", "system", 
                                      query=state["query"], 
                                      intents=state["intent"], 
                                      outputs_so_far=json.dumps(state["agent_outputs"]),
                                      critiques=json.dumps(state["critique_verdicts"]),
                                      iteration=state["iteration"])
        
        user_msg = self.loader.load("planner", "user",
                                   query=state["query"],
                                   intents=state["intent"],
                                   outputs_so_far=json.dumps(state["agent_outputs"]),
                                   critiques=json.dumps(state["critique_verdicts"]),
                                   iteration=state["iteration"])
        
        plan = self.llm.invoke(user_msg)
        duration_ms = int((time.time() - start_time) * 1000)
        
        self.audit_logger.log_agent_end(execution_id, plan.dict(), None, duration_ms)
        
        return {"plan": plan.dict()}
