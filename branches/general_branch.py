


import mysql.connector
from mysql.connector import Error
from anthropic import Anthropic
import os
# Load environment variables
from dotenv import load_dotenv
load_dotenv()
# Initialize the Anthropic client
anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

def answer_general_question(question, context):
    # Use Claude to generate a general response
    print("General Question:", question)

    # Use Claude to generate a response
    response = anthropic.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": f"""You are an assistant at the university, CSUN. Your task is to provide a response to the user's question. Be conversational and provide a helpful answer.

            Question: {question}

            Previous conversation context:
            {context}

            Provide your response:"""}
        ]
    )

    print(response.content[0].text)
    return response.content[0].text