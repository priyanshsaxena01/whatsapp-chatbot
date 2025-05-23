import os
import json
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load credentials and configuration from environment variables
ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")

# Basic in-memory store for user sessions/states.
user_sessions = {}

@app.route('/')
def home():
    return "Cityscope WhatsApp Chatbot is alive!"

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        if request.args.get('hub.mode') == 'subscribe' and request.args.get('hub.verify_token') == VERIFY_TOKEN:
            app.logger.info("Webhook verified successfully!")
            return request.args.get('hub.challenge'), 200
        else:
            app.logger.error("Webhook verification failed.")
            return 'Verification token mismatch', 403
    
    elif request.method == 'POST':
        app.logger.info("<<<<<<<<<< RECEIVED POST REQUEST TO WEBHOOK >>>>>>>>>>")
        data = request.get_json()
        app.logger.info(f"Incoming POST data: {json.dumps(data, indent=2)}")

        if data.get('object') == 'whatsapp_business_account':
            for entry in data.get('entry', []):
                for change in entry.get('changes', []):
                    if change.get('field') == 'messages':
                        value = change.get('value', {})
                        if value.get('messages'):
                            message_data = value['messages'][0]
                            sender_id = message_data['from']
                            
                            app.logger.info(f"Processing message from: {sender_id}")
                            mark_message_as_read(message_data['id'])
                            process_user_message(sender_id, message_data)
                        else:
                            app.logger.warning("No 'messages' array in value object.")
                    else:
                        app.logger.info(f"Received change for field: {change.get('field')}, not 'messages'.")
            return 'OK', 200
        else:
            app.logger.warning(f"Received POST object is not 'whatsapp_business_account': {data.get('object')}")
            return 'OK', 200
    
    return 'Method Not Allowed', 405

def process_user_message(sender_id, message_data):
    message_type = message_data.get('type')
    user_state = user_sessions.get(sender_id, {}).get('state', 'GREETING')
    app.logger.info(f"User {sender_id} is in state: {user_state}")

    if message_type == 'text':
        text_body = message_data['text']['body'].lower().strip()
        
        if text_body in ['hi', 'hello', 'menu', 'start', 'hey', 'cityscope']:
            send_cityscope_greeting(sender_id)
        elif text_body == 'help':
            send_cityscope_help_message(sender_id)
            send_cityscope_greeting(sender_id) # Offer main menu again
        else:
            handle_unexpected_input(sender_id, user_state)

    elif message_type == 'interactive':
        interactive_data = message_data['interactive']
        interactive_type = interactive_data['type']

        if interactive_type == 'button_reply':
            button_id = interactive_data['button_reply']['id']
            handle_cityscope_button_reply(sender_id, button_id)
        elif interactive_type == 'list_reply':
            # Example: If we add lists for exploring categories
            list_id = interactive_data['list_reply']['id']
            list_title = interactive_data['list_reply']['title']
            handle_cityscope_list_reply(sender_id, list_id, list_title)
        else:
            send_unknown_input_response(sender_id)
            send_cityscope_greeting(sender_id)
            # Ensure state is managed after sending greeting
            user_sessions[sender_id] = {'state': 'AWAITING_MAIN_CHOICE'}
    else:
        send_text_message(sender_id, "I can only process text and button clicks for now. Type 'menu' to see options.")
        send_cityscope_greeting(sender_id)
        # Ensure state is managed after sending greeting
        user_sessions[sender_id] = {'state': 'AWAITING_MAIN_CHOICE'}


