import time
import json
import logging
from datetime import datetime
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bridge.log'),
        logging.StreamHandler()
    ]
)

# ─────── CONFIG ───────
PENDING_FILE = "runtime/bridge_inbox/pending_requests.json"
RESPONSES_FILE = "runtime/bridge_inbox/responses.json"
CHECK_INTERVAL = 60  # seconds
# ─────────────────────

def load_pending_requests():
    """Load pending requests from the inbox."""
    try:
        with open(PENDING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_responses(responses):
    """Save responses to the responses file."""
    os.makedirs(os.path.dirname(RESPONSES_FILE), exist_ok=True)
    with open(RESPONSES_FILE, "w", encoding="utf-8") as f:
        json.dump(responses, f, indent=2)

def process_requests():
    """Process pending requests and generate responses."""
    pending = load_pending_requests()
    if not pending:
        return

    responses = []
    for req in pending:
        agent_id = req.get("agent_id", "agent-unknown")
        prompt = req.get("prompt", "")
        
        if not prompt:
            continue

        logging.info(f"Processing request from {agent_id}")
        
        # For now, we'll just echo the request back
        # This is where we'd integrate with ChatGPT API in production
        response = {
            "agent_id": agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "prompt": prompt,
            "response": f"Echo: {prompt}",
            "status": "processed"
        }
        responses.append(response)
        logging.info(f"Generated response for {agent_id}")

    if responses:
        save_responses(responses)
        # Clear pending requests after processing
        with open(PENDING_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)

def main_loop():
    """Main monitoring loop."""
    logging.info("Starting bridge service...")
    
    while True:
        try:
            process_requests()
            time.sleep(CHECK_INTERVAL)
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main_loop() 
