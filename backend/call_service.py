import os
from urllib.parse import urlencode
from twilio.rest import Client

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "your_account_sid")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "your_auth_token")
TWILIO_CALLER_ID = os.getenv("TWILIO_CALLER_ID", "+1234567890")
STATUS_CALLBACK_URL = os.getenv("TWILIO_STATUS_CALLBACK_URL", "https://alertbysyncgram-production.up.railway.app/twilio/callback")
SIP_DOMAIN = os.getenv("SIP_DOMAIN", "syncgram.sip.twilio.com")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def initiate_call_with_callback(number, message, retry_count=0):
    """
    Initiates a call with a status callback. Builds a fully qualified, URL-encoded callback URL.
    """
    # Construct the SIP URI for outbound dialing.
    sip_uri = f"sip:{number}@{SIP_DOMAIN}"
    
    # Build query parameters and URL-encode them.
    params = urlencode({
        "number": number,
        "message": message,
        "retry_count": retry_count
    })
    
    full_status_callback = f"{STATUS_CALLBACK_URL}?{params}"
    
    try:
        call = client.calls.create(
            twiml=f'<Response><Say voice="alice">{message}</Say></Response>',
            to=sip_uri,
            from_=TWILIO_CALLER_ID,
            status_callback=full_status_callback,
            status_callback_event=["initiated", "ringing", "answered", "completed"],
            status_callback_method="POST"
        )
        return call.sid
    except Exception as e:
        print(f"Failed to initiate call to {number} (SIP URI {sip_uri}): {e}")
        return None
