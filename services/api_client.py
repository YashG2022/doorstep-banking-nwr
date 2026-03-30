import requests

API_BASE = "http://localhost:5001"  # change to your API

def store_data(payload):
    requests.post(f"{API_BASE}/store", json=payload)

def get_all():
    response = requests.get(f"{API_BASE}/records")
    return response.json()

def get_one(submission_id):
    response = requests.get(f"{API_BASE}/records/{submission_id}")
    return response.json()