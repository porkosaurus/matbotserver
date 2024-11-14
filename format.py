from openai import OpenAI
from google.cloud import translate_v2 as translate
import os

# Initialize the OpenAI client
api_key = ''
client = OpenAI(api_key=api_key)

# Initialize the Google Cloud Translate client without explicitly providing credentials
translate_client = translate.Client()

def format_answer_with_openai(answer):
    # Set up the OpenAI API request
    messages = [
        {"role": "system", "content": "You are a chat assistant."},
        {"role": "user", "content": f"Convert this answer to HTML format using popular tags like strong, em, p, ul, ol, li, h1, h2, h3, h4, h5, h6, a, div. The outermost div should have the class 'response'. Use strong tags for headers and important info. Course names and course codes shoud be wrapped in strong tags. Do not include any code block markers like triple backticks. For a simple rule of thumb, never use triple backticks nor the word html followed by triple backticks. Do your response in text and not a code block. DO NOT USE A CODE BLOCK. DO NOT USE A CODE BLOCK IN YOUR RESPONSE. DO NOT USE TRIPLE BACKTICKS. DO NOT USE TRIPLE BACKTICK IN YOUR RESPONSE.  Here is the answer: {answer}"},
        {"role": "assistant", "content": "Here is the formatted answer in HTML:"}
    ]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )

    # Extract the formatted answer from the response
    formatted_answer = response.choices[0].message.content.strip()
    print(formatted_answer)
    return formatted_answer
