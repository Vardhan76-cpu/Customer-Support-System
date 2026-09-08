import json
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

SCENARIOS = [
    {
        "name": "Refund Request - Angry Customer",
        "persona": "angry",
        "scenario": "refund request for defective electronic item received 3 days ago",
        "initial_emotion": "angry",
        "issue_severity": "high",
        "patience_level": "low",
        "expected_resolution": "immediate full refund without restocking fee",
        "turns": [
            "Hello, thank you for reaching out to support. How can I help you today?",
            "I apologize for the defective item. Could you please share your order number so I can check your account details?",
            "Thank you. I have verified your order and initiated a full refund back to your original payment method. You should see it in 3-5 business days."
        ]
    },
    {
        "name": "Payment Failure - Confused Customer",
        "persona": "confused",
        "scenario": "card charged twice during checkout but order status says pending",
        "initial_emotion": "confused",
        "issue_severity": "medium",
        "patience_level": "medium",
        "expected_resolution": "clarity on charges and confirmation of order",
        "turns": [
            "Welcome to customer support! How can I assist you with your account today?",
            "No problem at all, I can look into that billing discrepancy right now. Let me review the duplicate transaction records.",
            "I checked our payment gateway: one transaction was only a temporary pre-authorization hold and has already been released. Your order is confirmed and will ship tomorrow!"
        ]
    },
    {
        "name": "Delayed Order - Impatient Customer",
        "persona": "impatient",
        "scenario": "birthday gift order delayed past guaranteed delivery date",
        "initial_emotion": "impatient",
        "issue_severity": "high",
        "patience_level": "low",
        "expected_resolution": "expedited delivery upgrade or delivery fee reimbursement",
        "turns": [
            "Hi there, thank you for contacting us. What can I do for you?",
            "I completely understand this is for a birthday and time is critical. Let me coordinate with our priority dispatch team right away.",
            "I have upgraded your shipment to overnight priority at zero cost, and refunded your shipping fee. You will receive tracking within the hour."
        ]
    },
    {
        "name": "Cancellation - Calm and Polite Customer",
        "persona": "polite",
        "scenario": "accidental double purchase of annual subscription",
        "initial_emotion": "calm",
        "issue_severity": "low",
        "patience_level": "high",
        "expected_resolution": "cancellation of the duplicate license and confirmation email",
        "turns": [
            "Hello! Welcome to support. How may I be of assistance today?",
            "I would be glad to help cancel the duplicate subscription for you right away. May I confirm the email associated with your account?",
            "The extra subscription has been cancelled and refunded in full. A confirmation email has just been sent to your inbox."
        ]
    }
]

def run_tests():
    all_logs = []
    print("=== STARTING MULTI-SCENARIO SIMULATOR TEST SUITE ===")

    for sc in SCENARIOS:
        print(f"\n---> Testing Scenario: {sc['name']}")
        conv_id = None
        current_emotion = sc["initial_emotion"]
        patience_level = sc["patience_level"]
        log_entries = []

        for turn_idx, agent_msg in enumerate(sc["turns"], 1):
            config = {
                "persona": sc["persona"],
                "scenario": sc["scenario"],
                "initial_emotion": sc["initial_emotion"],
                "current_emotion": current_emotion,
                "issue_severity": sc["issue_severity"],
                "patience_level": patience_level,
                "expected_resolution": sc["expected_resolution"]
            }

            payload = {
                "conversation_id": conv_id,
                "agent_message": agent_msg,
                "config": config
            }

            resp = client.post("/simulator/chat", json=payload)
            if resp.status_code != 200:
                print(f"Error turn {turn_idx}: {resp.status_code} - {resp.text}")
                break

            data = resp.json()
            conv_id = data.get("conversation_id")
            customer_msg = data.get("customer_message")
            current_emotion = data.get("current_emotion")
            patience_level = data.get("patience_level")

            print(f"  Turn {turn_idx}:")
            print(f"    Agent: {agent_msg}")
            print(f"    Customer: {customer_msg}")
            print(f"    Updated State -> Emotion: {current_emotion}, Patience: {patience_level}")

            log_entries.append({
                "turn": turn_idx,
                "agent_message": agent_msg,
                "customer_response": customer_msg,
                "emotion": current_emotion,
                "patience": patience_level
            })

        all_logs.append({
            "scenario": sc["name"],
            "conversation_id": conv_id,
            "config": sc,
            "turns": log_entries
        })

    # Save logs
    output_path = Path("sample_simulation_logs.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_logs, f, indent=2)
    print(f"\nSimulation test completed. Logs saved to {output_path.resolve()}")

if __name__ == "__main__":
    run_tests()
