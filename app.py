import os
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

from src.user_utils.auth import (
    create_token, login_required,
    admin_required, authenticate_user,
    get_token_data
)

from src.user_utils.utils import generate_unique_id,validate_template
from src.database.mongodb import db, get_dataframe
from src.user_utils.send_password import send_password_email, forget_password
from src.logger.log import Log_class
from src.template_engine.campaign_template_generator import CampaignTemplateGenerator

# ----------------------
# App Initialization
# ----------------------
app = Flask(__name__)
CORS(app)
load_dotenv()
logg_obj = Log_class("logs", "AppLog.txt")

#Taking current time.
def current_timestamp():
    return datetime.utcnow()

# ----------------------
# Configurations
# ----------------------
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.xls', '.xlsx', '.csv', '.txt'}

# Helper to check file types
def allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS

# ----------------------
# 1. User Signup
# ----------------------
@app.route('/signup', methods=['POST'])
def signup():
    try:
        logg_obj.Info_Log("-----------signup----------------")
        data = request.get_json()
        required = ['name', 'email', 'password', 'role']
        if not all(field in data for field in required):
            logg_obj.Info_Log("Missing required fields")
            return jsonify({'error': 'Missing required fields'}), 400

        # Check if email already exists
        if db.users.find_one({'email': data['email']}):
            logg_obj.Info_Log("Email already exists")
            return jsonify({'error': 'Email already exists'}), 400

        # Set creation time
        data['created_at'] = current_timestamp()

        # Hash the password
        unhashed_password = data['password']
        hashed_password = generate_password_hash(unhashed_password)

        # Insert user into the database
        data['password'] = hashed_password
        inserted = db.users.insert_one(data)
        mongo_id = inserted.inserted_id
        data['user_id'] = mongo_id
        db.users.update_one(
            {"_id": mongo_id},
            {"$set": {"user_id": str(mongo_id)}}
        )
        logg_obj.Info_Log("User registered successfully")

        # Send confirmation email
        sent = send_password_email(data['email'], unhashed_password)
        if not sent:
            logg_obj.Info_Log("User registered, but email sending failed")
            return jsonify({
                'message': 'User registered, but email sending failed',
                'user_id': str(mongo_id)
            })
        return jsonify({'message': 'User registered successfully', 'user_id': str(mongo_id)})

    except Exception as e:
        return jsonify({'message': 'User not registered.', 'error': str(e)})

# ----------------------
# User Login
# ----------------------
@app.route('/login', methods=['POST'])
def login():
    try:
        logg_obj.Info_Log("---------login----------")
        logg_obj.Info_Log("Login API Initiated!")
        data = request.get_json() or {}
        email = data.get('email')
        password = data.get('password')

        logg_obj.Info_Log("Check the email and password.")
        if not email or not password:
            logg_obj.Info_Log("Email and password are required")
            return jsonify({'error': 'Email and password are required'}), 400

        user = authenticate_user(email, password)
        print(user)
        if not user:
            logg_obj.Info_Log("Invalid credentials")
            return jsonify({'error': 'Invalid credentials'}), 401

        token = create_token(user['user_id'], user['name'], user['role'])
        logg_obj.Info_Log("JWT token generated")
        logg_obj.Info_Log("-------------------")
        return jsonify({
            'status': 'success',
            "user_id":user['user_id'],
            'name': user['name'],
            "email":email,
            'role': user['role'],
            'token': token
        })
    except Exception as e:
        logg_obj.Error_Log(str(e))
        return jsonify({'status':"unsuccess","error":str(e)}), 401

# ----------------------
# 2. User Management
# ----------------------
@app.route('/get_users', methods=['GET'])
@login_required
@admin_required
def get_users():
    try:
        logg_obj.Info_Log("---------get_users----------")
        logg_obj.Info_Log("get_users api start")
        users = list(db.users.find({}, {'_id': 0, 'password': 0}))
        logg_obj.Info_Log("user data fetch successfully")
        logg_obj.Info_Log("----------------------------")
        return jsonify(users)
    except Exception as e:
        logg_obj.Error_Log(str(e))
        return jsonify({'error': 'Failed to get users'}), 500

