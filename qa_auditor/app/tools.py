import subprocess

def get_pi_telemetry(target_ip: str) -> str:
    """
    Captures the current hardware and software state of the Pi.
    Returns:
    - Input Handlers (cat /proc/bus/input/devices)
    - Active Processes (pgrep -af mpv)
    - Filesystem State (mount | grep 'on / ')
    """
    cmd = ("cat /proc/bus/input/devices; "
           "echo '---'; pgrep -af mpv; "
           "echo '---'; mount | grep 'on / '")
    
    result = subprocess.run(
        ["ssh", f"kmercer5@{target_ip}", cmd],
        capture_output=True, text=True
    )
    return result.stdout
