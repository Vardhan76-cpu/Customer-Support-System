import os

from dotenv import load_dotenv
from huggingface_hub import InferenceClient


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
    raise RuntimeError(
        "HF_TOKEN is not set in the .env file."
    )


client = InferenceClient(
    api_key=HF_TOKEN,
    provider="auto",
)


# ============================================================
# Helper: safely get message content
# ============================================================

def _extract_content(response) -> str:

    if not response:
        return ""

    choices = getattr(
        response,
        "choices",
        None,
    )

    if not choices:
        return ""

    message = getattr(
        choices[0],
        "message",
        None,
    )

    if not message:
        return ""

    content = getattr(
        message,
        "content",
        None,
    )

    if content:
        return str(content).strip()

    return ""


# ============================================================
# Generate chatbot answer
# ============================================================

def generate_chat_answer(
    query: str,
    history: list,
    summary: str,
    results: list,
) -> str:

    # --------------------------------------------------------
    # Build knowledge context
    # --------------------------------------------------------

    context_parts = []

    for i, result in enumerate(
        results[:3],
        start=1,
    ):

        text = result.get(
            "text",
            "",
        )

        # Avoid sending extremely large chunks.
        text = text[:3500]

        context_parts.append(
            f"""
[Knowledge Source {i}]
Document: {result.get("document_name", "Unknown")}
Page: {result.get("page_number", "N/A")}

{text}
"""
        )

    if context_parts:

        knowledge_context = "\n\n".join(
            context_parts
        )

    else:

        knowledge_context = (
            "No relevant knowledge-base information "
            "was found."
        )

    # --------------------------------------------------------
    # Conversation context
    # --------------------------------------------------------

    conversation_parts = []

    if summary:

        conversation_parts.append(
            "Conversation Summary:\n"
            + summary
        )

    if history:

        # Only keep the latest 4 messages.
        recent_history = history[-4:]

        history_text = "\n".join(
            f'{message["role"].capitalize()}: '
            f'{message["content"]}'
            for message in recent_history
        )

        conversation_parts.append(
            "Recent Conversation:\n"
            + history_text
        )

    if conversation_parts:

        conversation_context = "\n\n".join(
            conversation_parts
        )

    else:

        conversation_context = (
            "No previous conversation."
        )

    # --------------------------------------------------------
    # Prompt
    # --------------------------------------------------------

    user_prompt = f"""
You are a customer support chatbot.

Answer the user's current question using the
knowledge base provided below.

CONVERSATION:
{conversation_context}

KNOWLEDGE BASE:
{knowledge_context}

CURRENT QUESTION:
{query}

RULES:

1. Use the knowledge base as the primary source.
2. Use the conversation context when useful.
3. Do not invent facts.
4. If the answer exists in the knowledge base,
   explain it clearly.
5. If the answer is not available in the knowledge base,
   say that you could not find the answer.
6. Answer the current question directly.
7. Keep the answer concise.
8. Do not output your reasoning.
9. Return only the final answer.
"""

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful and concise "
                "customer support knowledge-base "
                "assistant."
            ),
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]

    # --------------------------------------------------------
    # Hugging Face request
    # --------------------------------------------------------

    try:

        response = client.chat.completions.create(
            model=HF_MODEL,
            messages=messages,

            # Enough room for reasoning + final answer.
            max_tokens=1000,

            temperature=0.1,

            # DeepSeek-specific settings.
            # HF InferenceClient passes provider-specific
            # fields through extra_body.
            extra_body={
                "reasoning_effort": "low",
                "chat_template_kwargs": {
                    "thinking": True,
                    "reasoning_effort": "low",
                },
            },
        )

        # ----------------------------------------------------
        # Extract final answer
        # ----------------------------------------------------

        answer = _extract_content(
            response
        )

        if answer:

            return answer

        # ----------------------------------------------------
        # Debug information
        # ----------------------------------------------------

        print(
            "\n========== EMPTY DEEPSEEK RESPONSE =========="
        )

        print(
            "Response:",
            response,
        )

        if getattr(response, "choices", None):

            choice = response.choices[0]

            print(
                "Finish reason:",
                getattr(
                    choice,
                    "finish_reason",
                    None,
                ),
            )

            message = getattr(
                choice,
                "message",
                None,
            )

            if message:

                print(
                    "Reasoning:",
                    getattr(
                        message,
                        "reasoning",
                        None,
                    ),
                )

                print(
                    "Reasoning content:",
                    getattr(
                        message,
                        "reasoning_content",
                        None,
                    ),
                )

        print(
            "=============================================\n"
        )

        return (
            "I found relevant information in the "
            "knowledge base, but the AI model did not "
            "return a final answer. Please try again."
        )

    except Exception as exc:

        print(
            "\n========== DEEPSEEK ERROR =========="
        )

        print(
            "Error type:",
            type(exc).__name__,
        )

        print(
            "Error:",
            str(exc),
        )

        print(
            "====================================\n"
        )

        return (
            "I found relevant information in the "
            "knowledge base, but the AI service "
            "could not generate the answer. "
            "Please try again."
        )


# ============================================================
# Summarize conversation
# ============================================================

def summarize_conversation(
    old_summary: str,
    messages: list,
) -> str:

    if not messages:

        return old_summary or ""

    # Keep summarization input manageable.
    messages = messages[-20:]

    conversation_text = "\n".join(
        f'{message["role"].capitalize()}: '
        f'{message["content"]}'
        for message in messages
    )

    prompt = f"""
Create a concise summary of this customer
support conversation.

Keep only important information:

- User's main problem
- Important facts
- Product or feature mentioned
- Solutions already suggested
- Decisions already made
- Important unresolved questions

Do not invent information.

Previous summary:
{old_summary}

Conversation:
{conversation_text}

Return only the updated summary.
"""

    messages_for_model = [
        {
            "role": "system",
            "content": (
                "You summarize customer support "
                "conversations accurately and "
                "concisely."
            ),
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    try:

        response = client.chat.completions.create(
            model=HF_MODEL,
            messages=messages_for_model,
            max_tokens=400,
            temperature=0.1,
            extra_body={
                "reasoning_effort": "low",
                "chat_template_kwargs": {
                    "thinking": True,
                    "reasoning_effort": "low",
                },
            },
        )

        summary = _extract_content(
            response
        )

        if summary:

            return summary

        return old_summary or ""

    except Exception as exc:

        print(
            "Conversation summarization error:",
            repr(exc),
        )

        # Summarization failure must never
        # break the chatbot.
        return old_summary or ""