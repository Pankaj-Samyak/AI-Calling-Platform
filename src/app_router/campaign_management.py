from datetime import datetime
from flask import Blueprint, jsonify, request

from src.logger.log import Log_class
from src.database.mongodb import db
from src.user_utils.params import CreateCampaign
from src.user_utils.auth import login_required, admin_required, get_token_data

campaign_bp = Blueprint('campaign_bp', __name__)
logg_obj = Log_class("logs", "campaign_bp.txt")

#get current datetime
def current_timestamp():
    return datetime.utcnow()

#------------------------------------------#
#-------------Campaign-Management----------#
#------------------------------------------#
@campaign_bp.route('/create_campaign', methods=['POST'])
@login_required
@admin_required
def create_campaign_api():
    try:
        campaign_data = CreateCampaign.parse_raw(request.data).dict()
        # Get user ID from token
        token_data = get_token_data()
        if token_data:
            user_id = token_data.get('user_id')
            #add the some data in campaign.
            campaign_data["totalNumCall"] = 0
            campaign_data["totalCallTime"] = 0
            campaign_data["user_id"] = user_id
            campaign_data["created_at"] = current_timestamp()
            #Check the campaign is already exists.
            if db.campaign_details.find_one({"user_id":user_id,"campaign_name":campaign_data["campaign_name"]},{"_id":0}):
                return jsonify({'status':False,'error': 'campaign already exists!'}), 400

            # Insert multiple documents
            result = db.campaign_details.insert_one(campaign_data)
            mongo_id = result.inserted_id
            db.campaign_details.update_one(
                {"_id": mongo_id},
                {"$set": {"campaign_id": str(mongo_id)}}
            )
            return jsonify({'status':True, 'message': f'Campaign created successfully', 'campaign_id': str(mongo_id)}),200
        else:
           return jsonify({'status':False, "error": "Authorization failed. Please provide a valid JWT token."}), 400
    except Exception as e:
        error = str(e).replace("\n"," * ")
        return jsonify({'status':False, "error": f"{error}"}),500

@campaign_bp.route('/get_campaigns_list', methods=['GET'])
@login_required
@admin_required
def campaign_list_api():
    try:
        token_data = get_token_data()
        user_id = token_data.get('user_id')
        result = db.campaign_details.find({"user_id":user_id},{"_id":0})
        return list(result)
    except Exception as e:
        return []

@campaign_bp.route('/get_campaign_detail/<campaign_id>', methods=['GET'])
@login_required
@admin_required
def get_campaigns_details_api(campaign_id: str):
    try:
        token_data = get_token_data()
        user_id = token_data.get('user_id')
        result = db.campaign_details.find_one({"user_id":user_id,"campaign_id":campaign_id},{"_id":0})
        return dict(result)
    except Exception as e:
        return []

@campaign_bp.route('/delete_campaign/<campaign_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_campaign_api(campaign_id: str):
    try:
        token_data = get_token_data()
        user_id = token_data.get('user_id')
        result = db.campaign_details.delete_one({"user_id":user_id,"campaign_id":campaign_id})
        if result.deleted_count == 0:
            return jsonify({"error": "Campaign not found in DB"}), 404
        return jsonify({"message": "Campaign deleted successfully"}), 200
    except Exception as e:
        print(str(e))
        return jsonify({"error": f"{str(e)}"}), 404