from faker import Faker
import json
import uuid
import random

# Requirement 9.1: Seed 42 for consistency
fake = Faker()
Faker.seed(42)
random.seed(42)

def generate_customer_data():
    customers = [
        {
            "id": "CUST-0042",
            "name": "Rajesh Sharma",
            "pan": "ABCDE1234F",
            "credit_score": 712,
            "kyc_status": "verified",
            "segment": "gold"
        },
        {
            "id": "CUST-0007",
            "name": "Priya Mehta",
            "pan": "FGHIJ5678K",
            "credit_score": 820,
            "kyc_status": "verified",
            "segment": "platinum"
        }
    ]
    # Add more random customers
    for _ in range(18):
        customers.append({
            "id": f"CUST-{fake.unique.random_number(digits=4)}",
            "name": fake.name(),
            "pan": fake.bothify(text='?????####?').upper(),
            "credit_score": random.randint(300, 850),
            "kyc_status": "verified",
            "segment": "silver"
        })
    return customers

def generate_neo4j_fixtures():
    data = {
        "nodes": {
            "Customer": generate_customer_data(),
            "Account": [
                {"id": "ACT-12345", "type": "Savings", "balance": 250000, "last_txn_date": "2023-01-15", "cid": "CUST-0042"},
                {"id": "ACT-67890", "type": "Current", "balance": 1000000, "last_txn_date": "2023-11-20", "cid": "CUST-0042"},
                {"id": "ACT-11111", "type": "Savings", "balance": 5000, "last_txn_date": "2022-05-10", "cid": "CUST-0042"},
                {"id": "ACT-99999", "type": "Savings", "balance": 1500000, "last_txn_date": "2024-03-10", "cid": "CUST-0007"}
            ]
        },
        "relationships": [
            {"from": "CUST-0042", "to": "ACT-12345", "type": "HAS_ACCOUNT"},
            {"from": "CUST-0042", "to": "ACT-67890", "type": "HAS_ACCOUNT"},
            {"from": "CUST-0042", "to": "ACT-11111", "type": "HAS_ACCOUNT"},
            {"from": "CUST-0007", "to": "ACT-99999", "type": "HAS_ACCOUNT"},
            {"from": "CUST-0042", "to": "CUST-0019", "type": "LINKED_TO", "reason": "shared_device"}
        ]
    }
    
    with open("data/neo4j_seed.json", "w") as f:
        json.dump(data, f, indent=2)
    
    print("Neo4j dummy data with seed=42 generated to data/neo4j_seed.json")

if __name__ == "__main__":
    generate_neo4j_fixtures()
