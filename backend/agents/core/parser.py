import uuid
import time
from typing import Dict, Any
from langchain_google_genai import ChatGeminiAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from backend.graph.state import StateSchema
from backend.utils.audit_logger import AuditLogger

class ParsedQuery(BaseModel):
    intent: list[str] = Field(description="A list of banking intents (loan_eligibility, fraud_check, account_info, compliance_query)")
    customer_id: str = Field(description="The customer ID if mentioned, otherwise 'UNKNOWN'")
    entities: list[str] = Field(description="Entities like account numbers, dates, or amounts mentioned")

class QueryParser:
    def __init__(self, model_name="gemini-1.5-flash"):
        self.llm = ChatGeminiAI(model=model_name).with_structured_output(ParsedQuery)
        self.audit_logger = AuditLogger()

    def parse(self, state: StateSchema) -> Dict[str, Any]:
        start_time = time.time()
        execution_id = self.audit_logger.log_agent_start(
            state["turn_id"], 
            "query_parser", 
            0, 
            {"query": state["query"]}
        )
        
        prompt = ChatPromptTemplate.from_template(
            "Extract the banking intents, customer ID, and entities from the following user query: {query}"
        )
        chain = prompt | self.llm
        result = chain.invoke({"query": state["query"]})
        
        duration_ms = int((time.time() - start_time) * 1000)
        self.audit_logger.log_agent_end(execution_id, result.dict(), None, duration_ms)
        
        return {
            "intent": result.intent,
            "customer_id": result.customer_id,
            "iteration": 0,
            "agent_outputs": {},
            "critique_verdicts": {},
            "mcp_calls_log": [],
            "kg_queries_log": [],
            "requires_human": False,
            "scratchpad": ""
        }
