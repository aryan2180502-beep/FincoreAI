from typing import List, Dict, Any, TypedDict, Optional

class StateSchema(TypedDict):
    # Original raw customer query
    query: str
    
    # List of intents extracted from query
    intent: List[str]
    
    # Resolved customer ID
    customer_id: str
    
    # Current planner output
    plan: Dict[str, Any]
    
    # Orchestrator loop counter
    iteration: int
    
    # Results from verified specialist agents
    agent_outputs: Dict[str, Any]
    
    # Verdicts from critique agents (PASS / RETRY / ESCALATE)
    critique_verdicts: Dict[str, str]
    
    # Logs for audit and tracing
    mcp_calls_log: List[Dict[str, Any]]
    kg_queries_log: List[str]
    
    # IDs for auditing
    conversation_id: str
    turn_id: str
    audit_trace_id: str
    
    # Final synthesized response
    final_response: str
    
    # Risk assessment
    risk_level: str
    
    # Human escalation flag
    requires_human: bool
    
    # Scratchpad for Orchestrator internal reasoning
    scratchpad: str
