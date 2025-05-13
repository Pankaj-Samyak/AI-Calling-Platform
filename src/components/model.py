import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from src.logger.log import Log_class

load_dotenv()
logg_obj = Log_class("logs", "Model.txt")

class OpenAIModel:
    def __init__(self):
        logg_obj.Info_Log("Loading OpenAI API key from environment variables.")
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        if not OPENAI_API_KEY:
            logg_obj.Error_Log("OpenAI API key is missing. Please set it as an environment variable.")
            raise ValueError("OpenAI API key is missing. Set it as an environment variable.")

        # Load the OpenAI client
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        logg_obj.Info_Log("OpenAI API client successfully loaded.")

    def run(self,prompt):
        logg_obj.Info_Log("Initiating call to OpenAI API")

        # Call OpenAI API
        try:
            response = self.client.chat.completions.create(
                model= "gpt-4o-mini",
                messages = prompt,
                max_tokens=800,
                response_format={"type": "json_object"},
            )
            logg_obj.Info_Log("OpenAI API response received successfully.")

            # FIX: Ensure API response is valid and clean up any unwanted markdown characters
            if not response.choices or not response.choices[0].message or not response.choices[0].message.content:
                logg_obj.Error_Log("Received empty or invalid response from OpenAI.")
                print("Empty or invalid response from OpenAI")

            # Clean up response content to remove unwanted markdown characters (e.g., code blocks)
            response_content = response.choices[0].message.content.strip()

            # Remove any markdown formatting (if present), e.g., code block formatting
            if response_content.startswith("```json"):
                response_content = response_content[7:].strip()
            if response_content.endswith("```"):
                response_content = response_content[:-3].strip()

            # FIX: Try parsing JSON, handle errors
            try:
                json_response = json.loads(response_content)
                logg_obj.Info_Log("Successfully parsed JSON response from OpenAI.")
            except json.JSONDecodeError:
                logg_obj.Error_Log(f"Invalid JSON response from OpenAI: {response_content}")

            # Log the final response
            logg_obj.Info_Log("Returning the parsed JSON response.")

            # 👉 Track token usage
            usage = response.usage
            logg_obj.Info_Log(f"input_tokens:{usage.prompt_tokens}")
            logg_obj.Info_Log(f"output_tokens:{usage.completion_tokens}")
            logg_obj.Info_Log(f"total_tokens:{usage.total_tokens}")
            return json_response

        except Exception as e:
            logg_obj.Error_Log(f"Error during OpenAI API call: {str(e)}")
            return {"error": str(e)}