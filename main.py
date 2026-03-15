from dotenv import load_dotenv
import os
from backend.graph.graph import create_graph
import uuid
from backend.utils.audit_logger import AuditLogger
from langchain_core.callbacks import tracing_v2_enabled

# Load environment variables
load_dotenv()

def run_assistant(query: str, customer_id: str = "CUST-0042", scenario: str = "general"):
    app = create_graph()
    audit_logger = AuditLogger()
    
    convo_id = str(uuid.uuid4())
    turn_id = str(uuid.uuid4())
    audit_trace_id = str(uuid.uuid4())
    
    # Initialize Audit DB for this session
    audit_logger.create_conversation(convo_id, customer_id)
    audit_logger.create_turn(turn_id, convo_id, query)
    
    # Initial state
    initial_state = {
        "query": query,
        "intent": [],
        "customer_id": customer_id,
        "plan": {},
        "iteration": 0,
        "agent_outputs": {},
        "critique_verdicts": {},
        "mcp_calls_log": [],
        "kg_queries_log": [],
        "conversation_id": convo_id,
        "turn_id": turn_id,
        "audit_trace_id": audit_trace_id,
        "final_response": "",
        "risk_level": "low",
        "requires_human": False,
        "scratchpad": ""
    }
    
    print(f"--- Running Query: {query} ---")
    
    # Run the graph with LangSmith tags
    config = {
        "metadata": {
            "customer_id": customer_id,
            "scenario": scenario,
            "audit_trace_id": audit_trace_id
        },
        "tags": ["demo", scenario]
    }

    iterations = 0
    final_intents = []
    final_response_text = ""

    # Enable LangSmith project from env or default
    project_name = os.getenv("LANGCHAIN_PROJECT", "fincore-banking-demo")

    with tracing_v2_enabled(project_name=project_name):
        for output in app.stream(initial_state, config=config):
            for node_name, state_update in output.items():
                print(f"\nNode: {node_name}")
                
                if "plan" in state_update:
                    print(f"Plan: {state_update['plan']}")
                if "agent_outputs" in state_update:
                    print(f"Agent Output: {list(state_update['agent_outputs'].keys())}")
                if "critique_verdicts" in state_update:
                    print(f"Critique Verdicts: {state_update['critique_verdicts']}")
                if "intent" in state_update:
                    final_intents = state_update["intent"]
                if "iteration" in state_update:
                    iterations = state_update["iteration"]
                if "final_response" in state_update:
                    final_response_text = state_update["final_response"]
                    print(f"\n--- Final Response ---\n{final_response_text}")

    # Final Audit Update for the turn
    audit_logger.update_turn_final(turn_id, final_intents, final_response_text, iterations)

if __name__ == "__main__":
    # Demo Scenarios
    scenarios = [
        ("Check my account balance and tell me if I am eligible for a home loan of 20 lakhs. My customer ID is CUST-0042.", "loan_eligibility"),
        ("I saw a weird transaction of 45,000. Can you check it? My customer ID is CUST-0007.", "fraud_check")
    ]
    
    for query, scenario_name in scenarios:
        run_assistant(query, scenario=scenario_name)
