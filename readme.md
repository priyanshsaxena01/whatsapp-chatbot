# Cityscope WhatsApp Chatbot

A WhatsApp chatbot built with Python (Flask) and the WhatsApp Business API (via Meta Developer Portal) to serve as a basic interactive guide for Cityscope. It allows users to navigate through predefined options about Cityscope's services, featured content, and contact information using interactive buttons.

## Features

-   **Interactive Chat Flow:** Guides users through a structured conversation using WhatsApp interactive buttons.
-   **Predefined Options:** Presents users with fixed options for exploring Cityscope.
-   **Fixed Responses:** Provides static text responses based on user selections.
-   **Basic Help & Error Handling:** Includes a help message and gracefully handles unexpected inputs by re-offering main options.
-   **Webhook Integration:** Handles incoming messages from the WhatsApp Business API and webhook verification.

## Tech Stack

-   **Python 3.x**
-   **Flask:** Micro web framework for the backend server and webhook endpoint.
-   **Requests:** For making HTTP requests to the WhatsApp Graph API to send messages.
-   **python-dotenv:** For managing environment variables securely.
-   **Meta WhatsApp Business API:** (Cloud API utilized via the Meta Developer Portal).

## Core Logic

-   **State Management (`user_sessions`):** A simple in-memory Python dictionary tracks the user's current state in the conversation (e.g., `AWAITING_MAIN_CHOICE`, `AWAITING_POST_ACTION_CHOICE`).
-   **Button-Driven Navigation:** The primary interaction is through predefined buttons. The `handle_cityscope_button_reply` function processes these selections.
-   **Static Content:** Information about services, featured content, etc., is hardcoded as text strings within the Python script.
-   **Two-Part Greeting:** Due to WhatsApp's limit of 3 buttons per interactive message, the main menu is presented in two consecutive button messages.

## Setup and Installation

1.  **Prerequisites:**
    *   Python 3.8+ installed.
    *   `pip` (Python package installer).
    *   A Meta Developer Account.
    *   A configured WhatsApp Business API application on the Meta Developer Portal, providing:
        *   A Test Phone Number.
        *   A Phone Number ID.
        *   A Temporary Access Token (regenerate if it expires, typically every 23 hours).
    *   A publicly accessible HTTPS URL for your webhook (e.g., using ngrok for local development, or a deployed server like GitHub Codespaces, Heroku, etc.).

2.  **Clone the Repository (Example):**
    ```bash
    git clone <your-repository-url>
    cd <your-repository-directory>
    ```

3.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

4.  **Install Dependencies:**
    Create a `requirements.txt` file with the following content:
    ```txt
    Flask==2.3.3
    requests==2.31.0
    python-dotenv==1.0.0
    # gunicorn==21.2.0 # Optional: if you plan to use Gunicorn for deployment
    ```
    Then run:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Set Up Environment Variables:**
    *   Create a `.env` file in the root directory of the project.
    *   Add the following variables, replacing placeholders with your actual credentials from the Meta Developer Portal:
        ```env
        WHATSAPP_ACCESS_TOKEN=YOUR_TEMPORARY_ACCESS_TOKEN_FROM_META
        WHATSAPP_PHONE_NUMBER_ID=YOUR_PHONE_NUMBER_ID_FROM_META
        WHATSAPP_VERIFY_TOKEN=CHOOSE_A_STRONG_SECRET_VERIFY_TOKEN # e.g., "cityscope_secret_token123"
        FLASK_APP=app.py
        FLASK_DEBUG=True # Set to False for production
        # PORT=5000      # Optional: if you need to run on a specific port
        ```
    *   The `WHATSAPP_VERIFY_TOKEN` is a secret string you define. You will use this same string when configuring the webhook in the Meta Developer Portal.

6.  **Configure WhatsApp Webhook in Meta Developer Portal:**
    *   Navigate to your App Dashboard -> WhatsApp -> API Setup.
    *   Under "Step 3: Configure webhooks to receive messages", click "Edit".
    *   **Callback URL:** Enter your publicly accessible HTTPS URL followed by `/webhook` (e.g., `https://your-ngrok-url.io/webhook`).
    *   **Verify token:** Enter the *exact same* `WHATSAPP_VERIFY_TOKEN` that you defined in your `.env` file.
    *   Click "Verify and save".
    *   After successful verification, click "Manage" next to Webhook fields and ensure the `messages` field is subscribed.

## Running the Chatbot

1.  **Start the Flask Application:**
    ```bash
    python app.py
    ```

2.  **Ensure your Webhook is Publicly Accessible:**
    *   **If running locally:** Use a tool like `ngrok` to expose your local server.
        ```bash
        ngrok http 5000 # Replace 5000 if your app runs on a different port
        ```
        Use the `https://` URL provided by ngrok as your Callback URL.
    *   **If using GitHub Codespaces:** The port is automatically forwarded. Find the public URL in the "Ports" tab.

3.  **Test the Chatbot:**
    *   Add your personal WhatsApp number as a test recipient in the Meta Developer Portal (API Setup page, "Step 2: Send messages with the API").
    *   Send a message (e.g., "Hi", "menu", "cityscope") from your verified personal WhatsApp number to the **Test Phone Number** provided by Meta.
    *   Interact with the bot by tapping on the buttons presented.

## Example Chat Interaction

*   **User:** "Hi"
    *   **Bot:** (Sends "Welcome to Cityscope! 🌆" with buttons: "Explore Your City", "Featured Content", "For Businesses")
    *   **Bot:** (Immediately sends "More ways to connect with Cityscope:" with buttons: "Local Experiences", "About Cityscope", "Help / Contact")
*   **User:** (Taps "Explore Your City")
    *   **Bot:** (Sends a text message: "Let's explore! What are you interested in? ... Tell me (e.g., 'Food & Drink') or check our app for full listings!")
    *   **Bot:** (Sends "What would you like to do next?" with a "Main Menu" button)
*   **User:** (Taps "Help / Contact")
    *   **Bot:** (Sends contact information and help details.)
*   **User:** (Types "random text")
    *   **Bot:** "Hmm, I didn't quite get that. 🤔 Please choose an option from the menu, or type 'help' or 'menu'."
    *   **Bot:** (Re-sends the main greeting messages with buttons)

## Disclaimer

This project uses a temporary access token from the Meta Developer Portal for the WhatsApp Business API. This token typically expires every 23 hours and will need to be regenerated for continued testing. For a production application, a long-lived System User Access Token or proper OAuth flow would be necessary.