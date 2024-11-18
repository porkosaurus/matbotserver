from anthropic import Anthropic
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import requests
from datetime import datetime
import os
from dotenv import load_dotenv

# Initialize the Anthropic client
anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Constants
DINING_API_URL = "https://api.dineoncampus.com/v1/locations/status?site_id=5efb645cbf31720ae5755e2d&timestamp={}"
TIMESTAMP_FORMAT = '%Y-%m-%d'

def get_dining_information():
    # Get the current date
    current_date = datetime.now().strftime(TIMESTAMP_FORMAT)

    # Construct the API URL with the current timestamp
    url = DINING_API_URL.format(current_date)

    # Add a user-agent header to make the request look like it's coming from a browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    # Fetch the data from the API
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Process the data
        dining_info = ""
        for location in data['locations']:
            dining_info += f"Name: {location['name']}\n"
            dining_info += f"Status: {location['status']['label']} - {location['status']['message']}\n\n"

        return dining_info
    except requests.exceptions.RequestException as e:
        print(f"Error fetching dining information: {str(e)}")
        return "Sorry, there was an error fetching the dining information."

def answer_dining_question(question, context):
    # First LLM request
    response = anthropic.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=100,
        messages=[
            {"role": "user", "content": f"""You are an assistant. Your task is to determine if the user's query is related to dining information. Respond with either "Dining" or "Not Dining" based on your assessment.

            Question: {question}

            Provide your response:"""}
        ]
    )

    category = response.content[0].text.strip()

    if category == "Dining":
        dining_info = get_dining_information()

        response = anthropic.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": f"""You are a helpful university dining advisor providing information about the dining options on campus. Be conversational and provide specific details about the dining facilities and menu options.

                Question: {question}

                Dining Information:
                {dining_info}

                Provide your response:"""}
            ]
        )

        return response.content[0].text
    else:
        return "I'm sorry, I don't have any information about that. My expertise is limited to campus dining options."

# Example usage
if __name__ == "__main__":
    answer = answer_dining_question("What's for lunch today?", "")
    print(answer)