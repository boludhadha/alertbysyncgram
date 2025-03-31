# backend/call_service.py
import os
from twilio.rest import Client
from dotenv import load_dotenv
load_dotenv()
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "your_account_sid")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "your_auth_token")
TWILIO_CALLER_ID = os.getenv("TWILIO_CALLER_ID", "+1234567890")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def initiate_call(to_phone: str, message: str) -> str:
    """
    Initiate a voice call using Twilio with text-to-speech.
    Returns the call SID if successful; otherwise, returns None.
    """
    try:
        call = client.calls.create(
            twiml=f'<Response><Say voice="alice">{message}</Say></Response>',
            to=to_phone,
            from_=TWILIO_CALLER_ID
        )
        return call.sid
    except Exception as e:
        print(f"Failed to initiate call to {to_phone}: {e}")
        return None
