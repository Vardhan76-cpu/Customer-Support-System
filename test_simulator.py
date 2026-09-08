from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_simulator_chat():
    print("Testing Simulator Chat Endpoint...")
    
    payload = {
        "agent_message": "Hello! I understand you are having an issue with your recent order. How can I assist you?",
        "config": {
            "persona": "angry",
            "scenario": "delayed order",
            "initial_emotion": "frustrated",
            "current_emotion": "frustrated",
            "issue_severity": "high",
            "patience_level": "low",
            "expected_resolution": "immediate refund or expedited shipping"
        }
    }
    
    response = client.post("/simulator/chat", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("\nSUCCESS!")
        print(f"Conversation ID: {data.get('conversation_id')}")
        print(f"Customer Message: {data.get('customer_message')}")
        print(f"Current Emotion: {data.get('current_emotion')}")
        print(f"Patience Level: {data.get('patience_level')}")
    else:
        print(f"\nFAILED! Status Code: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_simulator_chat()
