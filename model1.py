import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time as time_module
import spacy
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import re
# Initialize the Flask application
app = Flask(__name__)
CORS(app)

# Initialize the OpenAI client
api_key = ''
client = OpenAI(api_key=api_key)

def answer_query_with_assistant(query, assistant_id):
    # Create a new Thread with the query
    thread_response = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": query
            }
        ]
    )
    thread_id = thread_response.id  # Access the id directly
    print(thread_id)
    
    # Run the Assistant on the Thread
    run_response = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    # Wait for the Run to complete
    while run_response.status in ['queued', 'in_progress', 'cancelling']:
        time_module.sleep(1)  # Wait for 1 second
        run_response = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_response.id
        )

    # Once the Run completes, list the Messages added to the Thread by the Assistant
    if run_response.status == 'completed':
        messages = client.beta.threads.messages.list(
            thread_id=thread_id
        )
        assistant_responses = []
        for message in messages:
            if message.role == "assistant":
                for text_object in message.content:
                    print(text_object.text.value)
                    if text_object.type == 'text':
                        assistant_responses.append(text_object.text.value)
        return "\n\n".join(assistant_responses)
    else:
        return "The Assistant could not complete the request."


def answer_general_question(question):
    # Use OpenAI's API to generate a general response
    print("General Question:", question)
    messages = [
        {"role": "system", "content": "You are an assistant at the university, CSUN. Your task is to provide a response to the user's question. Be conversational and provide a helpful answer."},
        {"role": "user", "content": f"Question: {question}"},
        {"role": "assistant", "content": "Answer:"},
    ]
    response = client.chat.completions.create(
        messages=messages,
        model="gpt-3.5-turbo",
    )
    return response.choices[0].message.content

def answer_map_question():
    csun_map = """<img src='https://public.boxcloud.com/api/2.0/internal_files/1288243218059/versions/1408427156599/representations/png_paged_2048x2048/content/1.png?access_token=1!fraJxkLtTotoRkgJhgN4cOyBzRsfrXx1cCb7wamy9dMcdnB-T-HkRKkX1bPjm2QQA8I1ym-_bumA7b2XCn6nN_2gLlnidUQZCQCo9ZFLaGEWiqwg5fOHZj3tORDCZxhLprbYCMj7PZkjmRlqVZdy_zxvlfitcuYnL5nO45yx5dwmfCsejDpvrB_p9eK-WTwnmwVV3alIDb0kjV8FQnOzTQyDhYcF_57dIq6DFWA3NLeGIQKaH17Wf7VTq4d3VfjFie53G0H03s8C_nT4JMNxZNPIHsXe77plC_Sc4ZWjQhhL_CxnCGUhGTJ6bPAx8IzCpM8Mh_oILD9VH1hCqFHRoiHE0Qtpmd6wUadB1Fhqxk1xJukkK461Xi3cKYrFVt4SL5rx6bJq0j9oHXuljFhjOU35dPmUt5TvIpZQzYr9s2pZbbnsn9VV4vljGrpajvWR0vk8cApr3pprDdyzYaoL-QhRm_apKoaf_H3ylXUAl4nyW3UUFk5OpBeMPakLFT47iRVtjzEZDN5fVFSXafCSdP9HCsxkNf6mnPKg5-GfeuoLgCanrWSiBmSCQ-GTZNTXaQ..&shared_link=https%3A%2F%2Fmycsun.app.box.com%2Fs%2Fm0sor244817nimv8g0phamx1iltqb3f5&box_client_name=box-content-preview&box_client_version=2.102.0'/>
    <h4>Here is a map of the CSUN Campus</h4>"""
    return csun_map

def answer_query_model1(query):
    # Use ChatGPT to determine the context of the query
    messages = [
        {"role": "system", "content": "You are an assistant. Your task is to identify whether the user's query is related to courses, sports, clubs, events, amenities, map or general. These responses are the only responses you are allowed. Your response must be one word long and it must be one of these eight. Amenities include nap pods, massage chairs, meditation room, gym. If the input is related to tutoring, such as seeking explanations or help with understanding concepts, output 'tutoring'. If it's about courses, such as asking for course details, schedules, or recommendations, output 'courses'."},
        {"role": "user", "content": query},
        {"role": "assistant", "content": "Is this query about courses, sports, clubs, events, amenities, map or tutoring?"},
    ]
    response = client.chat.completions.create(
        messages=messages,
        model="gpt-3.5-turbo",
        max_tokens=10  # Limit the response length
    )
    response = response.choices[0].message.content.strip().lower()

    # Define a mapping of contexts to assistant IDs
    assistant_ids = {
        "courses": "asst_5qWeT8FArsy1EjNQj0eCT980",
        "sports": "asst_EhtY3RdfayMhenigvyAoAWWh",
        "clubs": "asst_mQN7amGF9APm9ookWQY6Etx0",
        "events": "asst_MWryQa1AA4cUAhIyX8tD1j4G",
        "amenities": "asst_EutN36vqdYvPr6Uf03oRL4wM"
    }

    # Call the appropriate function based on the context
    if response in assistant_ids:
        return answer_query_with_assistant(query, assistant_ids[response])
    elif response == "map":
        return answer_map_question()
    elif response == "general" or response == "tutoring":
        return answer_general_question(query)
    else:
        return "I'm sorry, I couldn't determine the context of your query. Please try again with more specific information."

