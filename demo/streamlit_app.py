import requests
import streamlit as st

# ============================================================
# Configuration
# ============================================================

API_URL = "http://127.0.0.1:8000"

# ============================================================
# Page configuration
# ============================================================

st.set_page_config(
    page_title="AI Customer Support Coaching & Simulation Platform",
    page_icon="🎧",
    layout="wide",
)

# ============================================================
# Mode Selection in Sidebar
# ============================================================

st.sidebar.title("🎛️ Navigation & Modes")
app_mode = st.sidebar.radio(
    "Select Operating Mode:",
    [
        "🎭 Customer Simulator Agent (Task 3)",
        "📚 Support Knowledge Base & RAG (Task 2)",
    ],
    index=0,
)

st.sidebar.divider()

# ============================================================
# MODE 1: CUSTOMER SIMULATOR AGENT (TASK 3)
# ============================================================

if app_mode == "🎭 Customer Simulator Agent (Task 3)":
    st.title("🎭 Customer Simulator Agent")
    st.caption(
        "Simulates realistic, turn-by-turn customer conversations with configurable personas, "
        "scenarios, and dynamic emotional progression based on agent responses."
    )

    # Simulator Session State
    if "sim_conversation_id" not in st.session_state:
        st.session_state.sim_conversation_id = None
    if "sim_messages" not in st.session_state:
        st.session_state.sim_messages = []
    if "sim_current_emotion" not in st.session_state:
        st.session_state.sim_current_emotion = "frustrated"
    if "sim_patience" not in st.session_state:
        st.session_state.sim_patience = "medium"

    with st.sidebar:
        st.header("⚙️ Simulator Configuration")

        persona = st.selectbox(
            "Customer Persona:",
            ["calm", "confused", "frustrated", "angry", "impatient", "polite"],
            index=2,
            help="Defines personality, tone, and communication style."
        )

        scenario_presets = {
            "Refund Request": "Customer asking for a refund for a defective or unwanted product.",
            "Delayed Order": "Customer whose package has not arrived past guaranteed delivery date.",
            "Payment Failure": "Card charged multiple times or billing mismatch during checkout.",
            "Account Issues": "Customer locked out or unable to access subscription benefits.",
            "Order Cancellation": "Customer wants to immediately cancel an accidental duplicate order.",
            "Custom Scenario": ""
        }

        selected_preset = st.selectbox(
            "Scenario Category:",
            list(scenario_presets.keys()),
            index=1,
        )

        if selected_preset == "Custom Scenario":
            scenario_desc = st.text_area(
                "Custom Scenario Description:",
                value="Customer package is stuck in transit without updates."
            )
        else:
            scenario_desc = st.text_area(
                "Scenario Details:",
                value=scenario_presets[selected_preset]
            )

        initial_emotion = st.selectbox(
            "Initial Emotion:",
            ["neutral", "calm", "confused", "frustrated", "angry", "impatient"],
            index=3,
        )

        issue_severity = st.select_slider(
            "Issue Severity:",
            options=["low", "medium", "high", "critical"],
            value="high",
        )

        initial_patience = st.select_slider(
            "Starting Patience Level:",
            options=["low", "medium", "high"],
            value="medium",
        )

        expected_resolution = st.text_input(
            "Expected Customer Resolution:",
            value="expedited priority shipping or immediate refund"
        )

        st.divider()

        if st.button("🔄 Reset Simulation", use_container_width=True):
            st.session_state.sim_conversation_id = None
            st.session_state.sim_messages = []
            st.session_state.sim_current_emotion = initial_emotion
            st.session_state.sim_patience = initial_patience
            st.rerun()

    # Status Bar
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Customer Persona", persona.title())
    with col2:
        st.metric("Issue Severity", issue_severity.upper())
    with col3:
        st.metric("Current Emotion", st.session_state.sim_current_emotion.title())
    with col4:
        st.metric("Patience Level", st.session_state.sim_patience.title())

    st.markdown("---")

    # Display simulator conversation history
    for msg in st.session_state.sim_messages:
        role = msg["role"]
        with st.chat_message(role, avatar="🧑‍💼" if role == "assistant" else "👤"):
            st.markdown(f"**{'Support Agent' if role == 'assistant' else 'Simulated Customer'}:**")
            st.write(msg["content"])
            if "emotion" in msg:
                st.caption(f"State -> Emotion: *{msg['emotion']}* | Patience: *{msg.get('patience', 'N/A')}*")

    # Agent Input Form
    agent_input = st.chat_input("Type your response to the customer as the Support Agent...")

    if agent_input:
        # 1. Add agent message to UI
        st.session_state.sim_messages.append({
            "role": "assistant",
            "content": agent_input
        })
        with st.chat_message("assistant", avatar="🧑‍💼"):
            st.markdown("**Support Agent:**")
            st.write(agent_input)

        # 2. Call Simulator API
        with st.chat_message("user", avatar="👤"):
            with st.spinner("Customer is typing..."):
                try:
                    payload = {
                        "conversation_id": st.session_state.sim_conversation_id,
                        "agent_message": agent_input,
                        "config": {
                            "persona": persona,
                            "scenario": scenario_desc,
                            "initial_emotion": initial_emotion,
                            "current_emotion": st.session_state.sim_current_emotion,
                            "issue_severity": issue_severity,
                            "patience_level": st.session_state.sim_patience,
                            "expected_resolution": expected_resolution
                        }
                    }

                    res = requests.post(f"{API_URL}/simulator/chat", json=payload, timeout=60)
                    res.raise_for_status()
                    data = res.json()

                    st.session_state.sim_conversation_id = data.get("conversation_id")
                    customer_msg = data.get("customer_message")
                    st.session_state.sim_current_emotion = data.get("current_emotion", st.session_state.sim_current_emotion)
                    st.session_state.sim_patience = data.get("patience_level", st.session_state.sim_patience)

                    st.session_state.sim_messages.append({
                        "role": "user",
                        "content": customer_msg,
                        "emotion": st.session_state.sim_current_emotion,
                        "patience": st.session_state.sim_patience
                    })

                    st.markdown("**Simulated Customer:**")
                    st.write(customer_msg)
                    st.caption(f"State -> Emotion: *{st.session_state.sim_current_emotion}* | Patience: *{st.session_state.sim_patience}*")
                    st.rerun()

                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to FastAPI backend. Ensure Uvicorn is running on port 8000.")
                except Exception as exc:
                    st.error(f"Error generating customer response: {exc}")


