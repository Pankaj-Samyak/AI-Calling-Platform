from template import TemplateEngine

def demonstrate_appointment_template():
    # Initialize the template engine
    engine = TemplateEngine()
    
    # Appointment Confirmation Template
    appointment_template = """
    ============================================
    APPOINTMENT CONFIRMATION
    ============================================
    
    Dear {{name}},
    
    Your appointment has been confirmed with the following details:
    
    Date: {{date}}
    Time: {{time}}
    Amount: ${{amount}}
    
    Contact Information:
    Phone: {{phone}}
    
    Please arrive 10 minutes before your scheduled time.
    If you need to reschedule, please call us at least 24 hours in advance.
    
    Thank you for choosing our service!
    ============================================
    """
    
    # Example variables
    appointment_vars = {
        "name": "John Smith",
        "phone": "+1 (555) 123-4567",
        "date": "2024-03-15",
        "time": "14:30",
        "amount": "150.00"
    }
    
    # Render the template
    result = engine.render(appointment_template, appointment_vars)
    print(result)
    
    # Example with different data
    print("\n=== Another Appointment Example ===")
    another_appointment = {
        "name": "Sarah Johnson",
        "phone": "+1 (555) 987-6543",
        "date": "2024-03-20",
        "time": "10:00",
        "amount": "200.00"
    }
    
    result2 = engine.render(appointment_template, another_appointment)
    print(result2)

if __name__ == "__main__":
    demonstrate_appointment_template() 