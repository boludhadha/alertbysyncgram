# backend/korapay.py
import os
import uuid
import requests

def initiate_korapay_payment(amount: int, subscription_id: int, redirect_url: str, customer_email: str, customer_name: str = "") -> str:
    """
    Initiates a payment with Korapay using the Checkout Standard endpoint.
    
    Parameters:
      amount (int): The amount to charge the customer (in NGN).
      subscription_id (int): Your internal subscription identifier (used for metadata if desired).
      redirect_url (str): The URL to redirect your customer after the transaction.
      customer_email (str): The customer's email address.
      customer_name (str): The customer's name (optional).
      
    Returns:
      str: The checkout_url if successful, otherwise None.
    """
    endpoint = "https://api.korapay.com/merchant/api/v1/charges/initialize"
    secret_key = os.getenv("KORAPAY_SECRET_KEY")
    if not secret_key:
        print("KORAPAY_SECRET_KEY is not set in environment.")
        return None

    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/json"
    }
    
    # Generate a unique transaction reference using UUID
    reference = str(uuid.uuid4())
    
    payload = {
        "amount": amount,
        "currency": "NGN",
        "reference": reference,
        "redirect_url": redirect_url,
        "customer": {
            "email": customer_email,
            "name": customer_name
        },
        # Optionally, add additional parameters as needed:
        # "notification_url": "https://yourdomain.com/webhook",
        # "narration": "AlertsBySyncGram Subscription Payment",
        # "channels": ["bank_transfer", "card"],
        # "default_channel": "bank_transfer",
        # "merchant_bears_cost": True,
        # "metadata": {"subscription_id": subscription_id}
    }
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") is True:
                checkout_url = data.get("data", {}).get("checkout_url")
                return checkout_url
            else:
                print("Korapay API error:", data.get("message"))
                return None
        else:
            print("Error initiating Korapay payment, status code:", response.status_code)
            print(response.text)
            return None
    except Exception as e:
        print("Exception during Korapay payment initiation:", str(e))
        return None

if __name__ == "__main__":
    # For testing purposes only:
    # Set your environment variable KORAPAY_SECRET_KEY before running this test.
    test_payment_url = initiate_korapay_payment(
        amount=1000,
        subscription_id=123,
        redirect_url="https://yourdomain.com/payment_complete",
        customer_email="test@example.com",
        customer_name="Test User"
    )
    print("Test Payment URL:", test_payment_url)
