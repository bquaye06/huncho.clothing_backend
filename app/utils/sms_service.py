import os
import requests
from dotenv import load_dotenv

load_dotenv()

ARKESEL_API_KEY = os.getenv("ARKESEL_API_KEY")
ARKESEL_SENDER_ID = os.getenv("ARKESEL_SENDER_ID", "Huncho.clothing")

# Normalize the API key loaded from the environment: strip surrounding quotes and whitespace
if ARKESEL_API_KEY:
    # remove accidental surrounding quotes that sometimes appear when env vars are set
    ARKESEL_API_KEY = ARKESEL_API_KEY.strip().strip('"').strip("'")


def send_sms(phone_number, message):
    """
    Send an SMS using Arkesel's API.
    phone_number: in international format (e.g. +233550443601)
    Returns True on success, False on failure.
    """
    if not ARKESEL_API_KEY:
        print("ARKESEL_API_KEY not set. Skipping SMS send.")
        return False

    url = "https://sms.arkesel.com/api/v2/sms/send"

    # Some APIs expect the api-key header as 'api-key' while others expect Authorization Bearer.
    # Include both to increase compatibility; the server will ignore the unused one.
    headers = {
        "api-key": ARKESEL_API_KEY,
        "Authorization": f"Bearer {ARKESEL_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "sender": ARKESEL_SENDER_ID,
        "message": message,
        "recipients": [phone_number],
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
    except requests.exceptions.RequestException as e:
        # Network error / timeout / DNS issue
        print(f"Network error while sending SMS to {phone_number}: {e}")
        return False

    # Detailed response logging to help debugging
    status = response.status_code
    body = None
    try:
        body = response.json()
    except ValueError:
        body = response.text

    if 200 <= status < 300:
        print(f"SMS sent successfully to {phone_number}: status={status}, body={body}")
        return True

    # Non-successful response
    print(f"Error sending SMS to {phone_number}: status={status}, body={body}")
    return False
