import json
import os

class MockMCP:
    FIXTURES_DIR = "data/fixtures"

    @classmethod
    def _load_fixture(cls, name):
        path = os.path.join(cls.FIXTURES_DIR, f"{name}.json")
        if not os.path.exists(path):
            return {}
        with open(path, "r") as f:
            return json.load(f)

    @classmethod
    def get_account_summary(cls, customer_id: str):
        data = cls._load_fixture("core_banking")
        return data.get(customer_id, {}).get("accounts", [])

    @classmethod
    def get_transactions(cls, customer_id: str):
        data = cls._load_fixture("core_banking")
        return data.get(customer_id, {}).get("transactions", [])

    @classmethod
    def get_credit_score(cls, customer_id: str):
        data = cls._load_fixture("credit")
        return data.get(customer_id, {}).get("credit_score", 0)

    @classmethod
    def get_emi_schedule(cls, customer_id: str):
        data = cls._load_fixture("credit")
        return data.get(customer_id, {}).get("loans", [])

    @classmethod
    def score_transaction_risk(cls, txn_id: str):
        data = cls._load_fixture("fraud")
        return data.get(txn_id, {}).get("risk_score", 0.0)

    @classmethod
    def get_regulation_rules(cls):
        data = cls._load_fixture("compliance")
        return data.get("rules", [])
    
    @classmethod
    def get_docs_required(cls, product_type: str):
        data = cls._load_fixture("compliance")
        return data.get("requirements", {}).get(product_type, [])
