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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DOMAIN = os.getenv("DOMAIN", "your-domain.com")  # Your domain for WebSocket

# Voice settings
VOICE = "ballad"
SYSTEM_MESSAGE = """You are Catherine, a voice assistant from Samyak Telecommunications. You assist the customer with daily news and fun facts."""  # Add your full system message here

# Event types to log
LOG_EVENT_TYPES = [
    "error",
    "response.content.done",
    "rate_limits.updated",
    "response.done",
    "input_audio_buffer.committed",
    "input_audio_buffer.speech_stopped",
    "input_audio_buffer.speech_started",
    "session.created",
]

launch_bp = Blueprint("launch_bp", __name__)
# sock = Sock(launch_bp)
logg_obj = Log_class("logs", "launch_calls.txt")

# Get encryption key
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

# Initialize Fernet with the encryption key
try:
    cipher_suite = Fernet(ENCRYPTION_KEY)
except Exception as e:
    raise


def decrypt_credential(encrypted_credential):
    """Decrypt a credential using Fernet symmetric encryption"""
    return cipher_suite.decrypt(encrypted_credential.encode()).decode()


@launch_bp.route("/execute_call_batch", methods=["POST"])
@login_required
def execute_call_batch():
    try:
        batch_data = LaunchCall.parse_raw(request.data).dict()
        user_id = batch_data["user_id"]
        call_batch = list(
            db.call_batch_details.find(
                {"created_by": user_id, "batch_name": batch_data["batch_name"]}
            )
        )
        if not call_batch:
            return (
                jsonify(
                    {
                        "status": False,
                        "error": "No call batch found with the given name",
                    }
                ),
                404,
            )

        # Fetch user's telephony details
        telephony_details = db.telephony_details.find_one({"user_id": user_id})
        if not telephony_details:
            return (
                jsonify(
                    {
                        "status": False,
                        "error": "No telephony integration found for this user",
                    }
                ),
                400,
            )

        # Decrypt telephony credentials
        if telephony_details["voiceProvider"] == "TWILIO":
            account_sid = decrypt_credential(telephony_details["twilioAccountSid"])
            auth_token = decrypt_credential(telephony_details["twilioAuthToken"])
            phone_number = telephony_details.get("twilioPhoneNumber")

            # Initialize Twilio client
            client = Client(account_sid, auth_token)
            # Fetch call batch details from MongoDB
            try:
                # Check if SIP trunk already exists
                existing_trunk = None
                if "sip_trunk_sid" in telephony_details:
                    try:
                        existing_trunk = client.trunking.trunks(
                            telephony_details["sip_trunk_sid"]
                        ).fetch()
                    except:
                        pass

                if not existing_trunk:
                    # Create a unique domain name based on account SID
                    domain_name = f"{account_sid[-8:]}.pstn.twilio.com"

                    # Create SIP domain
                    try:
                        domain = client.sip.domains.create(
                            domain_name=domain_name,
                            friendly_name=f"Auto SIP Domain for {batch_data["user_id"]}",
                        )
                    except:
                        pass
                    # Create SIP trunk
                    try:
                        trunk = client.trunking.trunks.create(
                            friendly_name=f"Auto SIP Trunk for {batch_data["user_id"]}",
                            domain_name=domain_name,
                        )
                    except:
                        print(client.trunking.trunks.list())

                    # Store trunk SID in database
                    db.telephony_details.update_one(
                        {"user_id": batch_data["user_id"]},
                        {
                            "$set": {
                                "sip_trunk_sid": trunk.sid,
                                "domain_name": domain_name,
                            }
                        },
                    )

                    # Update phone number to use SIP trunk
                    phone_number = f"sip:{phone_number}@{domain_name}"
                    logg_obj.Info_Log(f"Created new SIP trunk with SID: {trunk.sid}")
                    return {"Status": "SIP Created"}
                else:
                    # Use existing trunk
                    phone_number = f"sip:{phone_number}@{existing_trunk.domain_name}"
                    logg_obj.Info_Log(
                        f"Using existing SIP trunk with SID: {existing_trunk.sid}"
                    )
                    trunk_sid = db.telephony_details.find_one(
                        {"user_id": user_id},
                        {
                            "_id": 0,
                            "sip_trunk_sid": 1,
                            "domain_name": 1,
                            "twilioPhoneNumber": 1,
                        },
                    )

                    outbound_twiml = (
                        f'<?xml version="1.0" encoding="UTF-8"?>'
                        f'<Response><Connect><Stream url="wss://{DOMAIN}/media-stream" /></Connect></Response>'
                    )

                    call = client.calls.create(
                        to="+919304263731",
                        from_=trunk_sid.get("twilioPhoneNumber"),
                        twiml=outbound_twiml,
                    )
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
        return jsonify({"status": False, "error": f"{e}"}), 500


@launch_bp.route("/stream_audio", methods=["GET"])
def stream_audio():
    def generate_audio():
        try:
            # Initialize OpenAI client
            client = openai.OpenAI(api_key=OPENAI_API_KEY)

            # Create a streaming response from OpenAI
            response = client.audio.speech.create(
                model="tts-1", voice=VOICE, input=SYSTEM_MESSAGE, response_format="mp3"
            )

            # Stream the audio data in chunks
            for chunk in response.iter_bytes(chunk_size=4096):
                yield chunk

        except Exception as e:
            logg_obj.Error_Log(f"Error in audio streaming: {str(e)}")
            yield b""

    return Response(generate_audio(), mimetype="audio/mpeg")  # Using MP3 format


@launch_bp.route("/call_status", methods=["POST"])
def call_status():
    # Handle call status updates
    status = request.form.get("CallStatus")
    call_sid = request.form.get("CallSid")
    logg_obj.Info_Log(f"Call {call_sid} status: {status}")
    return "", 200
