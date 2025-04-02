# backend/paystack.py
import os
import uuid
import requests

def initiate_paystack_payment(amount: int, subscription_id: int, callback_url: str, customer_email: str, customer_name: str = "") -> str:
    """
    Initiates a payment with Paystack and returns the payment authorization URL.
    
    Parameters:
      amount (int): The amount to charge the customer in NGN. (Converted to kobo internally)
      subscription_id (int): Your internal subscription ID (for metadata if desired).
      callback_url (str): The URL to redirect the customer after the transaction.
      customer_email (str): The customer's email address.
      customer_name (str): The customer's name (optional).
      
    Returns:
      str: The authorization URL (payment URL) if successful, otherwise None.
    """
    endpoint = "https://api.paystack.co/transaction/initialize"
    secret_key = os.getenv("PAYSTACK_SECRET_KEY")
    if not secret_key:
        print("PAYSTACK_SECRET_KEY is not set in environment.")
        return None

    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/json"
    }
    
    # Generate a unique transaction reference.
    reference = str(uuid.uuid4())
    
    # Paystack expects the amount in kobo (i.e., NGN * 100).
    payload = {
        "amount": amount * 100,  # Convert NGN to kobo.
        "email": customer_email,
        "reference": reference,
        "callback_url": callback_url,
        "currency": "NGN",
        "channels": ["card", "bank_transfer", "ussd"],
        "customer": {
            "name": customer_name,
            "email": customer_email
        }
    }
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") is True:
                authorization_url = data.get("data", {}).get("authorization_url")
                return authorization_url
            else:
                print("Paystack API error:", data.get("message"))
                return None
        else:
            print("Error initiating Paystack payment, status code:", response.status_code)
            print(response.text)
            return None
    except Exception as e:
        print("Exception during Paystack payment initiation:", str(e))
        return None

if __name__ == "__main__":
    # Test the Paystack integration independently.
    # Ensure your environment variable PAYSTACK_SECRET_KEY is set before running this test.
    test_payment_url = initiate_paystack_payment(
        amount=1000,
        subscription_id=123,
        callback_url="https://yourdomain.com/payment_complete",
        customer_email="test@example.com",
        customer_name="Test User"
    )
    print("Test Payment URL:", test_payment_url)
