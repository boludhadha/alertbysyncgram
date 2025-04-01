import os
from twilio.rest import Client

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "your_account_sid")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "your_auth_token")
TWILIO_CALLER_ID = os.getenv("TWILIO_CALLER_ID", "+1234567890")
STATUS_CALLBACK_URL = os.getenv("TWILIO_STATUS_CALLBACK_URL", "https://yourapp.com/twilio/callback")
SIP_DOMAIN = os.getenv("SIP_DOMAIN", "syncgram.sip.twilio.com")  # New variable

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def initiate_call_with_callback(number, message, retry_count=0):
    """
    Initiates a call with a status callback. Instead of dialing a standard phone number,
    this function dials a SIP URI using the SIP Domain.
    """
    # Construct the SIP URI from the number and SIP_DOMAIN.
    # Example: sip:+2348164603115@syncgram.sip.twilio.com
    sip_uri = f"sip:{number}@{SIP_DOMAIN}"
    
    try:
        call = client.calls.create(
            twiml=f'<Response><Say voice="alice">{message}</Say></Response>',
            to=sip_uri,
            from_=TWILIO_CALLER_ID,
            status_callback=f"{STATUS_CALLBACK_URL}?number={number}&message={message}&retry_count={retry_count}",
            status_callback_event=["initiated", "ringing", "answered", "completed"],
            status_callback_method="POST"
        )
        return call.sid
    except Exception as e:
        print(f"Failed to initiate call to {number} (SIP URI {sip_uri}): {e}")
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