def handle_unexpected_input(sender_id, user_state): # Modified this function
    send_unknown_input_response(sender_id)
    # Resend the appropriate menu based on state
    if user_state in ['AWAITING_MAIN_CHOICE', 'GREETING', 'AWAITING_POST_ACTION_CHOICE']:
        send_cityscope_greeting(sender_id)
    elif user_state == 'AWAITING_EXPLORE_CHOICE':
        # Since send_explore_city_options is not defined and this state isn't actively used
        # in this simpler version, let's make it do something reasonable.
        app.logger.info(f"User in undefined AWAITING_EXPLORE_CHOICE. Reverting to main greeting for {sender_id}.")
        send_cityscope_greeting(sender_id)
    else: # Default fallback for any other unknown states
        send_cityscope_greeting(sender_id)

    # Ensure the state is reset to something known if it was an unhandled one,
    # send_cityscope_greeting already sets state to AWAITING_MAIN_CHOICE.
    # If a different default state is needed for some cases, adjust here.
    if user_sessions.get(sender_id, {}).get('state') not in ['AWAITING_MAIN_CHOICE', 'AWAITING_POST_ACTION_CHOICE']:
         user_sessions[sender_id] = {'state': 'AWAITING_MAIN_CHOICE'}


def send_cityscope_greeting(recipient_id):
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_id,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "header": {"type": "text", "text": "Welcome to Cityscope! 🌆"},
            "body": {"text": "Discover the vibrant life of your city! How can I help you unveil its story today?"},
            "footer": {"text": "Your guide to local India"},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "explore_city", "title": "Explore Your City"}},
                    {"type": "reply", "reply": {"id": "featured_content", "title": "Featured Content"}},
                    {"type": "reply", "reply": {"id": "businesses_creators", "title": "For Businesses"}}
                ]
            }
        }
    }
    send_whatsapp_api_request(payload)
    user_sessions[recipient_id] = {'state': 'AWAITING_MAIN_CHOICE'}
    # Second message for more options, as WhatsApp buttons are limited to 3
    send_cityscope_greeting_part2(recipient_id)


def send_cityscope_greeting_part2(recipient_id):
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_id,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": "More ways to connect with Cityscope:"},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "local_experiences", "title": "Local Experiences"}},
                    {"type": "reply", "reply": {"id": "about_cityscope", "title": "About Cityscope"}},
                    {"type": "reply", "reply": {"id": "help_contact", "title": "Help / Contact"}}
                ]
            }
        }
    }
    send_whatsapp_api_request(payload)
    # The state AWAITING_MAIN_CHOICE is already set by send_cityscope_greeting


def handle_cityscope_button_reply(sender_id, button_id):
    app.logger.info(f"User {sender_id} clicked button: {button_id}")
    
    response_text = ""
    next_state = 'AWAITING_POST_ACTION_CHOICE' 

    if button_id == "explore_city":
        response_text = (
            "Let's explore! What are you interested in?\n"
            "• Hidden Gems 💎\n"
            "• Food & Drink 🍲\n"
            "• Local Events 🎉\n"
            "• Shopping Spots 🛍️\n\n"
            "Tell me (e.g., 'Food & Drink') or check our app for full listings!"
        )
        # In this simpler version, 'explore_city' gives a text prompt.
        # For a more interactive flow, you might set a state like 'AWAITING_EXPLORE_TEXT_INPUT'
        # and process the user's free text reply in process_user_message.
        # For now, it just shows text and then offers "Main Menu".
    elif button_id == "featured_content":
        response_text = (
            "Discover our latest stories! 📰\n"
            "1. 'The Secret Gardens of Bangalore' - A green escape.\n"
            "2. 'Street Food Sagas: Mumbai Edition' - A culinary journey.\n"
            "3. 'Meet Jaipur's Young Artisans' - Keeping traditions alive.\n\n"
            "Find these and more on the Cityscope app!"
        )
    elif button_id == "local_experiences":
        response_text = (
            "Immerse yourself in unique local experiences! 🤸‍♂️\n"
            "• Attend a pottery workshop in your city.\n"
            "• Join a guided heritage walk.\n"
            "• Discover local music gigs and art shows.\n\n"
            "Check the Cityscope app for current listings and bookings!"
        )
    elif button_id == "businesses_creators":
        response_text = (
            "Are you a local business or creator? Cityscope is here to help you shine! ✨\n"
            "We provide tools to grow your brand and connect with the local community.\n"
            "Visit [https://www.cityscope.media] to learn more and get listed!" # Example link
        )
    elif button_id == "about_cityscope":
        response_text = (
            "Cityscope is your go-to platform for discovering the vibrant life and offerings of cities across India. 🇮🇳\n"
            "We're on a mission to unveil every city's story through curated local content, unique experiences, "
            "and services that empower our community and creative entrepreneurs. Join us!"
        )
    elif button_id == "help_contact":
        response_text = (
            "Need help or have a question?\n"
            "📧 Email us: tech@analog.ventures\n" # Example email
            "🌐 Visit our Help Center: [https://www.cityscope.media]\n" # Example link
            "Type 'menu' to see options again."
        )
        next_state = 'AWAITING_MAIN_CHOICE' 
    elif button_id == "main_menu_prompt": 
        send_cityscope_greeting(sender_id)
        return 

    else:
        send_unknown_input_response(sender_id)
        send_cityscope_greeting(sender_id)
        return

    send_text_message(sender_id, response_text)
    user_sessions[sender_id] = {'state': next_state}
    
    if next_state == 'AWAITING_POST_ACTION_CHOICE':
        send_back_to_main_menu_prompt(sender_id)

