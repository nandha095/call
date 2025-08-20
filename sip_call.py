import pjsua as pj
import threading

# Global library and account
lib = pj.Lib()
acc = None
current_call = None

def start_lib():
    global lib
    lib.init()
    transport = lib.create_transport(pj.TransportType.UDP)
    lib.start()

def create_account(sip_domain, sip_id, sip_pass):
    global acc
    acc_cfg = pj.AccountConfig(domain=sip_domain, username=sip_id, password=sip_pass)
    acc = lib.create_account(acc_cfg)

def make_call(destination_number):
    global current_call
    if acc is None:
        raise Exception("SIP account not initialized")
    
    sip_uri = f"sip:{destination_number}@{acc.info().uri.split('@')[1]}"
    current_call = acc.make_call(sip_uri)
    return f"Calling {destination_number}..."

def hangup_call():
    global current_call
    if current_call:
        current_call.hangup()  # This sends SIP BYE immediately
        current_call = None
        return "Call hung up instantly"
    else:
        return "No active call"
