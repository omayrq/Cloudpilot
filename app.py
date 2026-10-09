"""
CloudPilot — Streamlit Web Application Interface
Your AWS Cost, Architecture, and Deployment Copilot
"""

import sys
import os

# Add cloudpilot directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from agent import ask_bedrock
from safety import create_change_proposal, validate_approval
from tools import plan_architecture, troubleshoot_pipeline

# Page Setup
st.set_page_config(
    page_title="CloudPilot — AWS Cost & Deployment Copilot",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ff9900 0%, #ff5500 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #9ca3af;
        margin-bottom: 1.5rem;
    }
    .stCard {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }
    .risk-high {
        color: #ef4444;
        font-weight: 700;
    }
    .risk-medium {
        color: #f59e0b;
        font-weight: 600;
    }
    .risk-low {
        color: #10b981;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []

if "proposals" not in st.session_state:
    st.session_state.proposals = {}

# Sidebar Configuration
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/9/93/Amazon_Web_Services_Logo.svg", width=120)
    st.markdown("### ☁️ CloudPilot Control Panel")
    
    selected_mode = st.radio(
        "Select Operation Mode:",
        ["🏗️ Architecture & Cost Planner", "🛠️ Pipeline Troubleshooter", "🛡️ Change Review & Approval"],
        index=0
    )

    st.divider()

    st.markdown("**AWS Environment Context:**")
    st.info(f"Region: `us-east-1`\n\nBedrock Model: `amazon.nova-lite-v1:0`\n\nStatus: 🟢 Connected")

    st.divider()
    if st.button("🧹 Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.proposals = {}
        st.rerun()

# Map Mode Name
if "Architecture" in selected_mode:
    active_mode = "architecture"
elif "Troubleshooter" in selected_mode:
    active_mode = "troubleshooter"
else:
    active_mode = "change_review"

# Main Interface Header
st.markdown("<div class='main-header'>CloudPilot — AWS Cost & Deployment Copilot</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Plan AWS architectures, estimate service cost drivers, troubleshoot deployment logs, and review infrastructure changes securely.</div>", unsafe_allow_html=True)

# Welcome First-Run Message
if not st.session_state.messages:
    welcome_text = (
        "Hi, I'm **CloudPilot**. I can help you plan AWS architectures, understand cost drivers, "
        "and troubleshoot deployment errors. I'll explain my recommendations and keep infrastructure "
        "changes under your control. What are you trying to build?"
    )
    st.session_state.messages.append({"role": "assistant", "content": welcome_text, "card": None})

# Prompt Suggestions
st.markdown("**💡 Example Quick Prompts:**")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🏗️ Plan a low-cost web app on AWS", use_container_width=True):
        st.session_state.user_prompt_input = "Plan a low-cost web application on AWS."
with col2:
    if st.button("🛠️ Explain CodeBuild Docker 429 error", use_container_width=True):
        st.session_state.user_prompt_input = "Explain this CodeBuild error: 429 Too Many Requests - toomanyrequests: You have reached your pull rate limit."
with col3:
    if st.button("🛡️ Review risks of resizing EC2 instance", use_container_width=True):
        st.session_state.user_prompt_input = "Review the risks of resizing an EC2 instance from t3.micro to t3.2xlarge."

# Render Chat History
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        # Render Structured Action Card if present
        if msg.get("card"):
            card = msg["card"]
            
            with st.expander(f"📋 Action Card: {card.get('summary', 'Details')}", expanded=True):
                # Mode Badge
                st.caption(f"Mode: **{card.get('mode', 'general').upper()}** | Execution Status: **{card.get('execution_status', 'not_executed').upper()}**")

                # Recommendations
                if card.get("recommendations"):
                    st.markdown("#### 💡 Recommendations")
                    for rec in card["recommendations"]:
                        st.markdown(f"- {rec}")

                # Cost Drivers
                if card.get("cost_drivers"):
                    st.markdown("#### 💰 Key Cost Drivers")
                    for cd in card["cost_drivers"]:
                        st.markdown(f"- 💵 {cd}")

                # Assumptions
                if card.get("assumptions"):
                    st.markdown("#### 📌 Assumptions & Scope")
                    for asm in card["assumptions"]:
                        st.markdown(f"- ℹ️ {asm}")

                # Risks
                if card.get("risks"):
                    st.markdown("#### ⚠️ Risks & Warnings")
                    for rk in card["risks"]:
                        st.markdown(f"- <span class='risk-high'>{rk}</span>", unsafe_allow_html=True)

                # Next Steps
                if card.get("next_steps"):
                    st.markdown("#### 🚀 Actionable Next Steps")
                    for ns in card["next_steps"]:
                        st.markdown(f"- 🎯 {ns}")

                # Change Approval Workflow Buttons (For Change Review Proposals)
                if card.get("mode") == "change_review" and card.get("execution_status") == "not_executed":
                    st.divider()
                    st.markdown("**🛡️ Human Approval Guardrail:**")
                    btn_col1, btn_col2 = st.columns(2)
                    
                    with btn_col1:
                        if st.button("✅ Approve Proposal", key=f"approve_{idx}", type="primary"):
                            updated_card = validate_approval(card, "approved")
                            msg["card"] = updated_card
                            msg["content"] = f"✅ Proposal Approved: {card.get('summary')}"
                            st.success("Proposal approved by human reviewer. Decision recorded.")
                            st.rerun()

                    with btn_col2:
                        if st.button("❌ Reject Proposal", key=f"reject_{idx}"):
                            updated_card = validate_approval(card, "rejected")
                            msg["card"] = updated_card
                            msg["content"] = f"❌ Proposal Rejected: {card.get('summary')}"
                            st.warning("Proposal rejected. No infrastructure changes will be performed.")
                            st.rerun()

# User Input Box
user_query = st.chat_input("Ask CloudPilot about AWS architecture, costs, or deployment errors...")

# Handle Button Input if Clicked
if "user_prompt_input" in st.session_state and st.session_state.user_prompt_input:
    user_query = st.session_state.user_prompt_input
    del st.session_state.user_prompt_input

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query, "card": None})
    
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        with st.spinner("CloudPilot is analyzing request via Amazon Bedrock Converse API..."):
            try:
                card_response = ask_bedrock(user_query, mode=active_mode)
                summary = card_response.get("summary", "Analysis completed.")
                
                st.markdown(f"### 🎯 CloudPilot Analysis\n{summary}")
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"### 🎯 CloudPilot Analysis\n{summary}",
                    "card": card_response
                })
                st.rerun()
            except Exception as e:
                st.error(f"Error querying CloudPilot agent: {e}")
