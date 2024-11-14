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
from selenium.common.exceptions import NoSuchElementException
from mysql.connector import Error

# Set up the Selenium WebDriver
service = Service(executable_path='C:\\Program Files (x86)\\chromedriver.exe')
driver = webdriver.Chrome(service=service)

# Connect to the MySQL database
connection = mysql.connector.connect(
    host="localhost", 
    user="connorjuman",  
    password="connorjuman", 
    database="course_info" 
)
cursor = connection.cursor()

# Open the webpage
driver.get("https://w2.csun.edu/as/departments/sport-clubs/available-sports")

# Find all div elements with class "router-grid__item"
div_elements = driver.find_elements(By.CLASS_NAME, "router-grid__item")

# Collect all links and names
sports_links = []
for div in div_elements:
    p_tags = div.find_elements(By.TAG_NAME, "p")
    if len(p_tags) >= 2:
        a_tag = p_tags[1].find_element(By.TAG_NAME, "a")
        name = a_tag.text.strip()
        link = a_tag.get_attribute("href")
        sports_links.append((name, link))

# Iterate through each link and extract the description and date and time
for name, link in sports_links:
    # Navigate to the link
    driver.get(link)

    # Extract the description from the div with id "main-content"
    try:
        main_content_div = driver.find_element(By.ID, "main-content")
        description = main_content_div.text.strip()
    except NoSuchElementException:
        description = "No description available"

    # Find the Practice Schedule and extract the date and time information
    try:
        practice_schedule_p = driver.find_element(By.XPATH, "//p[strong[contains(text(), 'Practice Schedule')]]")
        date_and_time_ul = practice_schedule_p.find_element(By.XPATH, "./following-sibling::ul")
        date_and_time = ', '.join([li.text.strip() for li in date_and_time_ul.find_elements(By.TAG_NAME, "li")])
    except NoSuchElementException:
        date_and_time = ""

    # Insert the data into the database
    insert_query = """
    INSERT INTO sports (name, link, date_and_time, description)
    VALUES (%s, %s, %s, %s);
    """
    cursor.execute(insert_query, (name, link, date_and_time, description))
    connection.commit()

    print(f"Data inserted successfully for {name}.")

# Close the browser
driver.quit()

# Close the database connection
cursor.close()
connection.close()

