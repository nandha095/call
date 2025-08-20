
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from make_call import make_call, hangup_call
# # from sip_call import make_call, hangup_call,create_account

# import threading
# import queue
# from contextlib import asynccontextmanager
# from fastapi.responses import HTMLResponse
# from fastapi.middleware.cors import CORSMiddleware

# # Track the active call number
# active_call = None

# # Shared queue and thread control
# call_queue = queue.Queue()
# stop_event = threading.Event()

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Start worker thread when app starts
#     worker_thread = threading.Thread(target=call_worker, daemon=True)
#     worker_thread.start()
#     yield
#     # Cleanup when app stops
#     stop_event.set()
#     worker_thread.join(timeout=5)

# app = FastAPI(lifespan=lifespan)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # change to ["http://127.0.0.1:5500"] in production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# @app.get("/", response_class=HTMLResponse)
# def serve_html():
#     return """
#     <!DOCTYPE html>
#     <html>
#     <head>
#         <title>SIP Call UI</title>
#     </head>
#     <body>
#         <h2>SIP Call UI</h2>
#         <input type="text" id="number" placeholder="Enter Number">
#         <button onclick="makeCall()">Make Call</button>
#         <button onclick="hangupCall()">Hangup Call</button>
#         <p id="response"></p>

#         <script>
#             async function makeCall() {
#                 const number = document.getElementById("number").value;
#                 const response = await fetch("/make_call", {
#                     method: "POST",
#                     headers: { "Content-Type": "application/json" },
#                     body: JSON.stringify({ number })
#                 });
#                 const result = await response.json();
#                 document.getElementById("response").innerText = JSON.stringify(result);
#             }

#             async function hangupCall() {
#                 const response = await fetch("/hangup_call", {
#                     method: "POST"
#                 });
#                 const result = await response.json();
#                 document.getElementById("response").innerText = JSON.stringify(result);
#             }
#         </script>
#     </body>
#     </html>
#     """

# def call_worker():
#     """Background thread processing call requests indefinitely."""
#     global active_call
#     while not stop_event.is_set():
#         try:
#             number = call_queue.get(timeout=1)
#             make_call(number)
#             active_call = number  # Set as active after starting
#             call_queue.task_done()
#         except queue.Empty:
#             continue

# class CallRequest(BaseModel):
#     number: str

# @app.post("/make_call")
# async def api_make_call(req: CallRequest):
#     try:
#         call_queue.put_nowait(req.number)
#         return {"status": "success", "message": f"Call initiated to {req.number}"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/hangup_call")
# async def api_hangup_call():
#     global active_call
#     if active_call:
#         success = hangup_call(active_call)
#         if success:
#             msg = f"Call with {active_call} ended"
#             active_call = None
#             return {"status": "success", "message": msg}
#     raise HTTPException(status_code=404, detail="No active call found")
# main.py
import subprocess
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from make_call import make_call, hangup_call
from contextlib import asynccontextmanager
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

# This global variable will store the active call process object
active_call_process: subprocess.Popen = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application starting...")
    yield
    print("Application shutting down. Terminating any active calls.")
    global active_call_process
    if active_call_process and active_call_process.poll() is None:
        try:
            # Use the graceful hangup function on shutdown
            hangup_call(active_call_process)
        except Exception as e:
            print(f"Error terminating process on shutdown: {e}")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
def serve_html():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SIP Call UI</title>
        <style>
            body { font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; background-color: #f0f2f5; }
            .container { padding: 2rem; background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); text-align: center; }
            h2 { color: #333; margin-bottom: 1.5rem; }
            input[type="text"] { padding: 0.75rem; border: 1px solid #ccc; border-radius: 8px; font-size: 1rem; margin-right: 0.5rem; width: 200px; }
            button { padding: 0.75rem 1.5rem; border: none; border-radius: 8px; color: white; font-size: 1rem; cursor: pointer; transition: background-color 0.3s; }
            #makeCallBtn { background-color: #4CAF50; }
            #makeCallBtn:hover { background-color: #45a049; }
            #hangupCallBtn { background-color: #f44336; }
            #hangupCallBtn:hover { background-color: #da190b; }
            #response { margin-top: 1.5rem; padding: 1rem; background: #e9ecef; border-radius: 8px; width: 100%; max-width: 400px; word-wrap: break-word; text-align: left; white-space: pre-wrap; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>SIP Call UI</h2>
            <input type="text" id="number" placeholder="Enter Number">
            <button id="makeCallBtn" onclick="makeCall()">Make Call</button>
            <button id="hangupCallBtn" onclick="hangupCall()">Hangup Call</button>
            <p id="response"></p>
        </div>

        <script>
            async function makeCall() {
                const number = document.getElementById("number").value;
                const response = await fetch("/make_call", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ number })
                });
                const result = await response.json();
                document.getElementById("response").innerText = JSON.stringify(result, null, 2);
            }

            async function hangupCall() {
                const response = await fetch("/hangup_call", {
                    method: "POST"
                });
                const result = await response.json();
                document.getElementById("response").innerText = JSON.stringify(result, null, 2);
            }
        </script>
    </body>
    </html>
    """

class CallRequest(BaseModel):
    number: str

@app.post("/make_call")
async def api_make_call(req: CallRequest):
    global active_call_process
    if active_call_process and active_call_process.poll() is None:
        raise HTTPException(status_code=409, detail="A call is already in progress.")
    try:
        active_call_process = make_call(req.number)
        if active_call_process:
            return {"status": "success", "message": f"Call initiated to {req.number}. PID: {active_call_process.pid}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to start call process.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/hangup_call")
async def api_hangup_call():
    global active_call_process
    if not active_call_process:
        raise HTTPException(status_code=404, detail="No active call to hang up.")
    try:
        success = hangup_call(active_call_process)
        if success:
            pid = active_call_process.pid
            active_call_process = None
            return {"status": "success", "message": f"Call (PID {pid}) terminated immediately."}
        else:
            raise HTTPException(status_code=500, detail="Failed to terminate call process.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error hanging up call: {e}")
