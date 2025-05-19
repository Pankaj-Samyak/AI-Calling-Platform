from pydantic import BaseModel
from typing import Any, Dict, List

#------------CreateCampaign------------#
class CreateCampaign(BaseModel):
    campaign_name: str
    campaign_description: str
    voice: str
    language: str
    knowledge_base: str
    tone: str
    first_line: str
    system_prompt: str
    post_call_analysis: bool
    post_call_analysis_schema: Dict[str, Any]

#------------CallBatch------------#
class CallBatch(BaseModel):
    campaign_id: str
    batch_name: str
    campaign_template: str
    scheduledTime: str
    callDetails: List[Any]

#---------------------------------#
class CampaignTemplates(BaseModel):
    campaign_id: str
    callDetails: List[Any]

#--------------------------------#
class AddTelephony(BaseModel):
   twilioAccountSid : str
   twilioAuthToken : str
   twilioPhoneNumber : str
   voiceProvider : str
