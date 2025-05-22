import pandas as pd
from src.components.model import OpenAIModel
from src.components.template import get_campaign_prompt

class CampaignTemplateGenerator:
    def __init__(self):
        pass
    def generate_templates(self, campaign_columns, camapign_data):
        try:
            campaign_prompt = get_campaign_prompt(campaign_columns,camapign_data)
            campaign_templates = OpenAIModel().run(campaign_prompt)
            return campaign_templates
        except Exception as e:
            print("error in generate_templates", str(e))
            return {}

    def evaluate_fstring_templates(self,campaign_templates,campaign_data):
        try:
            return campaign_templates.format(**campaign_data).replace("f","")
        except Exception as e:
            return []