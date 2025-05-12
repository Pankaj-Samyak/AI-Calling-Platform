import re
from typing import Dict, Any, Optional

class TemplateEngine:
    def __init__(self):
        # Pattern to match variables in the format {{variable_name}}
        self.variable_pattern = re.compile(r'\{\{([^}]+)\}\}')
    
    def render(self, template: str, variables: Dict[str, Any]) -> str:
        """
        Render a template string by substituting variables with their values.
        
        Args:
            template (str): The template string containing variables in {{variable_name}} format
            variables (Dict[str, Any]): Dictionary of variable names and their values
            
        Returns:
            str: The rendered template with variables substituted
        """
        def replace_variable(match: re.Match) -> str:
            variable_name = match.group(1).strip()
            if variable_name in variables:
                return str(variables[variable_name])
            return match.group(0)  # Return the original placeholder if variable not found
        
        return self.variable_pattern.sub(replace_variable, template)
    
    def render_file(self, template_path: str, variables: Dict[str, Any], encoding: str = 'utf-8') -> str:
        """
        Render a template file by substituting variables with their values.
        
        Args:
            template_path (str): Path to the template file
            variables (Dict[str, Any]): Dictionary of variable names and their values
            encoding (str): File encoding (default: utf-8)
            
        Returns:
            str: The rendered template with variables substituted
        """
        try:
            with open(template_path, 'r', encoding=encoding) as file:
                template = file.read()
            return self.render(template, variables)
        except FileNotFoundError:
            raise FileNotFoundError(f"Template file not found: {template_path}")
        except Exception as e:
            raise Exception(f"Error reading template file: {str(e)}") 