def send_back_to_main_menu_prompt(recipient_id):
    payload = {
        "messaging_product": "whatsapp", "to": recipient_id, "type": "interactive",
        "interactive": {
            "type": "button", "body": { "text": "What would you like to do next?" },
            "action": {"buttons": [{"type": "reply", "reply": {"id": "main_menu_prompt", "title": "Main Menu"}}]}
        }
    }
    send_whatsapp_api_request(payload)
    user_sessions[recipient_id] = {'state': 'AWAITING_MAIN_CHOICE'} 

def handle_cityscope_list_reply(sender_id, list_id, list_title):
    # This function is a placeholder in this version as no list messages are actively sent.
    app.logger.info(f"User {sender_id} selected list item ID: {list_id}, Title: {list_title} (List Reply Placeholder)")
    
    send_text_message(sender_id, f"You selected: {list_title} from a list. This feature is under development. More details coming soon via our app!")
    send_back_to_main_menu_prompt(sender_id)
    user_sessions[sender_id] = {'state': 'AWAITING_POST_ACTION_CHOICE'}


def send_cityscope_help_message(recipient_id):
    help_text = (
        "Welcome to Cityscope Support!\n"
        "I can help you with:\n"
        "🗺️ Exploring your city (select from main menu)\n"
        "📰 Finding featured content\n"
        "🎉 Discovering local experiences\n"
        "💼 Information for businesses/creators\n"
        "💡 Learning about Cityscope\n\n"
        "Type 'menu' or 'hi' to see the main options again."
    )
    send_text_message(recipient_id, help_text)

def send_unknown_input_response(recipient_id):
    send_text_message(recipient_id, "Hmm, I didn't quite get that. 🤔 Please choose an option from the menu, or type 'help' or 'menu'.")

def send_text_message(recipient_id, message_text):
    payload = {"messaging_product": "whatsapp", "to": recipient_id, "type": "text", "text": {"body": message_text}}
    send_whatsapp_api_request(payload)

def mark_message_as_read(message_id):
    payload = {"messaging_product": "whatsapp", "status": "read", "message_id": message_id}
    send_whatsapp_api_request(payload)

def send_whatsapp_api_request(payload):
    if not ACCESS_TOKEN or not PHONE_NUMBER_ID:
        app.logger.error("WhatsApp API credentials (ACCESS_TOKEN, PHONE_NUMBER_ID) are not set.")
        return

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages" 
    
    app.logger.info(f"Sending API request to {url} with payload: {json.dumps(payload, indent=2)}")
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        app.logger.info(f"API Response status: {response.status_code}, body: {response.text}")
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error sending WhatsApp API request: {e}")
        if hasattr(e, 'response') and e.response is not None:
            app.logger.error(f"Response content: {e.response.text}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)), debug=(os.getenv("FLASK_DEBUG", "False").lower() == "true"))