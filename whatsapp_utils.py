import logging
from flask import current_app, jsonify
import json
import requests
import csv
from twilio.rest import Client

# from app.services.openai_service import generate_response
import re

def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")


def get_text_message_input(recipient, text):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )

def generate_response(response):
    # Return text in uppercase
    if response.lower() == 'wifi':
        return 21522152
    if response.lower() == 'fmb':
        return 'Pick up on Mondays and Thursdays'
    if response.lower() == 'trash':
        return 'Tuesdays'
    else:
        return response.upper()
    

def send_message(data):
    twilio_client = Client(current_app.config['TWILIO_ACCOUNT_SID'], ['TWILIO_AUTH_TOKEN'])
    
    try:
        response = twilio_client.messages.create(
            from_='whatsapp:' + current_app.config['TWILIO_PHONE_NUMBER'],  # Your Twilio WhatsApp number
            body=data,
            to='whatsapp:' + current_app.config['RECIPIENT_WAID'],  # Recipient's WhatsApp number
        )
        print(response.sid)  # Optional: Print the message SID for tracking purposes
    except Exception as e:
        logging.error(f"Failed to send message: {e}")


def process_text_for_whatsapp(text):
    # Remove brackets
    pattern = r"\【.*?\】"
    # Substitute the pattern with an empty string
    text = re.sub(pattern, "", text).strip()

    # Pattern to find double asterisks including the word(s) in between
    pattern = r"\*\*(.*?)\*\*"

    # Replacement pattern with single asterisks
    replacement = r"*\1*"

    # Substitute occurrences of the pattern with the replacement
    whatsapp_style_text = re.sub(pattern, replacement, text)

    return whatsapp_style_text


def process_whatsapp_message(body):
    # Extract relevant information from the webhook body
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

    # Prepare the interactive message JSON
    interactive_message = {
        "interactive": {
            "type": "button",
            "header": {
                "type": "text",
                "text": "Hello, please select an option"
            },
            "body": {
                "text": "Please choose an option:"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "option1",
                            "title": "Option 1"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "option2",
                            "title": "Option 2"
                        }
                    }
                ]
            }
        }
    }

    # Convert the interactive message to JSON string
    interactive_message_json = json.dumps(interactive_message)

    # Write data to CSV file (if needed)
    csv_data = [[wa_id, name, "", ""]]  # Assuming empty message and response for interactive messages

    csv_file_path = 'whatsapp_messages.csv'
    with open(csv_file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(csv_data)

    # Send the interactive message
    send_message(interactive_message_json)
    
def is_valid_whatsapp_message(body):
    """
    Check if the incoming webhook event has a valid WhatsApp message structure.
    """
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )
