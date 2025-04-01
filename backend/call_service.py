# backend/call_service.py
import os
import time
from urllib.parse import urlencode
from twilio.rest import Client

# Load configuration from environment variables
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "your_account_sid")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "your_auth_token")
TWILIO_CALLER_ID = os.getenv("TWILIO_CALLER_ID", "+1234567890")
STATUS_CALLBACK_URL = os.getenv("TWILIO_STATUS_CALLBACK_URL", "https://alertbysyncgram-production.up.railway.app/twilio/callback")
SIP_DOMAIN = os.getenv("SIP_DOMAIN", "syncgram.sip.twilio.com")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def initiate_call_with_callback(number, message, retry_count=0):
    """
    Initiates a call via SIP trunking using a SIP URI, with a status callback URL that is
    fully qualified and URL-encoded with query parameters.
    
    :param number: The phone number to call (e.g., +2348164603115)
    :param message: The message to be spoken via TTS
    :param retry_count: The current retry attempt count
    :return: The call SID if successful, otherwise None
    """
    # Construct the SIP URI using the outbound number and SIP_DOMAIN.
    # Example: sip:+2348164603115@syncgram.sip.twilio.com
    sip_uri = f"sip:{number}@{SIP_DOMAIN}"
    
    # Build query parameters for the status callback, and URL-encode them.
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

def broadcast_call(phone_numbers, message, retry_count=0):
    """
    Initiates outbound calls to all provided phone numbers using the SIP trunk.
    Each call includes a status callback URL for tracking.
    
    :param phone_numbers: List of phone numbers (strings)
    :param message: The message to be spoken
    :param retry_count: The starting retry count (default is 0)
    :return: A dictionary mapping each phone number to its call SID (or None if the call failed)
    """
    call_sids = {}
    for number in phone_numbers:
        # Initiate the call for each number via SIP trunking
        call_sid = initiate_call_with_callback(number, message, retry_count)
        call_sids[number] = call_sid
    return call_sids

# Optionally, you can add a retry loop in this module if needed,
# or manage retries from your webhook as described in your callback setup.
# For now, broadcast_call() will be called by your alert processing code,
# and if a call fails, your webhook will handle retry logic.
