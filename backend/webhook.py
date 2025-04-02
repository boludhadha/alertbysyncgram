# backend/webhook.py
from fastapi import FastAPI, Request, Response
import logging
from backend.call_service import initiate_call_with_callback

app = FastAPI()
logger = logging.getLogger(__name__)

MAX_RETRIES = 3

@app.post("/twilio/callback")
async def twilio_callback(request: Request) -> Response:
    try:
        # Parse form data from Twilio's callback.
        data = await request.form()
        call_sid = data.get("CallSid")
        call_status = data.get("CallStatus")
        
        # Parse query parameters from the callback URL.
        params = request.query_params
        number = params.get("number")
        message = params.get("message")
        try:
            retry_count = int(params.get("retry_count", "0"))
        except ValueError:
            retry_count = 0

        logger.info("Twilio callback received: Call SID %s, Status %s, Number %s, Retry %s",
                    call_sid, call_status, number, retry_count)
        
        # If final status is not acceptable, retry if within MAX_RETRIES.
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
    except Exception as e:
        logger.exception("Error processing Twilio callback: %s", e)
        # Even if there's an error, we must return a successful HTTP response to Twilio.
    # Return a 204 No Content response to indicate success without any body.
    return Response(status_code=204)
