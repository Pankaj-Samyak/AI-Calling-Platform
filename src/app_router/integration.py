from flask import Blueprint, jsonify, request
from cryptography.fernet import Fernet
from src.database.mongodb import db
from src.user_utils.auth import login_required, admin_required, get_token_data
from src.user_utils.params import AddTelephony
from src.logger.log import Log_class
import os
import base64
from dotenv import load_dotenv

load_dotenv()

integration_bp = Blueprint('integration_bp', __name__)
logg_obj = Log_class("logs", "integration_bp.txt")

# Get encryption key
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')

# Initialize Fernet with the encryption key
try:
    cipher_suite = Fernet(ENCRYPTION_KEY)
except Exception as e:
    logg_obj.Error_Log(f"Failed to initialize Fernet: {str(e)}")
    raise

def encrypt_credential(credential):
    """Encrypt a credential using Fernet symmetric encryption"""
    return cipher_suite.encrypt(credential.encode()).decode()

def decrypt_credential(encrypted_credential):
    """Decrypt a credential using Fernet symmetric encryption"""
    return cipher_suite.decrypt(encrypted_credential.encode()).decode()

@integration_bp.route("/add_telephony", methods=['POST'])
@login_required
@admin_required
def add_telephony():
    try:
        telephony_data = AddTelephony.parse_raw(request.data).dict()
        
        # Encrypt sensitive credentials
        telephony_data['twilioAccountSid'] = encrypt_credential(telephony_data.get('twilioAccountSid'))
        telephony_data['twilioAuthToken'] = encrypt_credential(telephony_data.get('twilioAuthToken'))
        
        # Get user ID from token
        token_data = get_token_data()
        if not token_data:
            return jsonify({
                'status': False,
                "error": "Authorization failed. Please provide a valid JWT token."
            }), 400
        
        user_id = token_data.get('user_id')
        telephony_data["user_id"] = user_id
        
        # Check if the telephony account already exists
        existing_account = db.telephony_details.find_one({
            "user_id": user_id,
            "voiceProvider": telephony_data["voiceProvider"]
        })
        
        if existing_account:
            return jsonify({'status': False, 'message': 'Twilio account already created for this user'}), 400
            
        result = db.telephony_details.insert_one(telephony_data)
        mongo_id = result.inserted_id
        db.telephony_details.update_one(
            {"_id": mongo_id},
            {"$set": {"telephony_id": str(mongo_id)}}
        )
        return jsonify({
            'status': True, 
            'message': 'Twilio Account integrated successfully', 
            'telephony_id': str(mongo_id)
        }), 200
    except Exception as e:
        error = str(e).replace("\n", " * ")
        return jsonify({'status': False, "error": f"{error}"}), 500

@integration_bp.route("/get_telephony", methods=['GET'])
@login_required
def get_telephony():
    try:
        # Get user ID from token
        token_data = get_token_data()
        if not token_data:
            return jsonify({
                'status': False,
                "error": "Authorization failed. Please provide a valid JWT token."
            }), 400

        user_id = token_data.get('user_id')
        
        # Find all telephony accounts for the user
        telephony_accounts = dict(db.telephony_details.find_one(
            {"user_id": user_id},
            {"_id": 0}  # Exclude MongoDB _id from results
        ))
        if telephony_accounts:
            # Decrypt sensitive credentials before sending
            if 'twilioAccountSid' in telephony_accounts:
                telephony_accounts['twilioAccountSid'] = decrypt_credential(telephony_accounts['twilioAccountSid'])
            if 'twilioAuthToken' in telephony_accounts:
                telephony_accounts['twilioAuthToken'] = decrypt_credential(telephony_accounts['twilioAuthToken'])
            
            keys_to_remove = ['telephony_id', 'user_id']
            for key in keys_to_remove:
                telephony_accounts.pop(key, None)

            return jsonify({
                'status': True,
                'message': 'Telephony accounts found',
                'data': telephony_accounts
            }), 200
        else:
            return jsonify({
                'status': False,
                'message': 'No Telephony accounts found'
            }), 400
        
    except Exception as e:
        error = str(e).replace("\n", " * ")
        return jsonify({'status': False, "error": f"{error}"}), 500

@integration_bp.route("/update_telephony", methods=['PUT'])
@login_required
@admin_required
def update_telephony():
    try:
        telephony_data = AddTelephony.parse_raw(request.data).dict()
        
        # Get user ID from token
        token_data = get_token_data()
        if not token_data:
            return jsonify({
                'status': False,
                "error": "Authorization failed. Please provide a valid JWT token."
            }), 400

        user_id = token_data.get('user_id')
        
        # Check if telephony account exists for this user
        existing_account = db.telephony_details.find_one({
            "user_id": user_id
        })
        
        if not existing_account:
            return jsonify({
                'status': False,
                'message': 'No telephony account found to update'
            }), 404

        # Encrypt sensitive credentials
        if 'twilioAccountSid' in telephony_data:
            telephony_data['twilioAccountSid'] = encrypt_credential(telephony_data['twilioAccountSid'])
        if 'twilioAuthToken' in telephony_data:
            telephony_data['twilioAuthToken'] = encrypt_credential(telephony_data['twilioAuthToken'])
        
        # Update the telephony details
        result = db.telephony_details.update_one(
            {
                "user_id": user_id
            },
            {"$set": telephony_data}
        )
        if result.modified_count > 0:
            return jsonify({
                'status': True,
                'message': 'Telephony details updated successfully'
            }), 200
        else:
            return jsonify({
                'status': False,
                'message': 'No changes were made to the telephony details'
            }), 200
            
    except Exception as e:
        error = str(e).replace("\n", " * ")
        return jsonify({'status': False, "error": f"{error}"}), 500