# backend/webhook.py
from fastapi import FastAPI, Request, Response
import logging
from backend.call_service import initiate_conference_call_with_callback

app = FastAPI()
logger = logging.getLogger(__name__)

MAX_RETRIES = 3

@app.post("/twilio/callback")
async def twilio_callback(request: Request) -> Response:
    try:
        data = await request.form()
        call_sid = data.get("CallSid")
        call_status = data.get("CallStatus")
        
        params = request.query_params
        number = params.get("number")
        conference_room = params.get("conference_room")
        message = params.get("message")
        try:
            retry_count = int(params.get("retry_count", "0"))
        except ValueError:
            retry_count = 0
        
        logger.info("Twilio callback: Call SID %s, Status %s, Number %s, Conference %s, Retry %s",
                    call_sid, call_status, number, conference_room, retry_count)
                    
        if call_status not in ["completed", "busy"]:
            if retry_count < MAX_RETRIES:
                new_retry_count = retry_count + 1
                logger.info("Call for %s in conference %s failed (status: %s). Retrying (attempt %s)...",
                            number, conference_room, call_status, new_retry_count)
                new_call_sid = initiate_conference_call_with_callback(number, conference_room, message=message, retry_count=new_retry_count)
                logger.info("Retried call for %s with new Call SID: %s", number, new_call_sid)
            else:
                logger.info("Max retries reached for %s. No further retry.", number)
        else:
            logger.info("Call for %s ended with acceptable status: %s", number, call_status)
    except Exception as e:
        logger.exception("Error in Twilio callback: %s", e)
    return Response(status_code=204)
