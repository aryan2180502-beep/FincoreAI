from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.graph.state import StateSchema
from backend.utils.prompt_loader import PromptLoader
from backend.utils.audit_logger import AuditLogger
import json
import uuid
import time

class Aggregator:
    def __init__(self, prompt_loader: PromptLoader, model_name="gemini-2.0-flash"):
        self.loader = prompt_loader
        self.llm = ChatGoogleGenerativeAI(model=model_name)
        self.audit_logger = AuditLogger()

    def run(self, state: StateSchema) -> Dict[str, Any]:
        start_time = time.time()
        execution_id = self.audit_logger.log_agent_start(
            state["turn_id"], 
            "aggregator", 
            state["iteration"], 
            {"query": state["query"]}
        )
        
        system_msg = self.loader.load("aggregator", "system",
                                      query=state["query"],
                                      agent_outputs=json.dumps(state["agent_outputs"]))
        
        response = self.llm.invoke(system_msg)
        duration_ms = int((time.time() - start_time) * 1000)
        
        self.audit_logger.log_agent_end(execution_id, response.content, None, duration_ms)
        
        return {"final_response": response.content}
