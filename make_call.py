
import subprocess
import os
import threading
import time
import signal
from dotenv import load_dotenv

# Load SIP credentials from .env
load_dotenv()
SIP_ID = os.getenv("SIP_ID")
SIP_PASS = os.getenv("SIP_PASS")
SIP_DOMAIN = os.getenv("SIP_DOMAIN")
SIP_PORT = os.getenv("SIP_PORT", "5060")

def make_call(destination_number):
    """
    Starts a SIP call using pjsua as a subprocess.
    Returns the subprocess.Popen object.
    """
    timestamp = int(time.time())
    log_filename = f"call_{destination_number}_{timestamp}.log"
    
    cmd = [
        "pjsua",
        "--id", f"sip:{SIP_ID}@{SIP_DOMAIN}",
        "--registrar", f"sip:{SIP_DOMAIN}",
        "--realm", "*",
        "--username", SIP_ID,
        "--password", SIP_PASS,
        "--local-port", "0",
        "--log-level", "0",
        "--auto-answer", "200",
        f"sip:{destination_number}@{SIP_DOMAIN}"
    ]

    try:
        # Open a log file to capture stdout/stderr from the process
        log_file = open(log_filename, "w")
        
        # Start the subprocess and return the process object
        process = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            text=True
        )
        print(f"Call process started. PID: {process.pid} Log: {log_filename}")
        return process
        
    except Exception as e:
        print(f"Error starting call: {str(e)}")
        # Close the log file if an error occurs
        if 'log_file' in locals():
            log_file.close()
        return None

def hangup_call(process):
    """
    Attempts to gracefully hang up an active SIP call by sending 'h\n' to its stdin.
    If that fails, it sends a SIGINT signal. Finally, it forcefully terminates the process.
    """
    if not process or process.poll() is not None:
        print("No active process to hang up or process is already terminated.")
        return False
    
    try:
        # Step 1: Attempt to write 'h' to the stdin for a graceful hangup
        process.stdin.write('h\n')
        process.stdin.flush()
        print("Attempted graceful hangup via stdin.")

        # Give the process a moment to respond and exit gracefully
        try:
            process.wait(timeout=2)
            if process.poll() is not None:
                print("Process terminated gracefully after stdin command.")
                return True
        except subprocess.TimeoutExpired:
            pass # Process is still running, proceed to next step
        
        # Step 2: Send a SIGINT signal as a fallback
        process.send_signal(signal.SIGINT)
        print("Attempted hangup via SIGINT signal.")

        # Give the process a moment to respond and exit
        try:
            process.wait(timeout=2)
            if process.poll() is not None:
                print("Process terminated gracefully after SIGINT.")
                return True
        except subprocess.TimeoutExpired:
            pass # Process is still running, proceed to final step
        
        # Step 3: Final fallback, kill the process
        process.kill()
        print("Final fallback: Forceful kill.")
        process.wait(timeout=5)
        
        if process.poll() is not None:
            print(f"Call process (PID {process.pid}) terminated.")
            return True
        else:
            print("Failed to terminate process.")
            return False

    except Exception as e:
        print(f"Error during hangup sequence: {e}")
        # Final desperate attempt to kill the process
        try:
            process.kill()
            return True
        except:
            return False

# You can keep the zombie cleanup thread, but it's less critical with this approach
def cleanup_zombies():
    while True:
        try:
            os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            pass
        time.sleep(60)

cleanup_thread = threading.Thread(target=cleanup_zombies, daemon=True)
cleanup_thread.start()
