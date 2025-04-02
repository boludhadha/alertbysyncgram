import os
from urllib.parse import urlencode
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Dial

# Load configuration from environment variables.
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_CALLER_ID = os.getenv("TWILIO_CALLER_ID")
STATUS_CALLBACK_URL = os.getenv("TWILIO_STATUS_CALLBACK_URL")  # Must be fully qualified (e.g., https://yourdomain.com/twilio/callback)
DEFAULT_CONFERENCE = os.getenv("DEFAULT_CONFERENCE", "AlertConferenceRoom")
TWILIO_WAIT_URL = os.getenv("TWILIO_WAIT_URL", None)  # Optional wait URL (e.g., an MP3 file)

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def create_conference_twiml(conference_room, wait_url=None):
    """
    Generates TwiML that dials into a conference room.
    If a wait_url is provided, it plays audio while waiting for participants.
    """
    response = VoiceResponse()
    dial = Dial()
    if wait_url:
        dial.conference(conference_room, wait_url=wait_url, start_conference_on_enter=True, end_conference_on_exit=True)
    else:
        dial.conference(conference_room, start_conference_on_enter=True, end_conference_on_exit=True)
    response.append(dial)
    return str(response)

def initiate_conference_call_with_callback(number, conference_room=DEFAULT_CONFERENCE, wait_url=TWILIO_WAIT_URL, message="", retry_count=0):
    """
    Initiates an outbound call that joins the specified conference room.
    Constructs a fully qualified, URL-encoded status callback URL with query parameters.
    """
    # Generate the TwiML that instructs the call to join the conference.
    twiml = create_conference_twiml(conference_room, wait_url)
    
    # Build URL-encoded query parameters for the status callback.
    params = urlencode({
        "number": number,
        "conference_room": conference_room,
        "message": message,
        "retry_count": retry_count
    })
    full_status_callback = f"{STATUS_CALLBACK_URL}?{params}"
    
    try:
        call = client.calls.create(
            twiml=twiml,
            to=number,  # Ensure number is in E.164 format.
            from_=TWILIO_CALLER_ID,
            status_callback=full_status_callback,
            status_callback_event=["initiated", "ringing", "answered", "completed"],
            status_callback_method="POST"
        )
        return call.sid
    except Exception as e:
        print(f"Failed to initiate conference call to {number}: {e}")
        return None

def broadcast_conference_call(phone_numbers, conference_room=DEFAULT_CONFERENCE, wait_url=TWILIO_WAIT_URL, message=""):
    """
    Initiates outbound calls to all provided phone numbers.
    Each call connects the recipient to the same conference room.
    Returns a dictionary mapping each phone number to its call SID (or None if failed).
    """
    call_sids = {}
    for number in phone_numbers:
        sid = initiate_conference_call_with_callback(number, conference_room, wait_url, message, retry_count=0)
        call_sids[number] = sid
    return call_sids
