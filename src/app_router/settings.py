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

settings_bp = Blueprint('settings_bp', __name__)
logg_obj = Log_class("logs", "settings_bp.txt")

#get current datetime
def current_timestamp():
    return datetime.utcnow()

#------------------------------------------#
#-------------Campaign-Management----------#
#------------------------------------------#
@settings_bp.route('/get_voices_languages', methods=['GET'])
@login_required
def get_voices_languages():
    try:
        data = db.settings.find({}, {"_id": 0})
        return jsonify(list(data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@settings_bp.route('/voice_demo', methods=['GET'])
@login_required
def voice_demo():
    try:
        data = db.settings.find({}, {"_id": 0})
        return jsonify(list(data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
