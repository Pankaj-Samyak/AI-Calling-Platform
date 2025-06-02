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
    totalCallTime: int = 0
    totalNumCall: int = 0
    totalSpent: int = 0
    maxCallTimeout: int = 3
    inactiveCallTimeout: int = 15
    averageCallCost: float = 0.0
    timezone: str = "UTC"
    silenceTimer: int = 150
    wordsToInterrupt: int = 2
    detectInactivity: bool = True
    isFreeflow: bool = True
    forge_flow_script: str = ""
    sampleSid: str = ""
    description: str = ""


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

#--------------------------------#
class LaunchCall(BaseModel):
    batch_name : str
    user_id : str
    campaign_id : str
