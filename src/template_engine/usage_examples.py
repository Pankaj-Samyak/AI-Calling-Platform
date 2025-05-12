from template import TemplateEngine

def demonstrate_template_usage():
    # Initialize the template engine
    engine = TemplateEngine()
    
    # Example 1: Email Template
    print("\n=== Example 1: Email Template ===")
    email_template = """
    Dear {{customer_name}},

    Thank you for your order #{{order_number}}.
    Your order total is ${{order_amount}}.
    
    Estimated delivery date: {{delivery_date}}
    
    Best regards,
    {{company_name}} Support Team
    """
    
    email_vars = {
        "customer_name": "Alice Smith",
        "order_number": "ORD-2024-001",
        "order_amount": "149.99",
        "delivery_date": "2024-03-15",
        "company_name": "TechStore"
    }
    
    email_result = engine.render(email_template, email_vars)
    print(email_result)
    
    # Example 2: Configuration Template
    print("\n=== Example 2: Configuration Template ===")
    config_template = """
    # Database Configuration
    DB_HOST={{db_host}}
    DB_PORT={{db_port}}
    DB_NAME={{db_name}}
    DB_USER={{db_user}}
    DB_PASSWORD={{db_password}}
    
    # API Settings
    API_KEY={{api_key}}
    API_ENDPOINT={{api_endpoint}}
    """
    
    config_vars = {
        "db_host": "localhost",
        "db_port": "5432",
        "db_name": "myapp_db",
        "db_user": "admin",
        "db_password": "secret123",
        "api_key": "abc123xyz",
        "api_endpoint": "https://api.example.com/v1"
    }
    
    config_result = engine.render(config_template, config_vars)
    print(config_result)
    
    # Example 3: HTML Template
    print("\n=== Example 3: HTML Template ===")
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{page_title}}</title>
    </head>
    <body>
        <h1>Welcome to {{site_name}}</h1>
        <div class="user-info">
            <p>Hello, {{user_name}}!</p>
            <p>Your account type: {{account_type}}</p>
            <p>Last login: {{last_login}}</p>
        </div>
    </body>
    </html>
    """
    
    html_vars = {
        "page_title": "User Dashboard",
        "site_name": "MyAwesomeApp",
        "user_name": "John Doe",
        "account_type": "Premium",
        "last_login": "2024-03-10 14:30:00"
    }
    
    html_result = engine.render(html_template, html_vars)
    print(html_result)
    
    # Example 4: Error Message Template
    print("\n=== Example 4: Error Message Template ===")
    error_template = """
    Error: {{error_code}}
    Message: {{error_message}}
    Time: {{timestamp}}
    Request ID: {{request_id}}
    """
    
    error_vars = {
        "error_code": "ERR_404",
        "error_message": "Resource not found",
        "timestamp": "2024-03-10 15:45:22",
        "request_id": "req-123456"
    }
    
    error_result = engine.render(error_template, error_vars)
    print(error_result)

if __name__ == "__main__":
    demonstrate_template_usage() 