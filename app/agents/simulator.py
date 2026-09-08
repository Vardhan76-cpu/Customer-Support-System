import json
import os
from typing import Dict, Any

from dotenv import load_dotenv
from huggingface_hub import InferenceClient

from app.models.schemas import SimulatorConfig

# ============================================================
# Configuration
# ============================================================

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = os.getenv(
    "HF_MODEL",
    "deepseek-ai/DeepSeek-V4-Flash-0731",
)

if not HF_TOKEN:
    raise RuntimeError("HF_TOKEN is not set in the .env file.")

client = InferenceClient(api_key=HF_TOKEN, provider="auto")


# ============================================================
# Helper: safely get message content
# ============================================================

def _extract_content(response) -> str:
    if not response:
        return ""
    choices = getattr(response, "choices", None)
    if not choices:
        return ""
    message = getattr(choices[0], "message", None)
    if not message:
        return ""
    content = getattr(message, "content", None)
    if content:
        return str(content).strip()
    return ""


# ============================================================
# Generate Customer Turn
# ============================================================

def generate_customer_turn(
    agent_message: str,
    history: list,
    config: SimulatorConfig,
) -> Dict[str, Any]:
    """
    Simulates the customer's next message given the scenario,
    persona, and the agent's response. Also updates the emotional state.
    """
    
    # --------------------------------------------------------
    # Conversation context
    # --------------------------------------------------------
    
    # Only keep the latest 10 messages for context
    recent_history = history[-10:] if history else []
    
    history_text = ""
    if recent_history:
        history_text = "\n".join(
            f'{"Customer" if msg["role"] == "user" else "Agent"}: {msg["content"]}'
            for msg in recent_history
        )
    else:
        history_text = "No previous conversation."

    # --------------------------------------------------------
    # Prompt
    # --------------------------------------------------------

    system_prompt = f"""
You are a Customer Simulator Agent for a customer support training platform.
Your task is to generate realistic, turn-by-turn customer responses based on the provided scenario and persona.

SCENARIO CONFIGURATION:
- Persona: {config.persona}
- Scenario: {config.scenario}
- Current Emotion: {config.current_emotion}
- Issue Severity: {config.issue_severity}
- Patience Level: {config.patience_level}
- Expected Resolution: {config.expected_resolution}

RULES:
1. You must respond IN CHARACTER as the customer. 
2. Consider the 'Agent's Response' carefully. If the agent is helpful, your emotion may improve. If unhelpful or slow, your emotion may worsen.
3. Be realistic. Do not be overly verbose unless the persona demands it.
4. Output YOUR RESPONSE as a JSON object with EXACTLY these three keys:
   - "customer_message": Your actual dialogue/message as the customer.
   - "current_emotion": Your new emotional state (e.g., frustrated, calm, happy, angry).
   - "patience_level": Your new patience level (high, medium, low, exhausted).

Output ONLY the raw JSON object, without any markdown formatting like ```json ... ```.
"""

    user_prompt = f"""
CONVERSATION HISTORY:
{history_text}

AGENT'S LATEST RESPONSE:
{agent_message}

Generate your next response and updated emotional state as a JSON object.
"""

    messages = [
        {"role": "system", "content": system_prompt.strip()},
        {"role": "user", "content": user_prompt.strip()},
    ]

    try:
        response = client.chat.completions.create(
            model=HF_MODEL,
            messages=messages,
            max_tokens=800,
            temperature=0.7,
            extra_body={
                "reasoning_effort": "low",
                "chat_template_kwargs": {
                    "thinking": True,
                    "reasoning_effort": "low",
                },
            },
        )

        content = _extract_content(response)

        if not content:
            raise ValueError("Empty response from LLM")
            
        # Try to parse JSON. Sometimes LLMs still wrap in markdown despite instructions.
        import re
        
        # Strip potential markdown code blocks
        json_str = content
        if "```json" in json_str:
            json_str = re.search(r'```json(.*?)```', json_str, re.DOTALL)
            if json_str:
                json_str = json_str.group(1).strip()
            else:
                json_str = content # fallback
        elif "```" in json_str:
            json_str = re.search(r'```(.*?)```', json_str, re.DOTALL)
            if json_str:
                json_str = json_str.group(1).strip()
            else:
                json_str = content
                
        try:
            parsed_result = json.loads(json_str)
            return {
                "customer_message": parsed_result.get("customer_message", "I don't know what to say."),
                "current_emotion": parsed_result.get("current_emotion", config.current_emotion),
                "patience_level": parsed_result.get("patience_level", config.patience_level)
            }
        except json.JSONDecodeError as e:
            print(f"JSON Parsing Error: {e}. Raw content: {content}")
            # Fallback if the LLM didn't return valid JSON
            return {
                "customer_message": content, # Just dump the content
                "current_emotion": config.current_emotion,
                "patience_level": config.patience_level
            }

    except Exception as exc:
        print(f"SIMULATOR API WARNING/FALLBACK: {repr(exc)}")
        # Graceful dynamic fallback generator to ensure simulator always generates realistic,
        # scenario-consistent messages and emotional progression even when API quota is exhausted.
        return _generate_fallback_turn(agent_message, history, config)