#----------------ADD-USER-NEW--------------#
@app.route('/update_user_data', methods=['POST'])
@login_required
@admin_required
def add_user_data():
    try:
        logg_obj.Info_Log("------------add_user------------")
        logg_obj.Info_Log("update_user api start")
        data = request.get_json()
        required_fields = [
            "name", "role", "email", "status",
            "phone_no", "pincode", "city", "state", "country", "address"
        ]

        # Check for missing required fields
        missing = [field for field in required_fields if field not in data]
        if missing:
            logg_obj.Info_Log(f'Missing required fields: {", ".join(missing)}')
            return jsonify({'error': f'Missing required fields: {", ".join(missing)}'}), 400

        if db.users.find_one({"email": data["email"]}):
            logg_obj.Info_Log("Email already exists")
            return jsonify({"error": "Email already exists"}), 400

        #Extra Fileds
        data["created_at"] = current_timestamp()

        # Insert first to get the generated _id
        inserted = db.users.insert_one(data)
        mongo_id = inserted.inserted_id
        logg_obj.Info_Log(f"Insert user successfully, user_id: {str(e)}")

        #Generate Password:
        password = generate_unique_id()
        logg_obj.Info_Log(f"Generate Password successfully, Password: {password}")

        # Update document to include user_id as the same _id
        db.users.update_one(
            {"_id": mongo_id},
            {"$set": {"user_id": str(mongo_id),"password": generate_password_hash(password)}}
        )

        email_flag = send_password_email(data["email"],password)
        if not email_flag:
            logg_obj.Info_Log("User created successfully, but password not sent to email!")
            return jsonify({
                        "message": "User created successfully, but password not sent to email!",
                        "user_id": str(mongo_id),""
                        "password": password
                    })
        else:
            logg_obj.Info_Log("Email sent successfully for user credentials.")

        logg_obj.Info_Log("---------------------------")
        return jsonify({
            "message": "User created successfully",
            "user_id": str(mongo_id),
        })

    except Exception as e:
        logg_obj.Error_Log(str(e))
        logg_obj.Error_Log("---------------------------")
        return jsonify({"error": "Failed to add user"}), 500

@app.route('/add_user', methods=['POST'])
@login_required
@admin_required
def add_user():
    try:
        logg_obj.Info_Log("-----------add_user----------------")
        data = request.get_json() or {}
        required = ['name', 'email', 'role', 'status']

        if not all(field in data for field in required):
            logg_obj.Info_Log("Missing required fields")
            return jsonify({'error': 'Missing required fields'}), 400

        if db.users.find_one({'email': data['email']}):
            logg_obj.Info_Log("Email already exists")
            return jsonify({'error': 'Email already exists'}), 400

        # Set creation details.
        token_data = get_token_data()
        user_id = token_data.get('user_id')
        data['created_at'] = current_timestamp()
        data['created_by'] = user_id
        #----------------------------------#
        inserted = db.users.insert_one(data)
        mongo_id = inserted.inserted_id

        logg_obj.Info_Log("User added successfully")
        # Generate and save password
        password = generate_unique_id()
        db.users.update_one(
            {'_id': mongo_id},
            {'$set': {'user_id': str(mongo_id), 'password': generate_password_hash(password)}}
        )

        # Send email with password
        sent = send_password_email(data['email'], password)
        if not sent:
            logg_obj.Info_Log("User created, but send email failed")
            return jsonify({
                'message': 'User created, but send email failed',
                'user_id': str(mongo_id),
                'password': password
            })

        return jsonify({'message': 'User created successfully', 'user_id': str(mongo_id)})

    except Exception as e:
        return jsonify({'message': 'User not created.', 'error': str(e)})

@app.route('/update_user', methods=['POST'])
@login_required
@admin_required
def update_user():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    if not db.users.find_one({'user_id': user_id}):
        return jsonify({'error': 'User not exists'}), 400
    update_fields = {k: v for k, v in data.items() if k != 'user_id'}
    db.users.update_one({'user_id': user_id}, {'$set': update_fields})
    return jsonify({'message': 'User updated successfully'})

@app.route('/delete_user', methods=['POST'])
@login_required
@admin_required
def delete_user():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    result = db.users.delete_one({'user_id': user_id})
    if result.deleted_count == 0:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'message': 'User deleted successfully'})

# ----------------------
# 3. Password Reset
# ----------------------
@app.route('/forget_password', methods=['POST'])
def forget_password_api():
    data = request.get_json() or {}
    email = data.get('email')
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    if not db.users.find_one({'email': email}):
        return jsonify({'error': 'User not exists'}), 400
    new_pass = generate_unique_id()
    db.users.update_one(
        {'email': email},
        {'$set': {'password': generate_password_hash(new_pass)}}
    )
    sent = forget_password(email, new_pass)
    if not sent:
        return jsonify({'message': 'Password generated but email failed', 'password': new_pass})
    return jsonify({'message': 'Password reset email sent'})

@app.route('/reset_password', methods=['POST'])
def reset_password_api():
    data = request.get_json() or {}
    email = data.get('email')
    old_pass = data.get('old_password')
    new_pass = data.get('new_password')
    if not all([email, old_pass, new_pass]):
        return jsonify({'error': 'Email, old_password, new_password are required'}), 400
    user = db.users.find_one({'email': email})
    if not user or not user.get('password'):
        return jsonify({'error': 'User not exists'}), 400
    # Should use check_password_hash instead
    if not check_password_hash(user['password'], old_pass):
        return jsonify({'error': 'Incorrect old password'}), 400
    db.users.update_one({'email': email}, {'$set': {'password': generate_password_hash(new_pass)}})
    return jsonify({'message': 'Password updated successfully'})


