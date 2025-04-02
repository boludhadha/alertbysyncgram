# backend/korapay.py
import os
import requests

def initiate_korapay_payment(amount, subscription_id, redirect_url):
    """
    Initiates a payment with Korapay and returns a payment link.
    
    :param amount: Payment amount (e.g., 1000 for ₦1000)
    :param subscription_id: The subscription ID to associate with this payment
    :param redirect_url: URL to redirect the user after payment completion
    :return: Payment URL as a string if successful, otherwise None.
    """
    # Replace this endpoint with the correct one from Korapay's documentation.
    endpoint = "https://api.korapay.com/api/v1/payment"  
    
    headers = {
        "Authorization": f"Bearer {os.getenv('KORAPAY_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "amount": amount,
        "currency": "NGN",
        "redirect_url": redirect_url,
        "subscription_id": subscription_id,
        "description": "AlertsBySyncGram Subscription Payment"
    }
    
    response = requests.post(endpoint, json=payload, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        payment_url = result.get("payment_url")
        return payment_url
    else:
        print("Error initiating Korapay payment:", response.text)
        return None
