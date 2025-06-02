from datetime import datetime
from flask import Blueprint, jsonify, request, Response
from src.database.mongodb import db
from src.user_utils.params import LaunchCall
from src.user_utils.auth import login_required, admin_required, get_token_data
from src.user_utils.utils import get_lk_outbound_sip, trigger_outbound_call, activate_recording
from src.logger.log import Log_class
from twilio.rest import Client
import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet
import json
import base64
import asyncio
import websockets
from flask_sock import Sock
import wave
import io

load_dotenv()

# Voice settings
VOICE = "ballad"
SYSTEM_MESSAGE = """You are an Ayesha working for a financial services provider. Your tone should be friendly, polite, professional, and easy to understand. You are calling customers to remind them of an upcoming or overdue loan payment. Your goal is to inform them clearly, avoid sounding robotic or aggressive, and offer assistance if needed. You should personalize the call with the customer's name, mention the due date and amount, and ask them if they are able to pay it on time or not, If not, trace the reason. If something is out of order, ask them to contact the support team. Always speak slowly, with natural pauses, and sound empathetic and respectful throughout the call. Find the user details as follows:"""

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
sock = Sock(launch_bp)
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
        campaign_id = batch_data["campaign_id"]
        call_batch = list(
            db.call_batch_details.find(
                {"created_by": user_id, "batch_name": batch_data["batch_name"],
                 "campaign_id": campaign_id}, {"_id": 0}
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
        telephony_details = db.telephony_details.find_one(
            {"user_id": user_id}, {"_id": 0}
        )
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

            client = Client(account_sid, auth_token)
            # Fetch call batch details from MongoDB
            try:
                # Check if SIP trunk already exists
                existing_trunk = None
                if "sip_trunk_sid" in telephony_details:
                    try:
                        existing_trunk = client.trunks(telephony_details['sip_trunk_sid']).fetch()
                    except:
                        pass
                if not existing_trunk:
                    # Create a unique domain name based on account SID
                    domain_name = f"{account_sid[-8:]}.pstn.twilio.com"

                    # Create SIP domain
                    try:
                        user_id = batch_data["user_id"]
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
                        user_id = batch_data["user_id"]
                        trunk = client.trunking.trunks.create(
                            friendly_name=f"Auto SIP Trunk for {batch_data["user_id"]}",
                            domain_name=domain_name,
                        )
                        # trunk_sid = trunk.sid
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
                    # Create Credentials
                    credential_list = client.sip.credential_lists.create(
                        friendly_name=f"{user_id}-Credential-List",
                    )
                    print(f"Created Credential List SID: {credential_list.sid}")
                    # Store Credential List SID in database
                    db.telephony_details.update_one(
                        {"user_id": batch_data["user_id"]},
                        {
                            "$set": {
                                "credential_list_sid": credential_list.sid,
                            }
                        },
                    )
                    auth_password = telephony_details["voiceProvider"] + user_id
                    credential = client.sip.credential_lists(
                        credential_list.sid
                    ).credentials.create(username=user_id, password=auth_password)
                    print(f"Created Credential SID: {credential.sid}")

                    # Store Credential SID in database
                    db.telephony_details.update_one(
                        {"user_id": batch_data["user_id"]},
                        {
                            "$set": {
                                "credential_sid": credential.sid,
                                "user_name": user_id,
                                "password": auth_password,
                            }
                        },
                    )

                    # Associate Credential List with Trunk's Termination
                    client.trunking.v1.trunks(trunk.sid).credentials_lists.create(
                        credential_list_sid=credential_list.sid
                    )

                    print("Credential List linked to Termination URI")

                    # Store Credential List SID in database
                    db.telephony_details.update_one(
                        {"user_id": batch_data["user_id"]},
                        {
                            "$set": {
                                "is_credential_linked": True,
                            }
                        },
                    )
                    print(
                        "Credential List linked to Termination URI and added to telephony details"
                    )
                    
                    campaign_details = db.campaign_details.find_one(
            {"user_id": user_id, "campaign_id": campaign_id}, {"_id": 0}
        )
                    print(campaign_details)
                    # Create Livekit Outbound SIP
                    lk_outbound_sip = asyncio.run(
                        get_lk_outbound_sip(
                            name=user_id,
                            address=domain_name,
                            numbers=phone_number,
                            user_name=user_id,
                            password=auth_password,
                        )
                    )
                    # Store Credential List SID in database
                    db.telephony_details.update_one(
                        {"user_id": batch_data["user_id"]},
                        {
                            "$set": {
                                "is_lk_outbound_created": True,
                                "lk_outbound_sip": lk_outbound_sip,
                            }
                        },
                    )
                    print("Created LK Outbound SIP for Twilio and Stored in Telephony Details")
                    asyncio.run(trigger_outbound_call(outbound_trunk_id=lk_outbound_sip,))
                else:
                    # Fetch all details and trigger Call
                    is_lk_outbound_created = telephony_details.get(
                        "is_lk_outbound_created"
                    )
                    if is_lk_outbound_created:
                        lk_outbound_sip = telephony_details.get('lk_outbound_sip')
                    asyncio.run(trigger_outbound_call(outbound_trunk_id=lk_outbound_sip, system_prompt=SYSTEM_MESSAGE))
                    return {"Success":True}

            except Exception as e:
                print(str(e))
    except:
        pass
