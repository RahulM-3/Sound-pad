"""
device_switcher.py
Handles switching the Windows default audio RECORDING device (Microphone) on app open/close.
Uses PowerShell AudioDeviceCmdlets to dynamically grab the correct Device Index.
"""
import subprocess


def _run_ps(cmd: str) -> str:
    try:
        import os
        # Prevent the black command prompt window from flashing inside the PyInstaller GUI
        flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        r = subprocess.run(
            ["powershell", "-Command", cmd],
            capture_output=True, text=True, timeout=8,
            creationflags=flags
        )
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    return ""


def get_current_device_index() -> int | None:
    """Return the Index of the currently active Windows default audio RECORDING device (Microphone)."""
    res = _run_ps("(Get-AudioDevice -Recording).Index")
    if res and res.isdigit():
        return int(res)
    return None


def get_cable_device_index() -> int | None:
    """Find the Index of the Virtual Cable RECORDING device (usually named 'CABLE Output')."""
    # This filters down to the recording device containing 'CABLE'
    res = _run_ps("(Get-AudioDevice -List | Where-Object { $_.Type -eq 'Recording' -and $_.Name -like '*CABLE*' }).Index")
    if res:
        first_line = res.splitlines()[0].strip()
        if first_line.isdigit():
            return int(first_line)
    return None


def set_device_by_index(index: int) -> bool:
    """Switch Windows default device using its exact Index."""
    if index is None:
        return False
    # Set-AudioDevice outputs the newly set device object on success
    res = _run_ps(f"Set-AudioDevice -Index {index}")
    return res != ""