# ------------------------
# Document Management API
# ------------------------
@app.route('/upload_documents', methods=['POST'])
@login_required
@admin_required
def upload_excel():
    try:
        logg_obj.Info_Log("-----------upload_documents----------------")
        # Get campaign details from form data
        campaign_name = request.form.get('campaign_name')
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')

        # Validate required fields
        if not all([campaign_name, from_date, to_date]):
            logg_obj.Info_Log("Missing required fields")
            return jsonify({'error': 'Missing required fields: campaign_name, from_date, to_date'}), 400

        # Check if campaign name already exists
        if db.documents.find_one({'campaign_name': campaign_name}):
            logg_obj.Info_Log("Campaign name already exists")
            return jsonify({'error': 'Campaign name already exists'}), 400

        # Check if file is present
        if 'file' not in request.files:
            logg_obj.Info_Log("No file part")
            return jsonify({'error': 'No file part'}), 400

        file = request.files['file']
        if file.filename == '':
            logg_obj.Info_Log("No selected file")
            return jsonify({'error': 'No selected file'}), 400

        # Validate file type
        if not allowed_file(file.filename):
            logg_obj.Info_Log("Invalid file type")
            return jsonify({'error': f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

        # Get user ID from token
        token_data = get_token_data()
        user_id = token_data.get('user_id')
        # Create unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"

        # Save file to temporary location
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, unique_filename)
        file.save(file_path)

        # Read file content
        with open(file_path, 'rb') as f:
            file_content = f.read()

        # Store file in GridFS
        metadata = {
            'user_id': user_id,
            'campaign_name': campaign_name,
            'from_date': from_date,
            'to_date': to_date,
            'upload_date': current_timestamp(),
            'file_type': Path(filename).suffix.lower()
        }

        file_id = db.store_file(file_content, unique_filename, metadata)

        # Create document record with reference to GridFS file
        document = {
            'user_id': user_id,
            'campaign_name': campaign_name,
            'from_date': from_date,
            'to_date': to_date,
            'filename': filename,
            'file_id': file_id,  # Store GridFS file ID
            'upload_date': current_timestamp(),
            'file_type': Path(filename).suffix.lower()
        }

        # Save to MongoDB
        result = db.documents.insert_one(document)

        # Clean up temporary file
        os.remove(file_path)

        logg_obj.Info_Log("Document uploaded successfully")
        return jsonify({
            'message': 'Document uploaded successfully',
            'document_id': str(result.inserted_id)
        })

    except Exception as e:
        logg_obj.Error_Log(str(e))
        return jsonify({'error': 'Failed to upload document', 'details': str(e)}), 500

@app.route('/document_list', methods=['GET'])
# @login_required
def get_documents():
    docs = list(db.documents.find({}, {'_id': 0}))
    return jsonify(docs)

@app.route('/view_document/<file_id>', methods=['GET'])
def view_document(file_id: str):
    data, meta = db.get_file(file_id)
    filename = f"{meta['campaign_name']}.{meta['file_type']}"
    import mimetypes
    mime, _ = mimetypes.guess_type(filename)
    return data, 200, {
        'Content-Type': mime or 'application/octet-stream',
        'Content-Disposition': f'inline; filename="{filename}"'
    }

@app.route('/delete_document/<file_id>', methods=['DELETE'])
@login_required
def delete_document(file_id: str):
    try:
        result = db.documents.delete_one({"file_id":file_id}, {'_id': 0})
        return {"message": f"{int(result.deleted_count)}, document delete successfully"}
    except Exception as e:
        return {}


#----------------------------------------------#
#-------------Get-Campaign-Tempalates----------#
#----------------------------------------------#
@app.route('/generate_campaign_templates', methods=['POST'])
@login_required
@admin_required
def generate_campaign_templates_api():
    try:
        logg_obj.Info_Log("-----------generate_campaign_templates_api----------------")
        # Get campaign details from form data
        document_id = request.form.get('document_id')
        campaign_name = request.form.get('campaign_name')
        campaign_description = request.form.get('campaign_description')
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

@app.route('/get_campaign_templates/<campaign_template_id>', methods=['GET'])
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

@app.route('/get_campaign_templates', methods=['GET'])
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
#-----------------------------------------------#
@app.route('/add_campaign', methods=['POST'])
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

@app.route('/campaign_list', methods=['GET'])
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

@app.route('/delete_campaign', methods=['POST'])
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)