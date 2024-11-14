from bs4 import BeautifulSoup
import requests
import mysql.connector
from mysql.connector import Error

# Connect to the MySQL database
try:
    connection = mysql.connector.connect(
        host="localhost", 
        user="connorjuman",  
        password="connorjuman", 
        database="course_info" 
    )
    cursor = connection.cursor()
except Error as e:
    print("Error while connecting to MySQL", e)

# URL to scrape
base_url = 'https://catalog.csun.edu'

# Set headers to simulate a request from a browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

# Function to extract courses and units from a URL and store them in the database
def extract_courses_and_units(url, department, concentration):
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Accumulate all courses and units for this concentration
    all_requirements_info = []

    # Find all tables and their corresponding h3 tags
    tables = soup.find_all('table')
    for table in tables:
        # Find the h3 tag that precedes the table
        h3_tag = table.find_previous('h3')
        requirement_h3 = h3_tag.text.strip() if h3_tag else None
        print(f"H3: {requirement_h3}")

        # Accumulate courses and units for this requirement
        requirement_info = [f"{requirement_h3}:"]

        # Extract courses and units from the table
        tbody = table.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')[1:]  # Skip the first row with th tags
            for row in rows:
                tds = row.find_all('td')
                if len(tds) >= 2:
                    # Check if the course is in a link, strong tag, or directly in the td
                    course_tag = tds[0].find('a') or tds[0].find('strong') or tds[0]
                    course = course_tag.text.strip()
                    units = tds[1].text.strip()
                    print(f"Course: {course}, Units: {units}")

                    # Add the course and units to the requirement info
                    requirement_info.append(f"{course} ({units} units)")

        # Convert the requirement info list to a single string and add it to all requirements
        requirement_info_str = ' | '.join(requirement_info)
        all_requirements_info.append(requirement_info_str)

        print("--------")

    # Convert all requirements info to a single string
    all_requirements_info_str = ' || '.join(all_requirements_info)

    # Insert the department, concentration, and all requirements info into the database
    cursor.execute(
        "INSERT INTO degree_requirements (department, concentration, requirements) VALUES (%s, %s, %s)",
        (department, concentration, all_requirements_info_str)
    )
    connection.commit()



# Parse the HTML content of the page
response = requests.get(f"{base_url}/resource/road-map/2023/", headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

# Find all the spans with class 'section-title'
section_titles = soup.find_all('span', class_='section-title')

# Iterate over each section title
for title in section_titles:
    # Print the department name
    department = title.text.strip()
    print(f"Department: {department}")

    # Find all the sibling elements after the title until the next span with class 'section-title'
    sibling = title.find_next_sibling()
    while sibling and sibling.name != 'span':
        if sibling.name == 'p':
            a_tag = sibling.find('a')
            if a_tag:
                # Clean up the text
                text = a_tag.text.strip()
                text = text.split('(')[0].strip()  # Remove the year information
                if '/' in text:
                    # Remove the redundant department name in the concentration
                    parts = text.split('/')
                    if parts[0].strip() == department:
                        text = parts[1].strip()
                    else:
                        text = '/'.join(parts).strip()
                # Print the cleaned text
                print(f"Title: {text}")
                # Visit the link and extract courses and units
                link = a_tag['href']
                if not link.startswith('http'):
                    link = base_url + link
                print(f"Visiting link: {link}")
                extract_courses_and_units(link, department, text)  # Pass the department and concentration
        sibling = sibling.find_next_sibling()
    print("--------")


# Close the database connection
cursor.close()
connection.close()