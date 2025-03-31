# backend/webhook.py
from fastapi import FastAPI, Request
from db.database import SessionLocal
from models.call_log import CallLog

app = FastAPI()

@app.post("/twilio/webhook")
async def twilio_webhook(request: Request):
    """
    Endpoint to receive call status updates from Twilio.
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    call_status = form_data.get("CallStatus")
    print(f"Webhook received: Call SID {call_sid} with status {call_status}")
    
    # (Optional) Update the corresponding call log.
    db = SessionLocal()
    call_log = db.query(CallLog).filter(CallLog.details == call_sid).first()
    if call_log:
        call_log.status = call_status
        db.commit()
    db.close()
    
    return {"status": "ok"}
