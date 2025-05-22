from datetime import datetime
from flask import Blueprint, jsonify, request, Response
from src.database.mongodb import db
from src.user_utils.params import LaunchCall
from src.user_utils.auth import login_required, admin_required, get_token_data
from src.logger.log import Log_class
from twilio.rest import Client
import openai
import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet
import json
import base64
import asyncio
import websockets
from flask_sock import Sock

load_dotenv()

# Environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DOMAIN = os.getenv('DOMAIN', 'your-domain.com')  # Your domain for WebSocket

# Voice settings
VOICE = 'ballad'
SYSTEM_MESSAGE = """You are Catherine, a voice assistant from Samyak Telecommunications..."""  # Add your full system message here

# Event types to log
LOG_EVENT_TYPES = [
    'error', 'response.content.done', 'rate_limits.updated', 'response.done',
    'input_audio_buffer.committed', 'input_audio_buffer.speech_stopped',
    'input_audio_buffer.speech_started', 'session.created'
]

launch_bp = Blueprint('launch_bp', __name__)
#sock = Sock(launch_bp)
logg_obj = Log_class("logs", "launch_calls.txt")

# Get encryption key
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')

# Initialize Fernet with the encryption key
try:
    cipher_suite = Fernet(ENCRYPTION_KEY)
except Exception as e:
    raise

def decrypt_credential(encrypted_credential):
    """Decrypt a credential using Fernet symmetric encryption"""
    return cipher_suite.decrypt(encrypted_credential.encode()).decode()

@launch_bp.route('/execute_call_batch', methods=['POST'])
@login_required
def execute_call_batch():
    try:
        batch_data = LaunchCall.parse_raw(request.data).dict()

        call_batch = list(db.call_batch_details.find({
                "created_by": batch_data["user_id"],
                "batch_name": batch_data["batch_name"]}))
        if not call_batch:
            return jsonify({'status': False, "error": "No call batch found with the given name"}), 404

        # Fetch user's telephony details
        telephony_details = db.telephony_details.find_one({"user_id": batch_data["user_id"]})
        if not telephony_details:
            return jsonify({'status': False, "error": "No telephony integration found for this user"}), 400

        # Decrypt telephony credentials
        if telephony_details['voiceProvider'] == "TWILIO":
            account_sid = decrypt_credential(telephony_details['twilioAccountSid'])
            auth_token = decrypt_credential(telephony_details['twilioAuthToken'])
            phone_number = telephony_details.get('twilioPhoneNumber')

            # Initialize Twilio client
            client = Client(account_sid, auth_token)
             # Fetch call batch details from MongoDB
            try:
                # Check if SIP trunk already exists
                existing_trunk = None
                if 'sip_trunk_sid' in telephony_details:
                    try:
                        existing_trunk = client.trunks(telephony_details['sip_trunk_sid']).fetch()
                    except:
                        pass

                if not existing_trunk:
                    # Create a unique domain name based on account SID
                    domain_name = f"{account_sid[-8:]}.pstn.twilio.com"

                    # Create SIP domain
                    try:
                        domain = client.sip.domains.create(
                            domain_name=domain_name,
                            friendly_name=f"Auto SIP Domain for {batch_data["user_id"]}"
                        )
                    except:
                        domain = client.sip.domains.list()
                        main_dom = [dom for dom in domain if dom.account_sid == account_sid]
                        dom_sid = main_dom[0].sid
                        print(dom_sid)
                    # Create SIP trunk
                    try:
                        trunk = client.trunking.trunks.create(
                            friendly_name=f"Auto SIP Trunk for {batch_data["user_id"]}",
                            domain_name=domain_name
                        )
                    except:
                        print(client.trunking.trunks.list())
                    # print(f"Trunk SID: {trunk.sid}")
                    # print(f"Trunk Domain: {trunk.domain_name}")

                    # Store trunk SID in database
                    db.telephony_details.update_one(
                        {"user_id": batch_data["user_id"]},
                        {"$set": {"sip_trunk_sid": trunk.sid}}
                    )

                    # Update phone number to use SIP trunk
                    phone_number = f"sip:{phone_number}@{domain_name}"
                    logg_obj.Info_Log(f"Created new SIP trunk with SID: {trunk.sid}")
                    return {"Status": "SIP Created"}
                else:
                    # Use existing trunk
                    phone_number = f"sip:{phone_number}@{existing_trunk.domain_name}"
                    logg_obj.Info_Log(f"Using existing SIP trunk with SID: {existing_trunk.sid}")
                    return {"Status": "Using existing sid"}

            except Exception as e:
                logg_obj.Error_Log(f"Error in SIP trunk setup: {str(e)}")
                # Fall back to regular phone number if SIP setup fails
                logg_obj.Info_Log("Falling back to regular phone number")
                return {"Error in execute call batch": str(e)}
        else:
            pass
    
    except Exception as e:
        print("Error in Execute call batch", str(e))
        return jsonify({'status':False, "error": f"{e}"}), 500