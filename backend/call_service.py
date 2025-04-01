# backend/call_service.py
import os
from twilio.rest import Client
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_CALLER_ID = os.getenv("TWILIO_CALLER_ID")

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

def broadcast_call(phone_numbers, message, retry_count=0):
    """
    Initiates calls to all phone_numbers with the given message.
    Returns a dictionary mapping each phone number to its call SID.
    """
    call_sids = {}
    for number in phone_numbers:
        call_sid = initiate_call_with_callback(number, message, retry_count)
        call_sids[number] = call_sid
    return call_sids
