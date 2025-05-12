from template import TemplateEngine

def test_template_engine():
    # Create an instance of the template engine
    engine = TemplateEngine()
    
    # Example 1: Simple string template
    template = "Hello, {{name}}! Welcome to {{platform}}."
    variables = {
        "name": "John",
        "platform": "AI Calling Platform"
    }
    result = engine.render(template, variables)
    print("Example 1 - String Template:")
    print(f"Template: {template}")
    print(f"Variables: {variables}")
    print(f"Result: {result}\n")
    
    # Example 2: Template with missing variables
    template2 = "User: {{username}}, Role: {{role}}, Department: {{department}}"
    variables2 = {
        "username": "john_doe",
        "role": "admin"
    }
    result2 = engine.render(template2, variables2)
    print("Example 2 - Template with Missing Variables:")
    print(f"Template: {template2}")
    print(f"Variables: {variables2}")
    print(f"Result: {result2}\n")
    
    # Example 3: Template with numbers and special characters
    template3 = "Order #{{order_id}} - Total: ${{amount}} - Status: {{status}}"
    variables3 = {
        "order_id": "12345",
        "amount": "99.99",
        "status": "completed"
    }
    result3 = engine.render(template3, variables3)
    print("Example 3 - Template with Numbers and Special Characters:")
    print(f"Template: {template3}")
    print(f"Variables: {variables3}")
    print(f"Result: {result3}")

if __name__ == "__main__":
    test_template_engine() 