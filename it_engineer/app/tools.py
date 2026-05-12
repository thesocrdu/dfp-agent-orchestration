import asyncio
from typing import Optional, Dict
from kasa import SmartPlug
try:
    import ansible_runner
except ImportError:
    ansible_runner = None

def run_ansible_task(playbook: str, target_host: str, extra_vars: Optional[Dict] = None) -> dict:
    """
    Executes a pre-defined Ansible playbook against the Raspberry Pi.
    Use this for: Configuring kiosk mode, hiding cursors, or updating system state.
    Constraints: Only call if system is authorized for Read-Write mode or for non-persistent checks.
    """
    if ansible_runner is None:
        return {
            "status": "error",
            "rc": 1,
            "stdout": "Ansible Runner is not supported on this operating system (Windows)."
        }
        
    r = ansible_runner.run(
        private_data_dir='./ansible',
        playbook=f"{playbook}.yml",
        extravars=extra_vars or {},
        host_pattern=target_host
    )
    
    stdout_content = ""
    if r.stdout:
        try:
            stdout_content = r.stdout.read()[-1000:]
        except Exception:
            pass
            
    return {
        "status": r.status,
        "rc": r.rc,
        "stdout": stdout_content
    }

def kasa_power_cycle(alias: str, delay_seconds: int = 10) -> str:
    """
    Physically cycles the power of the Smart Plug.
    Safety Logic: This is a last resort 'Hard Reset'. 
    Rules: Must check if Overlay FS is Read-Only before use to prevent corruption.
    """
    async def toggle():
        plug = SmartPlug(alias)
        await plug.update()
        await plug.turn_off()
        await asyncio.sleep(delay_seconds)
        await plug.turn_on()
        return f"Power cycle of {alias} completed."
    
    return asyncio.run(toggle())
