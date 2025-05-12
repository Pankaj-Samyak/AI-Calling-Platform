import pandas as pd
from typing import List, Dict, Optional
import openai
from template import TemplateEngine

class CampaignTemplateGenerator:
    def __init__(self, openai_api_key: str):
        self.template_engine = TemplateEngine()
        openai.api_key = openai_api_key
        
    def get_excel_columns(self, excel_data: pd.DataFrame) -> List[str]:
        """Extract column names from Excel data"""
        return list(excel_data.columns)
    
    def generate_templates(self, campaign_name: str, campaign_description: str, 
                         available_variables: List[str]) -> List[str]:
        """Generate multiple templates using OpenAI based on campaign details and variables"""
        
        prompt = f"""
        Generate 3 different templates for a campaign with the following details:
        Campaign Name: {campaign_name}
        Campaign Description: {campaign_description}
        
        Available variables to use in templates: {', '.join(available_variables)}
        
        Requirements:
        1. Each template should use all available variables
        2. Templates should be professional and engaging
        3. Use {{variable_name}} format for variables
        4. Provide templates in different styles (formal, casual, etc.)
        
        Format each template with a number and brief description.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional template generator."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse the response to extract templates
            templates = self._parse_openai_response(response.choices[0].message.content)
            return templates
            
        except Exception as e:
            raise Exception(f"Error generating templates: {str(e)}")
    
    def _parse_openai_response(self, response: str) -> List[str]:
        """Parse OpenAI response to extract individual templates"""
        # Split response into individual templates
        templates = []
        current_template = []
        
        for line in response.split('\n'):
            if line.strip().startswith(('Template 1:', 'Template 2:', 'Template 3:')):
                if current_template:
                    templates.append('\n'.join(current_template))
                current_template = [line]
            else:
                current_template.append(line)
        
        if current_template:
            templates.append('\n'.join(current_template))
            
        return templates
    
    def validate_template(self, template: str, required_variables: List[str]) -> bool:
        """Validate if template contains all required variables"""
        for variable in required_variables:
            if f"{{{{{variable}}}}}" not in template:
                return False
        return True
    
    def process_campaign(self, campaign_name: str, campaign_description: str, 
                        excel_data: pd.DataFrame, custom_template: Optional[str] = None) -> Dict:
        """
        Process a campaign and generate/validate templates
        
        Returns:
            Dict containing:
            - available_variables: List of variables from Excel
            - generated_templates: List of AI-generated templates
            - custom_template_valid: Boolean indicating if custom template is valid
            - validation_message: Message about template validation
        """
        # Get variables from Excel
        available_variables = self.get_excel_columns(excel_data)
        
        # Generate templates using OpenAI
        generated_templates = self.generate_templates(
            campaign_name, 
            campaign_description, 
            available_variables
        )
        
        result = {
            "available_variables": available_variables,
            "generated_templates": generated_templates,
            "custom_template_valid": None,
            "validation_message": None
        }
        
        # Validate custom template if provided
        if custom_template:
            is_valid = self.validate_template(custom_template, available_variables)
            result["custom_template_valid"] = is_valid
            result["validation_message"] = (
                "Custom template is valid and contains all required variables."
                if is_valid else
                "Custom template is missing some required variables."
            )
        
        return result

def example_usage():
    # Example data
    excel_data = pd.DataFrame({
        'name': ['John', 'Sarah'],
        'phone': ['123-456-7890', '987-654-3210'],
        'date': ['2024-03-15', '2024-03-16'],
        'time': ['14:30', '15:30'],
        'amount': ['150.00', '200.00']
    })
    
    campaign_name = "Appointment Reminder"
    campaign_description = "Send appointment reminders to customers with their booking details"
    
    # Initialize generator (replace with actual API key)
    generator = CampaignTemplateGenerator("your-openai-api-key")
    
    # Process campaign
    result = generator.process_campaign(
        campaign_name,
        campaign_description,
        excel_data
    )
    
    # Print results
    print("Available Variables:", result["available_variables"])
    print("\nGenerated Templates:")
    for i, template in enumerate(result["generated_templates"], 1):
        print(f"\nTemplate {i}:")
        print(template)

if __name__ == "__main__":
    example_usage() 