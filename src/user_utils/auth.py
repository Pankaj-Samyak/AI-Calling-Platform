import jwt
import datetime
from typing import Optional, Dict, Any
from functools import wraps
from flask import request, jsonify
from werkzeug.security import check_password_hash
from ..database.mongodb import db

JWT_SECRET = "AI_Calling"
JWT_ALGORITHM = "HS256"

def create_token(user_id: str,user_name:str, role: str) -> str:
    """Create JWT token for user."""
    payload = {
        "user_id": user_id,
        "user_name":user_name,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token and return payload if valid."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        try:
            token = token.split(" ")[1]  # Remove "Bearer " prefix
            payload = verify_token(token)
            if not payload:
                return jsonify({"error": "Invalid token"}), 401

            # Add user info to request context
            request.user = payload
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({"error": "Authentication failed"}), 401
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(request, 'user') or request.user.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated

def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate user and return user info if valid."""
    try:
        user = db.users.find_one({"email": email},{"_id": 0})
        print(user, "afdasfsdfasd")
        if user and check_password_hash(user.get("password"), password):
            return {
                "user_id": str(user["user_id"]),
                "name": str(user["name"]),
                "role": user["role"]
            }
        return None
    except Exception as e:
        return str(e)

#-----------Get_Token_Data-----------#
def get_token_data():
    token = request.headers.get("Authorization")
    if not token:
        return False
    try:
        if token.startswith("Bearer "):
            token = token.split(" ")[1]
        token = token.strip()
        payload = verify_token(token)
        return payload
    except Exception as e:
        return False