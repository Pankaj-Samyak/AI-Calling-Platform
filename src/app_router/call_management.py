from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from src.database.mongodb import db
from src.user_utils.utils import validate_template
from src.user_utils.params import CallBatch, CampaignTemplates
from src.user_utils.auth import login_required, admin_required, get_token_data

from src.logger.log import Log_class
from src.template_engine.campaign_template_generator import CampaignTemplateGenerator

call_bp = Blueprint('call_bp', __name__)
logg_obj = Log_class("logs", "call_bp.txt")

#------------------------------------------#
#-------------Campaign-Management----------#
#------------------------------------------#
@call_bp.route('/generate_campaign_templates', methods=['POST'])
@login_required
@admin_required
def generate_campaign_templates_api():
    try:
        templates_data = CampaignTemplates.parse_raw(request.data).dict()
        #get tha all data from CampaignTemplate request.
        callDetails = templates_data.get("callDetails")
        campaign_id = templates_data.get("campaign_id")
        # Get user ID from token
        token_data = get_token_data()
        if token_data:
            camapign_data = dict(db.campaign_details.find_one({"campaign_id":campaign_id},{"_id":0}) )
            campaign_columns = list(callDetails[0].keys())
            #---------------------------------------#
            print(camapign_data)
            campaign_obj = CampaignTemplateGenerator()
            campaign_templates = campaign_obj.generate_templates(campaign_columns, camapign_data)
            return list(campaign_templates.values())
        else:
           return jsonify({'status':False, "error": "Authorization failed. Please provide a valid JWT token."}), 400
    except Exception as e:
        error = str(e).replace("\n"," * ")
        return jsonify({'status':False, "error": f"{error}"}), 500

@call_bp.route('/make_call_batch', methods=['POST'])
@login_required
@admin_required
def make_call_batch_api():
    try:
        callData = CallBatch.parse_raw(request.data).dict()
        campaign_obj = CampaignTemplateGenerator()
        #get tha all data from CallBatch request.
        batch_name = callData.get("batch_name")
        campaign_id = callData.get("campaign_id")
        campaign_template = callData.get("campaign_template")
        callDetails = callData.get("callDetails")
        scheduledTime = datetime.strptime(callData.get("scheduledTime"), "%d-%m-%Y %H:%M:%S")
        # Get user ID from token
        token_data = get_token_data()
        if token_data:
           campaign_columns = list(callDetails[0].keys())
           error = validate_template(campaign_template, campaign_columns)
           #------------------------------------------------------------#
           if error:
               return " ,".join(error)
           else:
                exist = db.call_batch_details.find_one({"created_by":token_data["user_id"], "batch_name":batch_name})
                if exist:
                   return jsonify({'status': False, "error": "Batch already exists in the database. Please use a different batch name."}), 400
                query = []
                for contact in callDetails:
                    contact["campaign_id"] = campaign_id
                    contact["batch_name"] = batch_name
                    contact["template"] = campaign_obj.evaluate_fstring_templates(campaign_template, contact)
                    contact["scheduledTime"] = scheduledTime
                    contact["created_at"] = datetime.utcnow()
                    contact["created_by"] = token_data["user_id"]
                    query.append(contact)
                result = db.call_batch_details.insert_many(query)
                return jsonify({'status': True, "message": f"Call batch successfully created. Total number of contacts: {len(result.inserted_ids)}."})
        else:
           return jsonify({'status':False, "error": "Authorization failed. Please provide a valid JWT token."}), 400
    except Exception as e:
        error = str(e).replace("\n"," * ")
        return jsonify({'status':False, "error": f"{error}"}), 500