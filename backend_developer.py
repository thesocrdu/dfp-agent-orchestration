"""
Agent logic for the Backend Developer.
"""
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from crew_configs import BACKEND_DEVELOPER_INSTRUCTION

def developer_node(state: dict) -> dict:
    """
    Phase 1: LangGraph node for the Backend Developer.
    Generates proposed changes (Ansible/Lua/Config) based on user intent and any NCRs.
    Operates completely sandboxed.
    """
    print("\n--- PHASE 1: DEVELOPER HANDOFF ---")
    print("Backend Developer generating code based on intent...")
    
    # Using Vertex AI Gemini 1.5 Flash as requested for the developer
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.1)
    
    intent = state.get("user_intent", "")
    ncr_reports = state.get("ncr_reports", "")
    
    prompt = f"Target Intent: {intent}\n"
    if ncr_reports:
        prompt += f"Non-Conformance Reports to Address:\n{ncr_reports}\n"
        
    messages = [
        SystemMessage(content=BACKEND_DEVELOPER_INSTRUCTION),
        HumanMessage(content=prompt)
    ]
    
    # Invoke the model
    response = model.invoke(messages)
    
    # The developer returns the proposed changes
    return {"proposed_changes": response.content}
