"""
Orchestration logic & Director Gates for the Lead Systems Engineer using LangGraph.
"""
from dotenv import load_dotenv
load_dotenv()

from typing import TypedDict, Annotated, Optional
import operator
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from backend_developer import developer_node
import tools

# --- 1. DEFINE AGENT STATE ---
class AgentState(TypedDict):
    """The central state dictionary that flows through the Sprint Sequence."""
    user_intent: str
    proposed_changes: Optional[str]
    fs_state: str  # 'ro' (Read-Only) or 'rw' (Read-Write)
    director_approval: Optional[bool]
    logs: Optional[str]
    telemetry: Optional[str]
    ncr_reports: Optional[str]

# --- 2. DEFINE CREW NODES ---

def governance_node(state: AgentState) -> dict:
    """Phase 2: Governance Gate (Lead Engineer)"""
    print("\n--- PHASE 2: GOVERNANCE GATE ---")
    print("Reviewing proposed changes from Developer:\n")
    print(state.get("proposed_changes", "No changes proposed."))
    print("--------------------------------")
    
    fs_state = state.get("fs_state", "ro")
    if fs_state == "ro":
        print("[Governance Check] Filesystem is Read-Only. Read-Write Maintenance Window Required.")
        
    # LangGraph will interrupt execution AFTER this node because we set `interrupt_before=["integration"]`.
    return {}

def integration_node(state: AgentState) -> dict:
    """Phase 3: Integration & Test (I&T Engineer)"""
    print("\n--- PHASE 3: DEPLOYMENT ---")
    print("I&T Engineer taking over...")
    
    # In full implementation, we'd extract playbook args from proposed_changes 
    # and call tools.run_ansible_task()
    print("Executing Ansible Playbook...")
    simulated_log = "Ansible executed successfully. rc=0, changed=1."
    
    return {"logs": simulated_log}

def qa_node(state: AgentState) -> dict:
    """Phase 4: Verification (QA Auditor)"""
    print("\n--- PHASE 4: VERIFICATION ---")
    print("QA Auditor checking telemetry against Golden State...")
    
    # In full implementation, we'd call tools.get_pi_telemetry()
    simulated_telemetry = "Telemetry check passed. System matches Golden State."
    
    # Simulate success. If there was a failure, we would set "ncr_reports" to trigger the loop
    return {"telemetry": simulated_telemetry, "ncr_reports": None}

def release_node(state: AgentState) -> dict:
    """Phase 5: Release & Closeout (Lead Engineer)"""
    print("\n--- PHASE 5: RELEASE & CLOSEOUT ---")
    print("Tasking I&T to Freeze Overlay FS (Return to Read-Only)...")
    print("Sprint successful. Notifying Director.")
    return {"fs_state": "ro"}

# --- 3. ROUTING LOGIC ---

def route_post_qa(state: AgentState) -> str:
    """Evaluates the QA Auditor's findings and routes accordingly."""
    if state.get("ncr_reports"):
        print("\n[QA ALERT] Non-Conformance Report generated! Routing back to Developer (Phase 1).")
        return "developer"
    else:
        print("\n[QA PASSED] Golden State confirmed. Proceeding to Release.")
        return "release"

# --- 4. BUILD THE GRAPH ---

builder = StateGraph(AgentState)

# Add Nodes
builder.add_node("developer", developer_node)
builder.add_node("governance", governance_node)
builder.add_node("integration", integration_node)
builder.add_node("qa", qa_node)
builder.add_node("release", release_node)

# Add Edges (The Sprint Sequence)
builder.add_edge(START, "developer")
builder.add_edge("developer", "governance")
# The transition from governance -> integration is the Approval Gate breakpoint.
builder.add_edge("governance", "integration")
builder.add_edge("integration", "qa")
builder.add_conditional_edges(
    "qa", 
    route_post_qa,
    {"developer": "developer", "release": "release"}
)
builder.add_edge("release", END)

# Compile Graph with MemorySaver (Thread persistence)
memory = MemorySaver()
# Interrupt *before* integration node allows Human-In-The-Loop approval
graph = builder.compile(checkpointer=memory, interrupt_before=["integration"])

# --- 5. EXECUTION & CLI ---
if __name__ == "__main__":
    import uuid
    
    # Generate a unique Thread ID for this specific sprint
    # If the Director disapproves, we can simply start a new Thread ID to reset state.
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    print("=== STARTING DIGITAL PICTURE FRAME PROGRAM OFFICE ===")
    initial_intent = "Update the labwc rc.xml configuration to ensure hide_cursor=yes."
    initial_state = {"user_intent": initial_intent, "fs_state": "ro"}
    
    print(f"User Intent: {initial_intent}")
    
    # 1. Run the graph until the HIL breakpoint (Governance Node)
    for event in graph.stream(initial_state, config, stream_mode="values"):
        pass # Node functions handle their own printing
        
    print("\n--- GRAPH EXECUTION PAUSED FOR HIL ---")
    
    # 2. Check if graph is waiting at our breakpoint
    snapshot = graph.get_state(config)
    if snapshot.next and snapshot.next[0] == "integration":
        # Provide Director Approval Tool Interface
        tools.request_director_approval(
            context="Developer has proposed the above changes. Ready for Ansible deployment.", 
            action="Switch to Read-Write mode and Execute Playbook"
        )
        
        # 3. Solicit input from Director
        user_input = input("\nDirector, do you authorize this Maintenance Window? (yes/no): ")
        if user_input.lower().strip() == 'yes':
            print("\n[DIRECTOR APPROVED] Resuming pipeline...")
            # Update state memory to reflect RW switch and approval
            graph.update_state(config, {"director_approval": True, "fs_state": "rw"})
            
            # Resume stream by passing None (uses existing state)
            for event in graph.stream(None, config, stream_mode="values"):
                pass
                
            print("\n=== SPRINT COMPLETE ===")
        else:
            print("\n[DIRECTOR DISAPPROVED] Maintenance Window Denied. Aborting Sprint.")
            print(f"State preserved in Thread ID: {thread_id}. Run a new thread to start over.")
