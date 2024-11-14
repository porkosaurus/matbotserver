from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time
import mysql.connector
from mysql.connector import Error

connection = mysql.connector.connect(
    host="localhost", 
    user="connorjuman",  
    password="connorjuman", 
    database="course_info" 
)
cursor = connection.cursor()

insert_query = """
INSERT INTO amenities (name, location, contact, date_and_time, description, link) 
VALUES (%s, %s, %s, %s, %s, %s)
"""

amenity_data = (
    "Children's Center",
    "Children's Center, 18343 Plummer St., Northridge, CA 91330",
    "(818) 677-2012",
    "Monday - Friday: 7:30am - 5:30pm",
    "The AS Children’s Center is a high-quality early childhood education program that provides a safe and nurturing environment while promoting the physical, social, emotional and intellectual development of young children.",
    "https://w2.csun.edu/as/departments/childrens-center"
)

cursor.execute(insert_query, amenity_data)
connection.commit()
