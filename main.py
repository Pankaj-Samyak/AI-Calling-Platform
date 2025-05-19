from flask import Flask
from flask_cors import CORS
from src.app_router.user_management import user_bp
from src.app_router.file_management import file_bp
from src.app_router.campaign_management import campaign_bp
from src.app_router.call_management import call_bp
from src.app_router.integration import integration_bp

app = Flask(__name__)
CORS(app)

# Register your blueprints
app.register_blueprint(user_bp, url_prefix='/users')
app.register_blueprint(file_bp, url_prefix='/files')
app.register_blueprint(campaign_bp, url_prefix='/campaign')
app.register_blueprint(call_bp, url_prefix='/call')
app.register_blueprint(integration_bp, url_prefix='/integration')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)