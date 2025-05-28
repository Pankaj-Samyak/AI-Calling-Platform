from datetime import datetime
from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash

from src.database.mongodb import db
from src.logger.log import Log_class
from src.user_utils.utils import generate_unique_id
from src.user_utils.send_password import send_password_email, forget_password
from src.user_utils.auth import create_token, login_required, admin_required, authenticate_user, get_token_data

user_bp = Blueprint('user_bp', __name__)
logg_obj = Log_class("logs", "user_bp.txt")

def current_timestamp():
    return datetime.utcnow()

# --------------------------
# ----User-Mangement-API----
# --------------------------
@user_bp.route('/signup', methods=['POST'])
def signup():
    try:
        logg_obj.Info_Log("-----------signup----------------")
        data = request.get_json()
        required_fields= [
            "name", "role", "email", "password",
            "phone_no", "pincode", "city", "state", "country", "address"
        ]
        missing_fields = list(filter(lambda x : not bool(x in data),required_fields))
        if missing_fields:
            logg_obj.Info_Log("Missing required fields")
            return jsonify({'error': f'Missing required fields: {missing_fields}'}), 400

        # Check if email already exists
        if db.users.find_one({'email': data['email']}):
            logg_obj.Info_Log("Email already exists")
            return jsonify({'error': 'Email already exists'}), 400

        # Set creation time
        data['created_at'] = current_timestamp()
        data['status'] = "active"
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

@user_bp.route('/login', methods=['POST'])
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

@user_bp.route('/forget_password', methods=['POST'])
def forget_password_api():
    try:
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
        return jsonify({'message': 'Password forget email sent'})
    except Exception as e:
        return jsonify({'message': 'Failed password forget request', "error": str(e)})

@user_bp.route('/reset_password', methods=['POST'])
def reset_password_api():
    try:
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
    except Exception as e:
        return jsonify({'message': 'Failed reset password request!', "error": str(e)})

# --------------------------------------------------------------------------------------#
@user_bp.route('/add_user', methods=['POST'])
@login_required
@admin_required
def add_user():
    try:
        logg_obj.Info_Log("-----------add_user----------------")
        data = request.get_json() or {}
        required_fields= [
            "name", "role", "email",
            "phone_no", "pincode", "city", "state", "country", "address"
        ]

        missing_fields = list(filter(lambda x : not bool(x in data),required_fields))
        if missing_fields:
            logg_obj.Info_Log("Missing required fields")
            return jsonify({'error': f'Missing required fields: {missing_fields}'}), 400

        if db.users.find_one({'email': data['email']}):
            logg_obj.Info_Log("Email already exists")
            return jsonify({'error': 'Email already exists'}), 400

        # Set creation details.
        token_data = get_token_data()
        user_id = token_data.get('user_id')
        data['created_at'] = current_timestamp()
        data['created_by'] = user_id
        data['status'] = "active"
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
        return jsonify({'message': 'User not created.', 'error': str(e)}),400

@user_bp.route('/get_users', methods=['GET'])
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

@user_bp.route('/update_user', methods=['POST'])
@login_required
@admin_required
def update_user():
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id')
        #--------------------------------------------------------------#
        required_fields= [
            "user_id", "name", "role","status", "email",
            "phone_no", "pincode", "city", "state", "country", "address"
        ]
        missing_fields = list(filter(lambda x : not bool(x in data),required_fields))
        if missing_fields:
            logg_obj.Info_Log("Missing required fields")
            return jsonify({'error': f'Missing required fields: {missing_fields}'}), 400
        #--------------------------------------------------------------#
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        if not db.users.find_one({'user_id': user_id}):
            return jsonify({'error': 'User not exists'}), 400
        update_fields = {k: v for k, v in data.items() if k != 'user_id'}
        db.users.update_one({'user_id': user_id}, {'$set': update_fields})
        return jsonify({'message': 'User updated successfully'})
    except Exception as e:
        return jsonify({'message': 'update user api request failed!', 'error': str(e)}),400

@user_bp.route('/delete_user', methods=['POST'])
@login_required
@admin_required
def delete_user():
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        result = db.users.delete_one({'user_id': user_id})
        if result.deleted_count == 0:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({'message': 'User deleted successfully'})
    except Exception as e:
        return jsonify({'message': 'User deleted failed', 'error': str(e)}),400