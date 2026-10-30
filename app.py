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

def process_message_async(sender_number, message_text, message_id=None, phone_number_id=None):
    try:
        t0 = time.time()
        print(f"👤 [{sender_number}] Processing: '{message_text}'")
        response = agent.invoke(
            {"messages": [{"role": "user", "content": message_text}]}
        )
        answer = response["messages"][-1].content
        duration = round(time.time() - t0, 2)
        print(f"🤖 [{sender_number}] Generated reply in {duration}s: {answer[:80]}...")

        send_whatsapp_message(sender_number, answer, phone_number_id=phone_number_id)
    except Exception as e:
        print(f"❌ Error processing message: {e}")


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

        # Prevent duplicate handling if Meta retries
        if message_id:
            if message_id in PROCESSED_MESSAGE_IDS:
                return jsonify({"status": "already_received"}), 200
            PROCESSED_MESSAGE_IDS.add(message_id)
            if len(PROCESSED_MESSAGE_IDS) > 2000:
                PROCESSED_MESSAGE_IDS.clear()

        if message.get("type") != "text":
            return jsonify({"status": "ignored_non_text"}), 200

        sender_number = message.get("from")
        message_text = message.get("text", {}).get("body", "")

        if not sender_number or not message_text:
            return jsonify({"status": "ignored"}), 200

        # Run in background thread so Meta gets instant 200 OK without timeout
        threading.Thread(
            target=process_message_async,
            args=(sender_number, message_text, message_id, phone_number_id),
            daemon=True
        ).start()

    except Exception as e:
        print(f"❌ Webhook Error: {e}")

    return jsonify({"status": "ok"}), 200



def send_whatsapp_message(to_number, message, phone_number_id=None):
    pn_id = phone_number_id if (phone_number_id and phone_number_id != "123456123") else PHONE_NUMBER_ID
    url = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{pn_id}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message}
    }
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
