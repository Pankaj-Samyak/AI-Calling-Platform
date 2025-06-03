from pymongo import MongoClient
from pymongo.errors import PyMongoError
from twilio.rest import Client
import threading
import time
from src.database.mongodb import db  # Make sure this imports your MongoDB instance correctly
import os
from cryptography.fernet import Fernet
import requests
import gridfs

# Get encryption key
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

# Initialize Fernet with the encryption key
try:
    cipher_suite = Fernet(ENCRYPTION_KEY)
except Exception as e:
    raise Exception("Invalid encryption key or error initializing Fernet") from e


def decrypt_credential(encrypted_credential):
    """Decrypt a credential using Fernet symmetric encryption"""
    return cipher_suite.decrypt(encrypted_credential.encode()).decode()

MAX_RETRIES = 5
RETRY_INTERVAL = 10  # seconds between status checks
FINAL_STATUSES = ['completed', 'failed', 'canceled', 'no-answer', 'busy']

def get_twilio_credentials(user_id):
    """Fetch and decrypt Twilio credentials for the given user"""
    cred = db.telephony_details.find_one({"user_id": user_id}, {"_id": 0})
    if cred and cred.get("voiceProvider") == "TWILIO":
        account_sid = decrypt_credential(cred["twilioAccountSid"])
        auth_token = decrypt_credential(cred["twilioAuthToken"])
        return account_sid, auth_token
    raise Exception(f"No Twilio credentials found for user_id: {user_id}")

def handle_call_status_update(doc):
    """Poll Twilio for call status and update the database"""
    call_sid = doc.get("twilio_call_sid")
    campaign_logs = db.campaign_call_logs.find_one({"twilio_call_sid": call_sid}, {"_id": 0})
    user_id = campaign_logs.get('user_id')
    campaign_id = campaign_logs.get('campaign_id')

    try:
        account_sid, auth_token = get_twilio_credentials(user_id)
        client = Client(account_sid, auth_token)
        attempt = 0
        status = None

        while attempt < MAX_RETRIES:
            call = client.calls(call_sid).fetch()
            status = call.status
            print(f"[{call_sid}] Attempt {attempt + 1}: Status = {status}")

            if status in FINAL_STATUSES:
                update_data = {"call_status": status}
                if status == "completed":
                    update_data.update({
                        "call_duration": call.duration,
                        "start_time": call.start_time,
                        "end_time": call.end_time,
                        "price": call.price,
                        "direction": call.direction,
                        "from": call.caller_name,
                        "to": call.to,
                        "recording": False
                    })
                    recordings = client.recordings.list(call_sid=call_sid)
                    if not recordings:
                        raise ValueError("No recordings found for this call SID.")
                    recording = recordings[0]
                    recording_url = f"https://api.twilio.com{recording.uri.replace('.json', '.mp3')}"
                    # Download mp3 as raw bytes
                    response = requests.get(recording_url, auth=(account_sid, auth_token))
                    if response.status_code != 200:
                        raise Exception(f"Failed to fetch recording: {response.status_code} {response.text}")
                    
                    file_id = db.store_file(file_data= response.content, filename=f"{call_sid}.mp3")
                    recording_doc = {
                        "user_id" : user_id,
                        "twilio_call_sid": call_sid,
                        "campaign_id": campaign_logs.get('campaign_id'),
                        "batch_name": campaign_logs.get('batch_name'),
                        "call_duration": call.duration,
                        "phone_number": call.to,
                        "file_id": file_id
                    }
                    db.recordings.insert_one(recording_doc)
                db.campaign_call_logs.update_one({"_id": doc["_id"]}, {"$set": update_data})
                print(f"Updated document with final status: {status}")
                return
            else:
                attempt += 1
                time.sleep(RETRY_INTERVAL)

        # After retries, update with last known status
        print(f"[{call_sid}] Max retries reached. Last known status: {status}")
        db.campaign_call_logs.update_one({"_id": doc["_id"]}, {"$set": {"call_status": status}})

    except Exception as e:
        print(f"Error handling call status for {call_sid}: {e}")


def poll_for_new_calls():
    """Poll MongoDB every few seconds for new outbound calls without a final status"""
    print("Polling for new call logs...")

    processed_ids = set()

    while True:
        try:
            docs = db.campaign_call_logs.find({
                "twilio_call_flag": True,
                "call_status": {"$exists": False}
            })

            for doc in docs:
                doc_id = str(doc["_id"])
                if doc_id not in processed_ids:
                    processed_ids.add(doc_id)
                    threading.Thread(target=handle_call_status_update, args=(doc,)).start()

        except PyMongoError as e:
            print(f"MongoDB error during polling: {e}")

        time.sleep(5)  # Poll every 10 seconds

if __name__ == "__main__":
    poll_for_new_calls()
