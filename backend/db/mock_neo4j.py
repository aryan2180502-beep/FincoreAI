import json
import os
import time
import uuid

class MockNeo4j:
    def __init__(self, audit_logger):
        self.audit_logger = audit_logger
        self.fixtures_dir = "data/fixtures"

    def _log_query(self, execution_id, query, params, result_count):
        self.audit_logger.log_kg_query(execution_id, query, params, result_count)

    def execute_query(self, execution_id: str, query_type: str, params: dict):
        """
        Simulates the 5 required Cypher queries (Q1-Q5) and logs them.
        """
        # Q1: Account & Balance Lookup
        if query_type == "Q1":
            cypher = "MATCH (c:Customer {id: $cid})-[:HAS_ACCOUNT]->(a:Account) RETURN a.id, a.type, a.balance, a.status ORDER BY a.balance DESC"
            # In a real demo, we'd fetch from a seed JSON. 
            # For now, we return a mock count and log it.
            self._log_query(execution_id, cypher, params, 3)
            return [{"id": "ACT-12345", "type": "Savings", "balance": 250000}]

        # Q2: Existing Active Loans
        elif query_type == "Q2":
            cypher = "MATCH (c:Customer {id: $cid})-[:HAS_LOAN]->(l:Loan {status: 'active'}) RETURN l.type, l.emi, l.outstanding"
            self._log_query(execution_id, cypher, params, 1)
            return [{"type": "Car Loan", "emi": 15000, "outstanding": 450000}]

        # Q3: Regulation Traversal
        elif query_type == "Q3":
            cypher = "MATCH (l:Loan {type: $ltype})-[:GOVERNED_BY]->(r:RegulationRule) RETURN r.source, r.description, r.effective_date"
            self._log_query(execution_id, cypher, params, 2)
            return [{"source": "RBI", "description": "LTV ratio rules"}]

        # Q4: Inactive Accounts
        elif query_type == "Q4":
            cypher = "MATCH (c:Customer {id: $cid})-[:HAS_ACCOUNT]->(a:Account) WHERE a.last_txn_date < date() - duration('P180D') RETURN a.id, a.type, a.last_txn_date"
            self._log_query(execution_id, cypher, params, 2)
            return [{"id": "ACT-11111", "type": "Savings", "last_txn": "2022-05-10"}]

        # Q5: Fraud Ring Detection
        elif query_type == "Q5":
            cypher = "MATCH (c:Customer {id: $cid})-[:LINKED_TO*1..2]-(s:Customer)-[:HAS_ACCOUNT]->(:Account)-[:HAS_TRANSACTION]->(t:Transaction)-[:FLAGGED_BY]->(f:RiskFlag) RETURN s.id, s.name, f.severity, count(t) AS flagged_txns"
            self._log_query(execution_id, cypher, params, 1)
            return [{"id": "CUST-0019", "name": "Unknown Associate", "severity": "High"}]

        return []
