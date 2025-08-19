
import subprocess
import os
import threading
import tim
from dotenv import load_dotenv

# Load SIP credentials from .env
load_dotenv()
SIP_ID = os.getenv("SIP_ID")
SIP_PASS = os.getenv("SIP_PASS")
SIP_DOMAIN = os.getenv("SIP_DOMAIN")
SIP_PORT = os.getenv("SIP_PORT", "5060")

def make_call(destination_number):
    """
    Starts a SIP call using pjsua with dummy audio (for WSL2 testing).
    Uses random port assignment and manages process lifecycle.
    """
    # Generate unique log file name
    timestamp = int(time.time())
    log_filename = f"call_{destination_number}_{timestamp}.log"
    
    cmd = [
        "pjsua",
        "--id", f"sip:{SIP_ID}@{SIP_DOMAIN}",
        "--registrar", f"sip:{SIP_DOMAIN}",
        "--realm", "*",
        "--username", SIP_ID,
        "--password", SIP_PASS,
        "--local-port", "0",  # Let OS choose free port
        # "--null-audio",
        "--log-level", "0",   # Reduce log verbosity
        "--auto-answer", "200",
        f"sip:{destination_number}@{SIP_DOMAIN}"
    ]

    try:
        with open(log_filename, "w") as log_file:
            process = subprocess.Popen(
                cmd,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True
            )
        print(f"Call process started. PID: {process.pid} Log: {log_filename}")
        
        # Return immediately without waiting
        return process.pid
        
    except Exception as e:
        print(f"Error starting call: {str(e)}")
        return None

# Optional: Add a cleanup thread for zombie processes
def cleanup_zombies():
    """Periodically reap completed child processes"""
    while True:
        try:
            os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            pass
        time.sleep(60)

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_zombies, daemon=True)
cleanup_thread.start()
