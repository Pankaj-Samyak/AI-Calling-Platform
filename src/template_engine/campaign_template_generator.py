import pandas as pd
from src.components.model import OpenAIModel
from src.components.template import get_campaign_prompt

class CampaignTemplateGenerator:
    def __init__(self):
        pass

    def generate_templates(self, campaign_columns, campaign_name, campaign_description):
        try:
            campaign_prompt = get_campaign_prompt(campaign_columns, campaign_name, campaign_description)
            campaign_templates = OpenAIModel().run(campaign_prompt)
            return campaign_templates
        except Exception as e:
            print("error in generate_templates", str(e))
            return {}

    def evaluate_fstring_templates(self,campaign_templates,campaign_data):
        try:
            return [{temp_key:temp_val.format(**campaign_data).replace("f","")} for temp_key, temp_val in campaign_templates.items()]
        except Exception as e:
            print(str(e))
            return []