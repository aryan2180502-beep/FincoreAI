from langgraph.graph import StateGraph, END
from backend.graph.state import StateSchema
from backend.agents.core.parser import QueryParser
from backend.agents.core.orchestrator import Orchestrator
from backend.agents.core.planner import Planner
from backend.agents.core.base_agents import SpecialistAgent, CritiqueAgent
from backend.agents.core.aggregator import Aggregator
from backend.utils.prompt_loader import PromptLoader

def create_graph():
    loader = PromptLoader()
    parser = QueryParser()
    orchestrator = Orchestrator(loader)
    planner = Planner(loader)
    aggregator = Aggregator(loader)
    
    # Instantiate specialists and critics
    loan_agent = SpecialistAgent("loan", loader)
    loan_critique = CritiqueAgent("loan_critique", loader)
    
    fraud_agent = SpecialistAgent("fraud", loader)
    fraud_critique = CritiqueAgent("fraud_critique", loader)
    
    account_agent = SpecialistAgent("account", loader)
    account_critique = CritiqueAgent("account_critique", loader)
    
    compliance_agent = SpecialistAgent("compliance", loader)
    compliance_critique = CritiqueAgent("compliance_critique", loader)

    workflow = StateGraph(StateSchema)

    # Add Nodes
    workflow.add_node("query_parser", parser.parse)
    workflow.add_node("orchestrator", orchestrator.run)
    workflow.add_node("planner", planner.run)
    
    workflow.add_node("loan_agent", loan_agent.run)
    workflow.add_node("loan_critique", loan_critique.run)
    
    workflow.add_node("fraud_agent", fraud_agent.run)
    workflow.add_node("fraud_critique", fraud_critique.run)
    
    workflow.add_node("account_agent", account_agent.run)
    workflow.add_node("account_critique", account_critique.run)
    
    workflow.add_node("compliance_agent", compliance_agent.run)
    workflow.add_node("compliance_critique", compliance_critique.run)
    
    workflow.add_node("aggregator", aggregator.run)

    # Define Edges
    workflow.set_entry_point("query_parser")
    workflow.add_edge("query_parser", "orchestrator")
    
    workflow.add_conditional_edges(
        "orchestrator",
        orchestrator.decide_next_node,
        {
            "planner": "planner",
            "aggregator": "aggregator"
        }
    )
    
    # Planner logic: Normally it should dispatch agents. 
    # For simplicity in this graph definition, we'll route from planner back to orchestrator
    # and have orchestrator trigger agents. But the guide says Planner outputs agents to call.
    # In a real multi-agent graph, we'd have a router node after planner.
    
    def planner_router(state: StateSchema):
        plan = state.get("plan", {{}})
        if plan.get("done"):
            return "orchestrator"
        
        # Call the first agent in the list for now (simplification)
        agents = plan.get("agents_to_call", [])
        if agents:
            return agents[0]
        
        return "orchestrator"

    workflow.add_conditional_edges(
        "planner",
        planner_router,
        {
            "loan_agent": "loan_agent",
            "fraud_agent": "fraud_agent",
            "account_agent": "account_agent",
            "compliance_agent": "compliance_agent",
            "orchestrator": "orchestrator"
        }
    )

    # Specialist -> Critique edges
    workflow.add_edge("loan_agent", "loan_critique")
    workflow.add_edge("loan_critique", "orchestrator")
    
    workflow.add_edge("fraud_agent", "fraud_critique")
    workflow.add_edge("fraud_critique", "orchestrator")
    
    workflow.add_edge("account_agent", "account_critique")
    workflow.add_edge("account_critique", "orchestrator")
    
    workflow.add_edge("compliance_agent", "compliance_critique")
    workflow.add_edge("compliance_critique", "orchestrator")

    workflow.add_edge("aggregator", END)

    return workflow.compile()
