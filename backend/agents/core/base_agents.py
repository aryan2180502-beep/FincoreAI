from typing import Dict, Any, List
from langchain_google_genai import ChatGeminiAI
from backend.graph.state import StateSchema
from backend.utils.prompt_loader import PromptLoader
from backend.mcp.mock_mcp import MockMCP
from backend.db.mock_neo4j import MockNeo4j
from backend.utils.audit_logger import AuditLogger
import json
import uuid
import time

class SpecialistAgent:
    def __init__(self, name: str, prompt_loader: PromptLoader, model_name="gemini-1.5-flash"):
        self.name = name
        self.loader = prompt_loader
        self.llm = ChatGeminiAI(model=model_name)
        self.audit_logger = AuditLogger()
        self.neo4j = MockNeo4j(self.audit_logger)

    def run(self, state: StateSchema) -> Dict[str, Any]:
        start_time = time.time()
        execution_id = self.audit_logger.log_agent_start(
            state["turn_id"], 
            f"{self.name}_agent", 
            state["iteration"], 
            {"sub_question": state.get("plan", {}).get("rationale", "")}
        )

        customer_id = state["customer_id"]
        mcp_output = {}
        kg_output = [] 
        
        # Specialist Logic with MCP Tools and KG Queries
        mcp_start = time.time()
        if self.name == "account":
            # Account Balance & Lookup (Q1, Q4)
            mcp_output = MockMCP.get_account_summary(customer_id)
            self.audit_logger.log_mcp_call(execution_id, "core_banking_mcp", "get_account_summary", {"cid": customer_id}, mcp_output, int((time.time()-mcp_start)*1000))
            kg_output = self.neo4j.execute_query(execution_id, "Q1", {"cid": customer_id})
            kg_output += self.neo4j.execute_query(execution_id, "Q4", {"cid": customer_id})

        elif self.name == "loan":
            # Loan Eligibility & Active Loans (Q2)
            mcp_output = {
                "score": MockMCP.get_credit_score(customer_id),
                "loans": MockMCP.get_emi_schedule(customer_id)
            }
            self.audit_logger.log_mcp_call(execution_id, "credit_mcp", "get_credit_info", {"cid": customer_id}, mcp_output, int((time.time()-mcp_start)*1000))
            kg_output = self.neo4j.execute_query(execution_id, "Q2", {"cid": customer_id})

        elif self.name == "fraud":
            # Fraud Score & Ring Detection (Q5)
            mcp_output = {"risk": MockMCP.score_transaction_risk("TXN999")}
            self.audit_logger.log_mcp_call(execution_id, "fraud_mcp", "score_transaction_risk", {"txid": "TXN999"}, mcp_output, int((time.time()-mcp_start)*1000))
            kg_output = self.neo4j.execute_query(execution_id, "Q5", {"cid": customer_id})

        elif self.name == "compliance":
            # Regulation Rules (Q3)
            mcp_output = MockMCP.get_regulation_rules()
            self.audit_logger.log_mcp_call(execution_id, "compliance_mcp", "get_regulation_rules", {}, mcp_output, int((time.time()-mcp_start)*1000))
            kg_output = self.neo4j.execute_query(execution_id, "Q3", {"ltype": "Home Loan"})

        retry_instruction = state.get("critique_verdicts", {}).get(f"{self.name}_retry", "")
        sub_question = state.get("plan", {}).get("rationale", "")

        user_msg = self.loader.load(f"agents/{self.name}", "user",
                                   customer_id=customer_id,
                                   sub_question=sub_question,
                                   mcp_output=json.dumps(mcp_output),
                                   kg_output=json.dumps(kg_output),
                                   retry_instruction=retry_instruction)

        response = self.llm.invoke(user_msg)
        duration_ms = int((time.time() - start_time) * 1000)
        
        self.audit_logger.log_agent_end(execution_id, response.content, None, duration_ms)
        
        agent_outputs = state["agent_outputs"].copy()
        agent_outputs[self.name] = response.content
        
        return {"agent_outputs": agent_outputs, 
                "mcp_calls_log": state["mcp_calls_log"] + [{"agent": self.name, "output": mcp_output, "execution_id": execution_id}]}

class CritiqueAgent:
    def __init__(self, name: str, prompt_loader: PromptLoader, model_name="gemini-1.5-flash"):
        self.name = name
        self.loader = prompt_loader
        self.llm = ChatGeminiAI(model=model_name)
        self.audit_logger = AuditLogger()

    def run(self, state: StateSchema) -> Dict[str, Any]:
        start_time = time.time()
        agent_name = self.name.replace("_critique", "")
        agent_output = state["agent_outputs"].get(agent_name, "")
        
        execution_id = self.audit_logger.log_agent_start(
            state["turn_id"], 
            self.name, 
            state["iteration"], 
            {"agent_output": agent_output}
        )

        mcp_data = next((item["output"] for item in state["mcp_calls_log"] if item["agent"] == agent_name), {})
        kg_data = [] # Critique could also check KG data if needed

        sub_question = state.get("plan", {}).get("rationale", "")

        user_msg = self.loader.load(f"critiques/{self.name}", "user",
                                   sub_question=sub_question,
                                   agent_output=agent_output,
                                   mcp_data_used=json.dumps(mcp_data),
                                   kg_data_used=json.dumps(kg_data))

        response = self.llm.invoke(user_msg)
        duration_ms = int((time.time() - start_time) * 1000)

        try:
            content = response.content.replace("```json", "").replace("```", "").strip()
            verdict = json.loads(content)
        except:
            verdict = {"verdict": "RETRY", "issues": ["Invalid JSON response from critique agent"], "confidence": 0, "retry_instruction": "Please re-read the data and output valid JSON."}

        self.audit_logger.log_agent_end(execution_id, verdict, verdict.get("verdict"), duration_ms)

        new_verdicts = state["critique_verdicts"].copy()
        new_verdicts[agent_name] = verdict["verdict"]
        
        if verdict["verdict"] == "RETRY":
            new_verdicts[f"{agent_name}_retry"] = verdict.get("retry_instruction", "Review the checklist and try again.")
        
        requires_human = state["requires_human"]
        if verdict["verdict"] == "ESCALATE":
            requires_human = True

        return {"critique_verdicts": new_verdicts, "requires_human": requires_human}
