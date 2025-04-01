# backend/webhook.py
from fastapi import FastAPI, Request
import logging
from backend.call_service import initiate_call_with_callback

app = FastAPI()
logger = logging.getLogger(__name__)

# Maximum number of retries for a call that doesn't complete as desired.
MAX_RETRIES = 3

@app.post("/twilio/callback")
async def twilio_callback(request: Request):
    # Parse form data from Twilio's callback.
    data = await request.form()
    call_sid = data.get("CallSid")
    call_status = data.get("CallStatus")
    
    # Parse query parameters from the callback URL.
    params = request.query_params
    number = params.get("number")
    message = params.get("message")
    retry_count = int(params.get("retry_count", "0"))
    
    logger.info("Twilio callback received: Call SID %s, Status %s, Number %s, Retry %s",
                call_sid, call_status, number, retry_count)
    
    # Check final call status.
    # If the status is not 'completed' or 'busy', and we haven't exceeded max retries, attempt a retry.
    if call_status not in ["completed", "busy"]:
        if retry_count < MAX_RETRIES:
            logger.info("Call for %s did not complete successfully (status: %s). Retrying (attempt %s)...", 
                        number, call_status, retry_count + 1)
            new_retry_count = retry_count + 1
            new_call_sid = initiate_call_with_callback(number, message, new_retry_count)
            logger.info("Retried call for %s initiated with new Call SID: %s", number, new_call_sid)
        else:
            logger.info("Max retries reached for %s. Not retrying further.", number)
    else:
        logger.info("Call for %s ended with acceptable status: %s", number, call_status)
    
    return {"status": "ok"}
