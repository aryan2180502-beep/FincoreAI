from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid
import os
from dotenv import load_dotenv

from backend.graph.graph import create_graph
from backend.utils.audit_logger import AuditLogger

load_dotenv()

app = FastAPI(title="FincoreAI API")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str
    customer_id: Optional[str] = "CUST-0042"
    scenario: Optional[str] = "general"

class QueryResponse(BaseModel):
    response: str
    conversation_id: str
    turn_id: str
    intents: List[str]
    iterations: int

graph = create_graph()
audit_logger = AuditLogger()

@app.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    convo_id = str(uuid.uuid4())
    turn_id = str(uuid.uuid4())
    audit_trace_id = str(uuid.uuid4())
    
    # Initialize Audit DB
    audit_logger.create_conversation(convo_id, request.customer_id)
    audit_logger.create_turn(turn_id, convo_id, request.query)
    
    initial_state = {
        "query": request.query,
        "intent": [],
        "customer_id": request.customer_id,
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
    
    final_state = {}
    
    try:
        # We run the graph synchronously for this API call
        # In a real production app, we might use streaming or background tasks
        for output in graph.stream(initial_state):
            for node_name, state_update in output.items():
                final_state.update(state_update)
        
        final_response_text = final_state.get("final_response", "I'm sorry, I couldn't process that.")
        final_intents = final_state.get("intent", [])
        iterations = final_state.get("iteration", 0)
        
        # Update Audit
        audit_logger.update_turn_final(turn_id, final_intents, final_response_text, iterations)
        
        return QueryResponse(
            response=final_response_text,
            conversation_id=convo_id,
            turn_id=turn_id,
            intents=final_intents,
            iterations=iterations
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