# ============================================================
# Scenario-driven Realistic Fallback Engine
# ============================================================

def _generate_fallback_turn(
    agent_message: str,
    history: list,
    config: SimulatorConfig,
) -> Dict[str, Any]:
    """
    Heuristic-based contextual response generator that adheres to the configured
    persona, scenario, issue severity, and emotional progression rules.
    Used when external LLM endpoints hit quota or network errors.
    """
    msg_lower = agent_message.lower()
    curr_emotion = (config.current_emotion or config.initial_emotion or "neutral").lower()
    patience = (config.patience_level or "medium").lower()

    # Determine turn count based on history
    turn_count = len([m for m in (history or []) if m.get("role") in ("user", "assistant")]) // 2 + 1

    # Emotion progression state machine
    is_positive_resolution = any(kw in msg_lower for kw in [
        "refund", "initiated", "resolved", "overnight", "upgraded", "cancelled",
        "released", "credited", "sent to your inbox", "zero cost", "processed"
    ])
    is_info_request = any(kw in msg_lower for kw in [
        "order number", "order id", "email", "tracking", "account details",
        "verify", "details", "could you please share", "confirm"
    ])

    new_emotion = curr_emotion
    new_patience = patience

    if is_positive_resolution:
        if curr_emotion in ["angry", "frustrated", "impatient"]:
            new_emotion = "relieved" if turn_count >= 2 else "calm"
            new_patience = "high"
        elif curr_emotion in ["confused"]:
            new_emotion = "relieved"
            new_patience = "high"
        else:
            new_emotion = "satisfied"
            new_patience = "high"
    elif is_info_request:
        if curr_emotion == "angry" and patience == "low":
            new_emotion = "frustrated" # slight shift as progress is being made
            new_patience = "medium"
        elif curr_emotion == "impatient":
            new_patience = "medium"
    else:
        # Generic or stalling response
        if curr_emotion in ["angry", "frustrated"]:
            new_patience = "low"
        elif curr_emotion == "calm":
            new_emotion = "neutral"

    # Contextual dialogue generation based on scenario and persona
    scenario_lower = config.scenario.lower()
    persona_lower = config.persona.lower()

    if is_positive_resolution:
        if persona_lower == "angry":
            message = (
                f"Alright, I see you processed the {config.expected_resolution}. "
                f"It shouldn't have taken this much effort, but I appreciate that you finally resolved it. "
                f"Please ensure a confirmation receipt is sent to my email immediately."
            )
        elif persona_lower == "confused":
            message = (
                f"Oh, that's such a relief! Thank you for clarifying that for me. "
                f"I'm glad the {config.scenario} is sorted out now and I don't have to worry about extra charges."
            )
        elif persona_lower == "impatient":
            message = (
                f"Finally, thank you. I'm glad this was expedited without further delay. "
                f"I'll be watching for the tracking and confirmation email within the hour."
            )
        else:
            message = (
                f"Thank you very much for your quick help in resolving this! "
                f"I really appreciate your assistance with my {config.scenario}."
            )

    elif is_info_request:
        if "order" in msg_lower:
            ref_info = "My order number is #ORD-84920."
        elif "email" in msg_lower:
            ref_info = "My registered email address is customer.support.test@example.com."
        else:
            ref_info = "My reference number is #REF-44219."

        if persona_lower == "angry":
            message = (
                f"{ref_info} Here it is. Now please look into this right away, "
                f"because I've already waited too long for my {config.scenario}."
            )
        elif persona_lower == "confused":
            message = (
                f"Sure, {ref_info} Is that what you need, or do you need me to provide any billing statements as well?"
            )
        elif persona_lower == "impatient":
            message = (
                f"{ref_info} Please check it quickly—I need this expedited immediately."
            )
        else:
            message = (
                f"Yes, certainly. {ref_info} Please let me know if you need any additional details."
            )

    else:
        # Opening or general turn
        if turn_count <= 1:
            if "refund" in scenario_lower:
                message = f"Hello. I am contacting you because I need a {config.expected_resolution} for my {config.scenario}. Can you assist with this?"
            elif "delay" in scenario_lower or "order" in scenario_lower:
                message = f"Hi, my package was supposed to arrive already and the status has not updated. This is urgent because I need it as soon as possible."
            elif "payment" in scenario_lower or "card" in scenario_lower:
                message = f"Hello, I noticed an issue with my payment for my recent order. It appears I was charged, but the status is unclear. Could you check what happened?"
            elif "cancel" in scenario_lower:
                message = f"Hi, I would like to request a cancellation for my subscription/order. Could you please process this for me?"
            else:
                message = f"Hello, I'm experiencing an issue regarding {config.scenario} and I would appreciate your help getting it resolved."
            
            if persona_lower == "angry":
                message = message.replace("Hello.", "I am very upset.").replace("Hi,", "Look,")
        else:
            message = (
                f"I understand, but my priority is getting {config.expected_resolution}. "
                f"What are the next steps to ensure this is taken care of?"
            )

    return {
        "customer_message": message,
        "current_emotion": new_emotion,
        "patience_level": new_patience
    }
