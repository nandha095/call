# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from make_call import make_call
# import threading

# app = FastAPI()

# class CallRequest(BaseModel):
#     number: str

# @app.post("/make_call")
# def api_make_call(req: CallRequest):
#     try:
#         # Run call in a separate thread to avoid blocking FastAPI
#         threading.Thread(target=make_call, args=(req.number,), daemon=True).start()

#         return {"status": "success", "message": f"Call started{req}"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from make_call import make_call
import threading
import queue
from contextlib import asynccontextmanager

# Shared queue and thread control
call_queue = queue.Queue()
stop_event = threading.Event()

def call_worker():
    """Background thread processing call requests indefinitely."""
    while not stop_event.is_set():
        try:
            number = call_queue.get(timeout=1)  # Check queue every second
            make_call(number)  # Runs in persistent worker thread
            call_queue.task_done()
        except queue.Empty:
            continue

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start worker thread when app starts
    worker_thread = threading.Thread(target=call_worker, daemon=True)
    worker_thread.start()
    yield
    # Cleanup when app stops
    stop_event.set()
    worker_thread.join(timeout=5)

app = FastAPI(lifespan=lifespan)

class CallRequest(BaseModel):
    number: str

@app.post("/make_call")
async def api_make_call(req: CallRequest):
    try:
        # Add call request to queue (non-blocking)
        call_queue.put_nowait(req.number)
        return {"status": "success", "message": f"Call initiated to {req.number}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))