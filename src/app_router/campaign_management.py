from datetime import datetime,timedelta
from flask import Blueprint, jsonify, request
from src.database.mongodb import db, get_dataframe
from src.user_utils.utils import validate_template
from src.user_utils.auth import login_required, admin_required, get_token_data

from src.logger.log import Log_class
from src.template_engine.campaign_template_generator import CampaignTemplateGenerator

campaign_bp = Blueprint('campaign_bp', __name__)
logg_obj = Log_class("logs", "campaign_bp.txt")

#----------------------------------------------#
#-------------Get-Campaign-Tempalates----------#
#----------------------------------------------#
@campaign_bp.route('/generate_campaign_templates', methods=['POST'])
@login_required
@admin_required
def generate_campaign_templates_api():
    try:
        logg_obj.Info_Log("-----------generate_campaign_templates_api----------------")
        # Get campaign details from form data
        document_id = request.form.get('document_id')
        campaign_name = request.form.get('campaign_name')
        campaign_description = request.form.get('campaign_description')
        #---------------------------------------------------------------#
        # Check if campaign already exists
        if db.campaign_details.find_one({'campaign_name': campaign_name}):
            return jsonify({'error': 'campaign already exists'}), 400
        #-----------------------------------------------------------------------------#
        df = get_dataframe(document_id)
        if df.empty:
            logg_obj.Info_Log("No file found!")
            return jsonify({'error': 'No file found!'}), 400

        #correct the format of df columns.
        campaign_columns = [col.strip().replace(' ', '_') for col in df.columns]
        df.columns = campaign_columns

        #----------------LLM-Campaign-Template---------------#
        campaign_obj = CampaignTemplateGenerator()
        campaign_templates = campaign_obj.generate_templates(campaign_columns, campaign_name,campaign_description)
        #---------------Generate-Campaign-Template---------------#
        token_data = get_token_data()
        user_id = token_data.get('user_id')
        #_________________________________________________________#
        campaign_data = {
                            "campaign_name":campaign_name,
                            "campaign_description":campaign_description,
                            "campaign_templates": list(campaign_templates.values()),
                            "document_id" : document_id,
                            "created_by": user_id,
                        }
        # Insert multiple documents
        result = db.campaign_template.insert_one(campaign_data)
        #--------------------------#
        db.campaign_template.update_one(
                {"_id": result.inserted_id},
                {"$set": {"campaign_template_id": str(result.inserted_id)}}
            )
        logg_obj.Info_Log("Document uploaded successfully")
        return {'message': f'Campaign templates created successfully.', "campaign_template_id":str(result.inserted_id)}

    except Exception as e:
        print(str(e))
        return {"error": str(e)}

@campaign_bp.route('/get_campaign_templates/<campaign_template_id>', methods=['GET'])
@login_required
@admin_required
def get_campaign_templates_api(campaign_template_id: str):
    try:
        token_data = get_token_data() or {}
        created_by = token_data.get('user_id')
        query = {"created_by":created_by}
        if campaign_template_id.strip() != "":
            query["campaign_template_id"] = campaign_template_id
            result = db.campaign_template.find_one(query,{"_id":0})
            return dict(result)
        else:
            return {}
    except Exception as e:
        print(str(e))
        return {}

@campaign_bp.route('/get_campaign_templates', methods=['GET'])
@login_required
@admin_required
def get_all_campaign_templates_api():
    try:
        token_data = get_token_data() or {}
        created_by = token_data.get('user_id')
        query = {"created_by":created_by}
        result = db.campaign_template.find(query,{"_id":0})
        return list(result)
    except Exception as e:
        print(str(e))
        return []


@campaign_bp.route('/add_campaign', methods=['POST'])
@login_required
@admin_required
def add_campaign_api():
    try:
        logg_obj.Info_Log("-----------run_campaign_api----------------")
        # Get campaign details from form data
        document_id = request.form.get('document_id')
        campaign_name = request.form.get('campaign_name')
        campaign_description = request.form.get('campaign_description')
        campaign_template = request.form.get('campaign_template')
        #---------------------------------------------------------------#
        # Check if campaign already exists
        if db.campaign_details.find_one({'campaign_name': campaign_name}):
            return jsonify({'error': 'campaign already exists'}), 400
        #---------------------------------------------------------------#

        df = get_dataframe(document_id)
        if df.empty:
            logg_obj.Info_Log("No file found!")
            return jsonify({'error': 'No file found!'}), 400
        #correct the format of df columns.
        campaign_templates_list = []
        campaign_columns = [col.strip().replace(' ', '_') for col in df.columns]
        df.columns = campaign_columns
        #----------------Custom-Campaign-Template---------------#
        flag = validate_template(campaign_template, campaign_columns)
        if flag:
            return {"error": ", ".join(flag)}
        else:
            campaign_obj = CampaignTemplateGenerator()
            row_list = [dict(row) for _ , row in df.iterrows()]
            for row in row_list:
                campaign_templates = {"template": campaign_template}
                templates = campaign_obj.evaluate_fstring_templates(campaign_templates, row)
                row["campaign_name"] = campaign_name
                row["campaign_description"] = campaign_description
                row["campaign_templates"] = templates
                campaign_templates_list.append(row)

        # Insert multiple documents
        result = db.campaign_details.insert_many(campaign_templates_list)
        #--------------------------#
        token_data = get_token_data()
        user_id = token_data.get('user_id')
        # Loop through inserted IDs and update each document
        for inserted_id in result.inserted_ids:
            db.campaign_details.update_one(
                {"_id": inserted_id},
                {"$set": {"campaign_id": str(inserted_id),"created_by":user_id, "document_id": str(document_id)}}
            )
        logg_obj.Info_Log("Document uploaded successfully")
        return {
            'message': f'Campaign added successfully, total rows are {len(result.inserted_ids)}'
        }
    except Exception as e:
        print(str(e))
        return {"error": str(e)}

@campaign_bp.route('/campaign_list', methods=['GET'])
@login_required
@admin_required
def campaign_list_api():
    try:
        # Get user ID from token
        token_data = get_token_data()
        user_id = token_data.get('user_id')
        # Insert multiple documents
        result = db.campaign_details.find({"created_by":user_id},{"_id":0})
        return list(result)
    except Exception as e:
        print(str(e))
        return result

@campaign_bp.route('/delete_campaign', methods=['POST'])
@login_required
@admin_required
def delete_campaign_api():
    try:
        campaign_id = request.form.get('campaign_id')
        # Insert delete_many documents
        result = db.campaign_details.delete_many({"campaign_id":campaign_id})
        if result.deleted_count > 0:
            return {'message': f'{result.deleted_count} campaign(s) deleted successfully.'}
        else:
            return {'message': 'No campaign found with the given campaign_id.'}
    except Exception as e:
        print(str(e))
        return {"error": str(e)}