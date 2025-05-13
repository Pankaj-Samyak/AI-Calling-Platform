# AI Calling Platform

A robust outbound calling system that enables automated voice calls with DTMF (keypad) input handling.

## 📋 Overview

The AI Calling Platform is designed to automate outbound calls with scripted voice messages and DTMF-based user interactions. This Phase 1 implementation focuses on building a solid foundation with fixed voice scripts and keypad responses.

## 🚀 Features

### Core Functionality
- Campaign Management with CSV upload support
- Script Template Engine with variable substitution
- Text-to-Speech (TTS) integration
- Dialer Integration (Exotel/Twilio/Gupshup)
- DTMF Input Capture
- Call Status Tracking
- Admin Dashboard

### User Management
- User Authentication & Authorization
- Role-based Access Control
- Password Management
- User Profile Management

### Document Management
- CSV/Excel File Upload
- Document Storage and Retrieval
- Document History Tracking

## 🛠️ Technical Stack

### Backend
- Python 3.x
- Flask Framework
- MongoDB Database
- JWT Authentication

### Dependencies
- Flask & Flask-CORS
- PyMongo
- Pandas
- Python-dotenv
- PyJWT
- Other utilities (see requirements.txt)

## 📦 Project Structure

```
AI-Calling-Platform/
├── app.py              # Main application file
├── requirements.txt    # Project dependencies
├── src/               # Source code directory
│   ├── database/      # Database related code
│   ├── user_utils/    # User management utilities
│   └── logger/        # Logging functionality
├── logs/              # Application logs
└── venv/              # Virtual environment
```

## 🚀 Getting Started

### Prerequisites
- Python 3.x
- MongoDB
- Virtual Environment (recommended)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd AI-Calling-Platform
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file with the following variables:
```
MONGODB_URI=your_mongodb_uri
JWT_SECRET=your_jwt_secret
EMAIL_CONFIG=your_email_config
```

5. Run the application:
```bash
python app.py
```

## 📝 API Endpoints

### Authentication
- `POST /signup` - User registration
- `POST /login` - User login
- `POST /forget_password` - Password recovery
- `POST /reset_password` - Password reset

### User Management
- `GET /get_users` - List all users (Admin only)
- `POST /update_user_data` - Add new user
- `POST /update_user` - Update user details
- `POST /delete_user` - Delete user

### Document Management
- `POST /upload_documents` - Upload CSV/Excel files
- `GET /get_documents` - List uploaded documents
- `GET /view_document/<file_id>` - View document
- `DELETE /delete_document/<file_id>` - Delete document

## 📊 CSV Format

Required fields for campaign upload:
- name
- phone
- date
- time
- amount

## 📈 Output Format

Call logs are stored in JSON format with the following structure:
```json
{
    "phone": "string",
    "status": "string",
    "dtmf_response": "string",
    "timestamp": "datetime"
}
```

## 🚧 Pending Features

### Phase 1 Pending Items
- TTS Engine Integration
- Dialer Integration (Exotel/Twilio/Gupshup)
- DTMF Capture Implementation
- Call Status Tracking System
- Campaign Management Dashboard
- Script Template Engine

### Future Phases
- LLM Integration
- Speech-to-Text (STT) Implementation
- Advanced Analytics
- Real-time Call Monitoring
- Custom Voice Bot Training

## 🔒 Security

- JWT-based authentication
- Password hashing
- Role-based access control
- Secure file upload handling
- Environment variable configuration

## 📝 Logging

The application maintains detailed logs in the `logs` directory:
- Application logs
- Error logs
- User activity logs

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.