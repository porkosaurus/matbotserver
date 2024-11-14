import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
import os
from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time as time_module
import spacy
import mysql.connector

def get_event_info():
    # Base URL for the events page
    base_url = "https://www.csun.edu/usu/events"

    # Connect to the MySQL database
    connection = mysql.connector.connect(
        host="localhost", 
        user="connorjuman",  
        password="connorjuman", 
        database="course_info" 
    )
    cursor = connection.cursor()

    # Iterate through the pages
    for page in range(12):  # Change to 12 to include pages 0 to 11
        # Construct the URL for the current page
        page_url = f"{base_url}?sort_by=field_event_date_value&sort_order=ASC&page={page}"
        
        # Send a request to the page
        response = requests.get(page_url)
        
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Find all h2 tags with class 'node--title'
        event_titles = soup.find_all("h2", class_="node--title")
        
        # Extract event titles and links
        for event_title in event_titles:
            name = event_title.find("a").text.strip()
            link = event_title.find("a")["href"]

            # Find the parent article of the event title
            parent_article = event_title.find_parent("article")
            
            # Find the date and time
            date_time_span = parent_article.find("span", class_="date-display-single")
            date_and_time = date_time_span.text.strip() if date_time_span else "Not available"

            # Find the description
            description_div = parent_article.find("div", class_="field-label-hidden")
            description = description_div.find("p").text.strip() if description_div and description_div.find("p") else "Not available"

            # Insert the data into the database
            insert_query = """
            INSERT INTO events (name, link, date_and_time, description, contact, location)
            VALUES (%s, %s, %s, %s, %s, %s);
            """
            cursor.execute(insert_query, (name, link, date_and_time, description, '', ''))
            connection.commit()

    # Close the database connection
    cursor.close()
    connection.close()

get_event_info()