# ============================================================
# MODE 2: SUPPORT KNOWLEDGE BASE & RAG (TASK 2)
# ============================================================

else:
    st.title("🤖 Support Knowledge Base RAG Assistant")
    st.caption("Ask questions grounded in indexed company support documents, FAQs, and policies.")

    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []

    with st.sidebar:
        st.header("📄 Knowledge Base Ingestion")
        uploaded_file = st.file_uploader(
            "Upload a support document",
            type=["pdf", "txt", "md"],
            help="Upload PDF, TXT, or Markdown support policies/manuals.",
        )

        if uploaded_file is not None:
            if st.button("⬆️ Upload & Index Document", use_container_width=True):
                with st.spinner("Processing document..."):
                    try:
                        response = requests.post(
                            f"{API_URL}/upload",
                            files={
                                "file": (
                                    uploaded_file.name,
                                    uploaded_file.getvalue(),
                                    uploaded_file.type,
                                )
                            },
                            timeout=120,
                        )
                        response.raise_for_status()
                        data = response.json()
                        st.success("Document indexed successfully!")
                        st.write(f"**Filename:** {data.get('filename')}")
                        st.write(f"**Chunks Stored:** {data.get('chunks', 0)}")
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to FastAPI. Start Uvicorn first.")
                    except Exception as exc:
                        st.error(f"Upload failed: {exc}")

        st.divider()
        st.header("⚙️ Search Settings")
        top_k = st.slider("Knowledge sources to retrieve", min_value=1, max_value=5, value=3)

        if st.button("🗑️ Reset Chat", use_container_width=True):
            st.session_state.conversation_id = None
            st.session_state.messages = []
            st.rerun()

    # Display RAG Chat Messages
    for message in st.session_state.messages:
        role = message["role"]
        with st.chat_message(role):
            st.markdown(message["content"])
            if role == "assistant" and message.get("sources"):
                with st.expander("📚 Retrieved Knowledge Sources"):
                    for i, source in enumerate(message["sources"], start=1):
                        st.markdown(f"**{i}. {source.get('document_name', 'Doc')} (Page {source.get('page_number', 'N/A')})**")
                        st.write(source.get("text", ""))

    user_question = st.chat_input("Ask a question based on your support documents...")
    if user_question:
        st.session_state.messages.append({"role": "user", "content": user_question})
        with st.chat_message("user"):
            st.markdown(user_question)

        with st.chat_message("assistant"):
            with st.spinner("Retrieving sources & generating answer..."):
                try:
                    response = requests.post(
                        f"{API_URL}/chat",
                        json={
                            "conversation_id": st.session_state.conversation_id,
                            "query": user_question,
                            "top_k": top_k,
                        },
                        timeout=180,
                    )
                    response.raise_for_status()
                    data = response.json()
                    st.session_state.conversation_id = data.get("conversation_id")
                    answer = data.get("answer", "No answer returned.")
                    sources = data.get("results", [])

                    st.markdown(answer)
                    if sources:
                        with st.expander("📚 Retrieved Knowledge Sources"):
                            for i, source in enumerate(sources, start=1):
                                st.markdown(f"**{i}. {source.get('document_name')} (Page {source.get('page_number')})**")
                                st.write(source.get("text", ""))

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                    })
                except Exception as exc:
                    st.error(f"RAG query failed: {exc}")