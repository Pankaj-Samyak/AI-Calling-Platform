import json

def get_campaign_prompt(campaign_columns, campaign_name, campaign_description):
    response_format={
                        "template_1": "f-string template data",
                        "template_2": "f-string template data",
                        "template_3": "f-string template data"
                    }

    prompt = [
        {
            "role": "system",
            "content": "You are a professional template generator for AI-powered calling campaigns. Your task is to create engaging and effective call script templates."
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"""
                    Generate 3 different call script templates for an AI voice calling campaign with the following details:

                    Campaign Name: {campaign_name}
                    Campaign Description: {campaign_description}
                    Campaign Column Names: {campaign_columns}

                    Instructions:
                    1. Understand the campaign context using the name and description.
                    2. Use the provided column names as placeholders within f-strings to dynamically insert customer-specific data. For example, use {{column_name}} syntax.
                    3. Ensure all f-strings are syntactically correct and can be executed without error andnot use any symbol inside the f-string.
                    4. Create three distinct templates with different tones:
                    - One formal
                    - One casual
                    - One persuasive or enthusiastic
                    5. Each template should:
                    - Be clear, professional, and engaging
                    - Sound natural and suitable for AI voice delivery
                    - Be appropriate for informing or engaging the customer based on campaign data
                    6. Assume the role of an AI calling agent who is contacting a customer using the provided campaign data.
                    7. Ensure that each campaign template follows this structure:
                    - Opening greeting (with client name or greet)
                    - Objective and main information (based on the campaign data)
                    - Polite closing
                    Please provide the output strictly in the following JSON format:
                    {json.dumps(response_format, indent=4)}
                    """
                }
            ]
        }
    ]

    return prompt
