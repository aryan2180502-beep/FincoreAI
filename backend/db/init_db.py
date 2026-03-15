import sqlite3
import os

def init_audit_db(db_path="backend/db/audit.sqlite"):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    # Table 1: conversations
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY,
        customer_id TEXT,
        started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT
    )
    ''')

    # Table 2: turns
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS turns (
        id TEXT PRIMARY KEY,
        conversation_id TEXT,
        query TEXT,
        intent TEXT,
        final_response TEXT,
        iterations_used INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conversation_id) REFERENCES conversations(id)
    )
    ''')
    
    # Table 3: agent_executions
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agent_executions (
        id TEXT PRIMARY KEY,
        turn_id TEXT,
        agent_name TEXT,
        iteration INTEGER,
        input_state TEXT,
        output TEXT,
        verdict TEXT,
        prompt_used TEXT,
        executed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        duration_ms INTEGER,
        FOREIGN KEY (turn_id) REFERENCES turns(id)
    )
    ''')

    # Table 4: mcp_calls
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS mcp_calls (
        id TEXT PRIMARY KEY,
        agent_execution_id TEXT,
        server TEXT,
        tool TEXT,
        input_params TEXT,
        response TEXT,
        called_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        duration_ms INTEGER,
        FOREIGN KEY (agent_execution_id) REFERENCES agent_executions(id)
    )
    ''')

    # Table 5: kg_queries
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS kg_queries (
        id TEXT PRIMARY KEY,
        agent_execution_id TEXT,
        cypher_query TEXT,
        parameters TEXT,
        result_count INTEGER,
        executed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (agent_execution_id) REFERENCES agent_executions(id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Audit database initialized at {db_path} with 5-table schema.")

if __name__ == "__main__":
    init_audit_db()
