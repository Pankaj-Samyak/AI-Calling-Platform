import string
import random

#--------------------------------User_Id-Generator----------------------------#
def generate_unique_id():
        characters = string.ascii_letters + string.digits
        return ''.join(random.choices(characters, k=8))

#------------------------Campaign-Template-Validator--------------------------#
def validate_template(template: str, campaign_columns: list[str]) -> list[str]:
    errors = []
    try:
        # Check balanced braces
        open_braces = template.count('{')
        close_braces = template.count('}')
        if open_braces != close_braces:
              errors.append(f"Unmatched braces: {{ count = {open_braces} vs }} count = {close_braces}")

        # Extract placeholders
        formatter = string.Formatter()
        placeholders = {field_name for _, field_name, _, _ in formatter.parse(template) if field_name}

        # Find placeholders not in columns
        for ph in placeholders:
                if ph not in campaign_columns:
                        errors.append(f"Placeholder {{{ph}}} is not in campaign_columns")
        return errors
    except Exception as e:
        errors.append(f"error in validate_template function: {str(e)}")