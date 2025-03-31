# utils/filters.py

def is_signal_message(message_text: str) -> bool:
    """
    Check if the message contains trading signal keywords.
    """
    message_text = message_text.upper()
    keywords = ["BUY", "SELL", "TP", "SL"]
    return any(keyword in message_text for keyword in keywords)
