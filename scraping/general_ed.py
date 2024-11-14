from selenium import webdriver
from selenium.webdriver.common.by import By
import time

# Set up the Selenium WebDriver
driver = webdriver.Chrome()  # You might need to specify the path to your chromedriver executable
driver.get("https://catalog.csun.edu/general-education/courses/")

# Click on all divs with class "panel-default"
panels = driver.find_elements(By.CLASS_NAME, "panel-default")
for panel in panels:
    panel.click()
    time.sleep(1)  # Wait for the panel to expand

# Create a dictionary to store the association between h2 texts and course names
course_dict = {}

# Find all h2 elements with class "pseudo-h4"
h2_elements = driver.find_elements(By.CLASS_NAME, "pseudo-h4")
for h2 in h2_elements:
    # Get the text of the h2 element
    h2_text = "GE " + h2.text.split('(')[0].strip()  # Add "GE" and remove the number in parentheses

    # Find all the course names within the same panel as the h2 element
    panel_body = h2.find_element(By.XPATH, "./ancestor::div[contains(@class, 'panel-default')]").find_element(By.CLASS_NAME, "panel-body")
    course_elements = panel_body.find_elements(By.TAG_NAME, "a")
    course_names = [course.text.split('.')[0].strip() for course in course_elements]  # Extract the course code

    # Associate the h2 text with the course names
    course_dict[h2_text] = course_names

# Print the association between h2 texts and course names
for h2_text, course_names in course_dict.items():
    print(f"{h2_text}: {', '.join(course_names)}")

# Close the WebDriver
driver.quit()
