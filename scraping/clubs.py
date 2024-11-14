import mysql.connector
from mysql.connector import Error
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time

# Set up the Selenium WebDriver
service = Service(executable_path='C:\\Program Files (x86)\\chromedriver.exe')
driver = webdriver.Chrome(service=service)

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

# Create the organizations table in the MySQL database
if connection.is_connected():
    try:
        create_table_query = """
        CREATE TABLE IF NOT EXISTS organizations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            link VARCHAR(255),
            description TEXT,
            contact_info TEXT
        );
        """
        cursor.execute(create_table_query)
        connection.commit()
        print("Table 'organizations' created successfully.")
    except Error as e:
        print("Error while creating table in MySQL", e)

# Open the webpage
driver.get("https://csun.campuslabs.com/engage/organizations")

# Wait for the page to load
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.XPATH, "//button[@tabindex='0'][@type='button']"))
)

# Click the "Load More" button 13 times
for _ in range(27):
    try:
        load_more_button = driver.find_element(By.XPATH, "//button[@tabindex='0'][@type='button']")
        driver.execute_script("arguments[0].scrollIntoView();", load_more_button)
        driver.execute_script("arguments[0].click();", load_more_button)
        time.sleep(2)  # Wait for the content to load
    except (TimeoutException, NoSuchElementException):
        print("No more 'Load More' buttons to click or an error occurred.")
        break

# Extract the links of all organizations
organization_elements = driver.find_elements(By.CSS_SELECTOR, "div[style='font-size: 1.125rem; font-weight: 600; color: rgb(73, 73, 73); padding-left: 0.313rem; text-overflow: initial; margin-top: 0.313rem; overflow: initial; height: initial;']")
organization_links = [org.find_element(By.XPATH, "./ancestor::a").get_attribute("href") for org in organization_elements]

print(f"Found {len(organization_links)} organization links.")

# Visit each link to extract details
for link in organization_links:
    driver.get(link)
    # Extract the organization name from the <h1> tag with the specified padding
    try:
        name_element = driver.find_element(By.XPATH, "//h1[@style='padding: 13px 0px 0px 85px;']")
        name = name_element.text.strip()
    except NoSuchElementException:
        name = "No name available"
    # Extract the description from the first <p> tag
    try:
        description_element = driver.find_element(By.XPATH, "//div[@class='bodyText-large userSupplied']//p")
        description = description_element.text.strip()
    except NoSuchElementException:
        description = "No description available"

    # Extract contact information
    contact_info = {}
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h3")))
        if "Contact Information" in driver.page_source:
            contact_elements = driver.find_elements(By.XPATH, "//div[contains(@style, 'margin-left: 5px; padding: 5px 15px; border-left: 1px solid rgb(210, 210, 210);')]/div")
            for element in contact_elements:
                key = element.find_element(By.XPATH, ".//span[contains(@class, 'sr-only')]").text.strip() if element.find_element(By.XPATH, ".//span[contains(@class, 'sr-only')]") else "Unknown"
                value = element.text.strip()
                contact_info[key] = value
        # Extract social media and website links
        social_links = driver.find_elements(By.XPATH, "//div[a[@aria-label]]/a")
        for social_link in social_links:
            label = social_link.get_attribute("aria-label").split()[-1].capitalize()  # Get the last word of the aria-label and capitalize it
            url = social_link.get_attribute("href")
            contact_info[label] = url
    except TimeoutException:
        print("Contact Information not found within the specified time.")

    print(f"Name: {name}\nLink: {link}\nDescription: {description}\nContact Info: {contact_info}\n")

    # Insert the data into the MySQL database
    if connection.is_connected():
        try:
            query = "INSERT INTO organizations (name, link, description, contact_info) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (name, link, description, str(contact_info)))
            connection.commit()
        except Error as e:
            print("Error while inserting data into MySQL", e)

    # Go back to the main organizations page to ensure all organizations are loaded before moving to the next link
    driver.get("https://csun.campuslabs.com/engage/organizations")
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[style='font-size: 1.125rem; font-weight: 600; color: rgb(73, 73, 73); padding-left: 0.313rem; text-overflow: initial; margin-top: 0.313rem; overflow: initial; height: initial;']"))
    )

# Close the browser
driver.quit()
