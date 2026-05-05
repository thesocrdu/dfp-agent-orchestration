import subprocess
import json
import asyncio
from typing import Optional, Dict
from kasa import SmartPlug  # Requirement: pip install python-kasa
import ansible_runner       # Requirement: pip install ansible-runner
from langchain_core.tools import tool

# --- INFRASTRUCTURE TOOLS (Primary: I&T Engineer) ---

@tool
def run_ansible_task(playbook: str, target_host: str, extra_vars: Optional[Dict] = None):
    """
    Executes a pre-defined Ansible playbook against the Raspberry Pi.
    Use this for: Configuring kiosk mode, hiding cursors, or updating system state.
    Constraints: Only call if system is authorized for Read-Write mode or for non-persistent checks.
    """
    # Using ansible-runner for a clean agentic interface
    r = ansible_runner.run(
        private_data_dir='./ansible',
        playbook=f"{playbook}.yml",
        extravars=extra_vars or {},
        host_pattern=target_host
    )
    
    # Read stdout safely
    stdout_content = ""
    if r.stdout:
        try:
            stdout_content = r.stdout.read()[-1000:]
        except Exception:
            pass
            
    return {
        "status": r.status,
        "rc": r.rc,
        "stdout": stdout_content # Return last 1000 chars for context
    }

@tool
def kasa_power_cycle(alias: str, delay_seconds: int = 10):
    """
    Physically cycles the power of the Smart Plug.
    Safety Logic: This is a last resort 'Hard Reset'. 
    Rules: Must check if Overlay FS is Read-Only before use to prevent corruption.
    """
    async def toggle():
        # Discover and connect to the plug by alias (e.g., 'Mom-Frame-Plug')
        plug = SmartPlug(alias)
        await plug.update()
        await plug.turn_off()
        await asyncio.sleep(delay_seconds)
        await plug.turn_on()
        return f"Power cycle of {alias} completed."
    
    return asyncio.run(toggle())

# --- TELEMETRY TOOLS (Primary: QA Auditor) ---

@tool
def get_pi_telemetry(target_ip: str):
    """
    Captures the current hardware and software state of the Pi.
    Returns:
    - Input Handlers (cat /proc/bus/input/devices)
    - Active Processes (pgrep -af mpv)
    - Filesystem State (mount | grep 'on / ')
    """
    # This tool uses SSH to gather the ground truth
    cmd = ("cat /proc/bus/input/devices; "
           "echo '---'; pgrep -af mpv; "
           "echo '---'; mount | grep 'on / '")
    
    result = subprocess.run(
        ["ssh", f"kmercer5@{target_ip}", cmd],
        capture_output=True, text=True
    )
    return result.stdout

# --- DIRECTOR TOOLS (Primary: Lead Engineer) ---

@tool
def request_director_approval(context: str, action: str):
    """
    PAUSE EXECUTION. Sends a formal request to the Director (Kyle) for authorization.
    Use this for: Read-Write mode switches or non-standard power cycles.
    """
    # This tool creates a human-in-the-loop gate
    print(f"\n[GOVERNANCE GATE] Requesting Approval for: {action}")
    print(f"Context: {context}")
    return "GATE_OPENED: Provide this string to the agent once approval is manually verified."
