# AI Calling Platform

A robust outbound calling system that enables automated voice calls with DTMF (keypad) input handling.

## 📋 Overview

The AI Calling Platform is designed to automate outbound calls with scripted voice messages and DTMF-based user interactions. This Phase 1 implementation focuses on building a solid foundation with fixed voice scripts and keypad responses.

## 🚀 Features

### Implemented Features

- User Authentication & Authorization
- Role-based Access Control
- Password Management
- User Profile Management
- Document Management (CSV/Excel File Upload)
- Basic Campaign Management
- Logging System
- Database Integration (MongoDB)

### Pending Features

- Text-to-Speech (TTS) Integration
- Dialer Integration (Exotel/Twilio/Gupshup)
- DTMF Input Capture
- Call Status Tracking
- Admin Dashboard
- Script Template Engine with variable substitution
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
- OpenAI
- PyMuPDF
- Cryptography

## 📦 Project Structure

```
AI-Calling-Platform/
├── main.py            # Main application file
├── requirements.txt   # Project dependencies
├── src/              # Source code directory
│   ├── app_router/   # API route handlers
│   ├── components/   # Core components
│   ├── database/     # Database related code
│   ├── template_engine/ # Template processing
│   ├── user_utils/   # User management utilities
│   └── logger/       # Logging functionality
├── logs/             # Application logs
└── venv/             # Virtual environment
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
python main.py
```

## 📝 API Endpoints

### Authentication

- `POST /users/signup` - User registration
- `POST /users/login` - User login
- `POST /users/forget_password` - Password recovery
- `POST /users/reset_password` - Password reset

### User Management

- `GET /users/get_users` - List all users (Admin only)
- `POST /users/update_user_data` - Add new user
- `POST /users/update_user` - Update user details
- `POST /users/delete_user` - Delete user

### Document Management

- `POST /files/upload_documents` - Upload CSV/Excel files
- `GET /files/get_documents` - List uploaded documents
- `GET /files/view_document/<file_id>` - View document
- `DELETE /files/delete_document/<file_id>` - Delete document

### Campaign Management

- `POST /campaign/create` - Create new campaign
- `GET /campaign/list` - List campaigns
- `GET /campaign/<campaign_id>` - Get campaign details

### Call Management

- `POST /call/initiate` - Initiate a call
- `GET /call/status/<call_id>` - Get call status

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

## 🚧 Future Enhancements

### Phase 2 Features

- TTS Engine Integration
- Dialer Integration (Exotel/Twilio/Gupshup)
- DTMF Capture Implementation
- Call Status Tracking System
- Campaign Management Dashboard
- Script Template Engine

### Phase 3 Features

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
