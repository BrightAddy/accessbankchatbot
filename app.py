import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from dotenv import load_dotenv
import os
import requests
from flask import Flask, request, jsonify

load_dotenv()

from rag_agent import agent

app = Flask(__name__)

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v21.0")
WHATSAPP_REQUEST_TIMEOUT = int(os.getenv("WHATSAPP_REQUEST_TIMEOUT", "20"))


# ── Health Check ────────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "status": "online",
        "service": "Access Bank Ghana WhatsApp Bot"
    }), 200


# ── Webhook Verification ────────────────────────────────────────────────────
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verified!")
        return challenge, 200
    print("❌ Webhook verification failed!")
    return "Forbidden", 403


import threading
import time

PROCESSED_MESSAGE_IDS = set()

def process_message_async(sender_number, message_text, message_id=None, phone_number_id=None, user_display=None):
    label = user_display or sender_number
    try:
        t0 = time.time()
        print(f"👤 [{label}] Processing: '{message_text}'")
        response = agent.invoke(
            {"messages": [{"role": "user", "content": message_text}]}
        )
        answer = response["messages"][-1].content
        duration = round(time.time() - t0, 2)
        print(f"🤖 [{label}] Generated reply in {duration}s: {answer[:80]}...")

        send_whatsapp_message(sender_number, answer, phone_number_id=phone_number_id, message_id=message_id)
    except Exception as e:
        print(f"❌ Error processing message for {label}: {e}")
        try:
            send_whatsapp_message(
                sender_number,
                "I apologize, but I am experiencing a temporary system delay. Please try again shortly or contact Access Bank Ghana Customer Care at 0800 004 400.",
                phone_number_id=phone_number_id,
                message_id=message_id
            )
        except Exception as send_err:
            print(f"❌ Failed to send fallback message: {send_err}")


# ── Receive Messages ────────────────────────────────────────────────────────
@app.route("/webhook", methods=["POST"])
def receive_message():
    data = request.get_json() or {}
    try:
        # Standard webhook delivery
        if "entry" in data and len(data["entry"]) > 0:
            entry = data["entry"][0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
        # Developer Portal "Test" button delivery
        elif "value" in data:
            value = data.get("value", {})
        else:
            value = data

        if "messages" not in value or len(value["messages"]) == 0:
            return jsonify({"status": "ok"}), 200

        message = value["messages"][0]
        message_id = message.get("id")
        phone_number_id = value.get("metadata", {}).get("phone_number_id")
        
        contacts = value.get("contacts")
        first_contact = contacts[0] if (contacts and isinstance(contacts, list) and len(contacts) > 0 and isinstance(contacts[0], dict)) else {}

        # Support standard phone numbers as well as Meta Cloud API user_ids / usernames
        sender_number = (
            message.get("from")
            or message.get("from_user_id")
            or first_contact.get("wa_id")
            or first_contact.get("user_id")
        )
        
        # Format display name from profile if available
        user_display = sender_number
        if isinstance(first_contact.get("profile"), dict):
            p_name = first_contact["profile"].get("name")
            p_user = first_contact["profile"].get("username")
            if p_name and p_user:
                user_display = f"{p_name} (@{p_user})"
            elif p_name:
                user_display = p_name
            elif p_user:
                user_display = f"@{p_user}"

        msg_type = message.get("type", "unknown")

        # Prevent duplicate handling if Meta retries
        if message_id:
            if message_id in PROCESSED_MESSAGE_IDS:
                return jsonify({"status": "already_received"}), 200
            PROCESSED_MESSAGE_IDS.add(message_id)
            if len(PROCESSED_MESSAGE_IDS) > 2000:
                PROCESSED_MESSAGE_IDS.clear()

        # Handle non-text messages (voice notes, images, stickers, documents)
        if msg_type != "text":
            print(f"ℹ️ Received non-text ({msg_type}) message from {user_display}")
            threading.Thread(
                target=send_whatsapp_message,
                args=(sender_number, "Hello! Currently, I can only assist with written text messages. Please type your banking question and I'll be happy to help!", phone_number_id, message_id),
                daemon=True
            ).start()
            return jsonify({"status": "handled_non_text"}), 200

        raw_text = message.get("text")
        if isinstance(raw_text, dict):
            message_text = raw_text.get("body", "")
        elif isinstance(raw_text, str):
            message_text = raw_text
        else:
            message_text = ""

        if not sender_number or not message_text:
            print(f"⚠️ Webhook message ignored: sender='{sender_number}', text='{message_text}'")
            return jsonify({"status": "ignored"}), 200

        print(f"📩 Webhook message from {user_display}: '{message_text}'")

        # Run in background thread so Meta gets instant 200 OK without timeout
        threading.Thread(
            target=process_message_async,
            args=(sender_number, message_text, message_id, phone_number_id, user_display),
            daemon=True
        ).start()

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Webhook Error: {e}")

    return jsonify({"status": "ok"}), 200



def send_whatsapp_message(to_number, message, phone_number_id=None, message_id=None):
    pn_id = phone_number_id if (phone_number_id and phone_number_id != "123456123") else PHONE_NUMBER_ID
    url = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{pn_id}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": str(to_number),
        "type": "text",
        "text": {"body": message}
    }
    # Provide message_id context so replies to Meta User IDs / BSUIDs are accurately threaded and delivered
    if message_id:
        payload["context"] = {"message_id": message_id}

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=WHATSAPP_REQUEST_TIMEOUT
    )
    print(f"📤 Sent to {to_number} (Status: {response.status_code})")
    if response.status_code != 200:
        print(f"⚠️ Meta Error Response: {response.text}")
    return response



if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"🚀 Starting Access Bank Ghana WhatsApp Bot on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)
