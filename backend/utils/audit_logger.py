import sqlite3
import json
from datetime import datetime
import os
import uuid
from typing import Dict, Any, Optional

class AuditLogger:
    def __init__(self, db_path="backend/db/audit.sqlite"):
        self.db_path = db_path

    def _execute(self, query: str, params: tuple):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute(query, params)
        conn.commit()
        conn.close()

    def create_conversation(self, conversation_id: str, customer_id: str, status: str = "active"):
        query = "INSERT OR IGNORE INTO conversations (id, customer_id, status) VALUES (?, ?, ?)"
        self._execute(query, (conversation_id, customer_id, status))

    def create_turn(self, turn_id: str, conversation_id: str, query_text: str):
        query = "INSERT INTO turns (id, conversation_id, query) VALUES (?, ?, ?)"
        self._execute(query, (turn_id, conversation_id, query_text))

    def update_turn_final(self, turn_id: str, intent: list, final_response: str, iterations: int):
        query = "UPDATE turns SET intent = ?, final_response = ?, iterations_used = ? WHERE id = ?"
        self._execute(query, (json.dumps(intent), final_response, iterations, turn_id))

    # Specification 6.2 Methods
    def log_agent_start(self, turn_id: str, agent_name: str, iteration: int, input_state: Any) -> str:
        execution_id = str(uuid.uuid4())
        query = '''
        INSERT INTO agent_executions (id, turn_id, agent_name, iteration, input_state)
        VALUES (?, ?, ?, ?, ?)
        '''
        self._execute(query, (
            execution_id,
            turn_id,
            agent_name,
            iteration,
            json.dumps(input_state) if input_state else None
        ))
        return execution_id

    def log_agent_end(self, execution_id: str, output: Any, verdict: Optional[str], duration_ms: int):
        query = '''
        UPDATE agent_executions 
        SET output = ?, verdict = ?, duration_ms = ?
        WHERE id = ?
        '''
        self._execute(query, (
            json.dumps(output) if output else None,
            verdict,
            duration_ms,
            execution_id
        ))

    def log_mcp_call(self, execution_id: str, server: str, tool: str, params: Any, response: Any, duration_ms: int):
        call_id = str(uuid.uuid4())
        query = '''
        INSERT INTO mcp_calls (id, agent_execution_id, server, tool, input_params, response, duration_ms)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        self._execute(query, (
            call_id,
            execution_id,
            server,
            tool,
            json.dumps(params) if params else None,
            json.dumps(response) if response else None,
            duration_ms
        ))

    def log_kg_query(self, execution_id: str, cypher: str, params: Any, result_count: int):
        query_id = str(uuid.uuid4())
        query = '''
        INSERT INTO kg_queries (id, agent_execution_id, cypher_query, parameters, result_count)
        VALUES (?, ?, ?, ?, ?)
        '''
        self._execute(query, (
            query_id,
            execution_id,
            cypher,
            json.dumps(params) if params else None,
            result_count
        ))
