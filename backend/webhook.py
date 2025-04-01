from fastapi import FastAPI, Request
import logging
from backend.call_service import initiate_call_with_callback

app = FastAPI()
logger = logging.getLogger(__name__)

# Maximum number of retries for a call that fails to complete as desired.
MAX_RETRIES = 3

@app.post("/twilio/callback")
async def twilio_callback(request: Request):
    """
    Handles status callbacks from Twilio.
    If the call status is not 'completed' or 'busy', and if the retry count is below MAX_RETRIES,
    the call is re-initiated immediately.
    """
    # Parse the form data from Twilio's callback
    data = await request.form()
    call_sid = data.get("CallSid")
    call_status = data.get("CallStatus")
    
    # Parse query parameters appended in our call initiation (number, message, retry_count)
    params = request.query_params
    number = params.get("number")
    message = params.get("message")
    try:
        retry_count = int(params.get("retry_count", "0"))
    except ValueError:
        retry_count = 0

    logger.info("Twilio callback received: Call SID %s, Status %s, Number %s, Retry %s",
                call_sid, call_status, number, retry_count)
    
    # Check if the final call status is acceptable.
    # We consider 'completed' or 'busy' as acceptable statuses.
    if call_status not in ["completed", "busy"]:
        if retry_count < MAX_RETRIES:
            new_retry_count = retry_count + 1
            logger.info("Call for %s did not complete successfully (status: %s). Retrying (attempt %s)...",
                        number, call_status, new_retry_count)
            new_call_sid = initiate_call_with_callback(number, message, new_retry_count)
            logger.info("Retried call for %s initiated with new Call SID: %s", number, new_call_sid)
        else:
            logger.info("Max retries reached for %s. Not retrying further.", number)
    else:
        logger.info("Call for %s ended with acceptable status: %s", number, call_status)
    
    return {"status": "ok"}
