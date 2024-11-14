from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time
import mysql.connector
from mysql.connector import Error

# Set up the Selenium WebDriver
service = Service(executable_path='C:\\Program Files (x86)\\chromedriver.exe')
driver = webdriver.Chrome(service=service)

# Open the webpage
driver.get("https://www.csun.edu/usu/services")

# Wait for the page to load
# WebDriverWait(driver, 10).until(
#     EC.presence_of_element_located((By.CLASS_NAME, "field-name-field-title-text"))
# )

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

# Create the amenities table
try:
    create_table_query = """
    CREATE TABLE IF NOT EXISTS amenities (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255),
        link VARCHAR(255),
        date_and_time TEXT,
        description TEXT,
        contact TEXT,
        location TEXT
    );
    """
    cursor.execute(create_table_query)
    connection.commit()
    print("Table 'amenities' created successfully.")
except Error as e:
    print("Error while creating table in MySQL", e)

def scrape_initial_amenities():
    # Find all h2 elements with class "field-title-text"
    h2_elements = driver.find_elements(By.CLASS_NAME, "field-name-field-title-text")

    # Dictionary to map names to specific URLs
    name_to_url = {
        "A.S. Ticket Office": "https://w2.csun.edu/as/departments/ticket-office",
        "Computer Lab": "https://www.csun.edu/usu/computer-lab",
        "Dream Center": "https://www.csun.edu/dreamcenter",
        "Pride Center": "https://www.csun.edu/pride",
        "Oasis Wellness Center": "https://www.csun.edu/oasis",
        "Reservations and Event Services": "https://www.csun.edu/usu/reservations",
        "Veterans Resource Center": "https://www.csun.edu/vrc",
    }

    for h2 in h2_elements:
        # Scroll the h2 element into view
        driver.execute_script("arguments[0].scrollIntoView();", h2)
        
        # Click the h2 element to expand the section
        h2.click()
        time.sleep(1)  # Wait for the section to expand
        
        # Extract the name from the h2 element
        name = h2.text.split("\n")[0].strip()
        
        # Find the corresponding div with class "field-name-field-body" and extract the description
        try:
            description_div = h2.find_element(By.XPATH, "./following-sibling::div[contains(@class, 'field-name-field-body')]")
            description = description_div.text.strip()
        except NoSuchElementException:
            description = "No description available"
        
        # Get the specific URL if available
        url = name_to_url.get(name, "No specific URL available")

        # Insert or update the data in the database
        try:
            update_query = """
            INSERT INTO amenities (name, link, description)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                link = VALUES(link),
                description = VALUES(description);
            """
            cursor.execute(update_query, (name, url, description))
            connection.commit()
            print(f"Data updated successfully for {name}.")
        except Error as e:
            print(f"Error while updating the database for {name}:", e)

    # Close the browser
    driver.quit()

    # Close the database connection
    cursor.close()
    connection.close()




as_ticket_full_description = """
Ticket Office:
The AS Ticket Office offers ticketing services for campus events including athletic games, theater performances, music ensembles, and more. Discounted tickets for movie theaters and theme parks are available, along with transit passes for Metro and AVTA for commuter students and the local community.

AS Ticket Office Box Office:
Visit the AS Ticket Office or call (818) 677-2488 for more information. Located across Subway in the University Student Union (USU).

Campus Events:
The CSUN community and talented students come together to create various campus events. The A.S. Ticket Office provides ticketing services for these events, including athletic games, theater performances, and more.

Theme Park Prices:
The AS Ticket Office offers discounted tickets for thrill-seekers, animal lovers, and movie enthusiasts. Most tickets must be purchased in person at the AS Ticket Office, located across Subway in the USU. For certain discounts from Universal Studios Hollywood and LEGOLAND California Resort, tickets must be purchased online with a CSUN email address.

Online Tickets:
- Universal Studios Theme Parks: General Admission up to $149, Discount as low as $99
- Legoland California: General Admission up to $119, Discount as low as $75.20
- Knott's Berry Farm: Gate Admission up to $99, Discount as low as $58
- Whale Watching: General Admission up to $28, Discount as low as $20
- Aquarium of the Pacific: General Admission up to $44.95, Discount as low as $39
- Medieval Times: General Admission up to $67.95, Discount as low as $52.95

In-Person Tickets:
- AMC Theatres: Standard Movie Ticket up to $16.99, Discount as low as $11.50
- Catalina Express: General Admission up to $89, Discount as low as $72
- San Diego Zoo: General Admission up to $74, Discount as low as $62.50
- San Diego Zoo Safari Park: General Admission up to $74, Discount as low as $62.50

Note: Prices and offers are subject to change without notice. Call the AS Ticket Office at (818) 677-2488 for the latest prices.

Prices updated: August 2023
"""
as_location_info = """
Location:
Ticket Office
18111 Nordhoff St.
Northridge, CA 91330
(located in the University Student Union)
"""
as_contact_info = """
Contact:
Phone: (818) 677-2488
Email: [Send email link]  
"""
as_hours_info = """
Office Hours:
Monday: 10am - 6pm
Tuesday: 10am - 6pm
Wednesday: 10am - 6pm
Thursday: 10am - 6pm
Friday: 9am - 5pm
"""
# Define the data for AS Ticket Office
as_ticket_data = {
    'name': 'A.S. Ticket Office',
    'link': 'https://w2.csun.edu/as/departments/ticket-office',
    'date_and_time': as_hours_info,
    'description': as_ticket_full_description,
    'contact': as_contact_info,
    'location': as_location_info
}

try:
    update_query = """
    UPDATE amenities
    SET link = %s, date_and_time = %s, description = %s, contact = %s, location = %s
    WHERE name = %s;
    """
    # The order of values in the tuple must match the order of placeholders in the SQL query
    cursor.execute(update_query, (as_ticket_data['link'], as_ticket_data['date_and_time'], as_ticket_data['description'], as_ticket_data['contact'], as_ticket_data['location'], as_ticket_data['name']))
    connection.commit()
    print(f"Data updated successfully for {as_ticket_data['name']}.")
except Error as e:
    print(f"Error while updating the database for {as_ticket_data['name']}:", e)


computer_lab_full_description = """
The USU Computer Lab is a professional workspace that offers CSUN students 130 computer workstations, 20 print stations, 10 scanners and a private Training Lab as well as a wide range of cutting-edge software programs. All students are welcome to use any available workstation to study, print 140 free pages per week or just surf the web between classes.

We’re here so you can print, study and browse or become more tech savvy by signing up for our USU Tech Tips workshops, held right here, at the Computer Lab.

Need Assistance? Our Computer Lab Technicians are ready to help you and answer any of your computer and software related questions in a productive and supportive environment.
"""
computer_lab_location_info = """
University Student Union
18111 Nordhoff Street, Northridge, CA 91330
"""
computer_lab_contact_info = """
Phone: (818) 677-1200
"""
computer_lab_hours_info = """
Spring/Fall Hours:
Monday – Thursday: 8 a.m. – 9 p.m.
Friday: 8 a.m. – 5 p.m.
Saturday – Sunday: 10 a.m. – 4 p.m.

Winter/Summer Hours:
Monday – Friday: 8 a.m. – 5 p.m.
Saturday – Sunday: 10 a.m. – 4 p.m.
"""

dream_center_full_description = """
The DREAM Center of the University Student Union at CSUN is a welcoming resource center that provides resources and services to undocumented students, mixed status families, staff, faculty, allies, and future undocumented students while fostering a more inclusive campus community. DREAM stands for Dreamers, Resources, Empowerment, Advocacy, and Mentorship. You can meet with us by appointment or just walk into our space at the USU.

We provide resources and services to help empower students so that they can become advocates during their educational trajectory.
We increase knowledge of the ever-changing political climate which affects students in their personal and professional lives.
We believe students thrive and undergo a transformation when they feel supported and empowered in their autonomies to confidently pursue their aspirations and goals.

The University Student Union at CSUN includes the DREAM Center, Pride Center, Computer Lab, East Conference Center, Games Room, Northridge Center, Oasis Wellness Center, Reservations & Event Services, Student Recreation Center, USU Programs, Veterans Resource Center...and you!
"""
dream_center_location_info = """
DREAM Center
(Located in the University Student Union Building C)
18111 Nordhoff Street
Northridge, CA 91330-8453
"""
dream_center_contact_info = """
Phone: (818) 677-7069
Email: dreamcenter@csun.edu
"""
dream_center_hours_info = """
Fall/Spring Hours:
Monday – Thursday: 9 a.m. – 6 p.m.
Friday: 9 a.m. – 2 p.m.

Summer Hours:
Monday – Friday: 10 a.m. – 2 p.m.
"""

pride_center_full_description = """
Be You.
The Pride Center supports lesbian, gay, bisexual, transgender, queer, questioning, intersex, and asexual (LGBTQIA+) students, faculty, and staff through programming and educational outreach to improve the campus climate for LGBTQIA+ individuals as well as advocate for the respect and safety of all members of the campus community.

Pride Center Values: Advocacy, Communication, Empowerment, Fun, Inclusivity, Intersectionality, Learning, Social Justice

The University Student Union at CSUN includes the DREAM Center, Pride Center, Computer Lab, East Conference Center, Games Room, Northridge Center, Oasis Wellness Center, Reservations & Event Services, Student Recreation Center, USU Programs, Veterans Resource Center...and you!
"""
pride_center_location_info = """
Pride Center
(Located in the University Student Union Sol Center, second floor)
18111 Nordhoff Street
Northridge, CA 91330-8272
"""
pride_center_contact_info = """
Phone: (818) 677-4355
Email: pride@csun.edu
"""
pride_center_hours_info = """
Fall/Spring Hours:
Monday – Thursday: 9 a.m. – 6 p.m.
Friday: 10 a.m. – 2 p.m.
Saturday – Sunday: Closed
"""

oasis_wellness_center_full_description = """
Your Place to Relax, Revive and Succeed.
The Oasis is a welcoming destination where CSUN students can find serenity and relaxation amid the rush and activity of campus life. The Oasis features a wide range of health and wellness programs intended to promote student academic success.

The Oasis Wellness Center at the University Student Union. Come experience it for yourself.

The University Student Union at CSUN includes the DREAM Center, Pride Center, Computer Lab, East Conference Center, Games Room, Northridge Center, Oasis Wellness Center, Reservations & Event Services, Student Recreation Center, USU Programs, Veterans Resource Center...and you!
"""
oasis_wellness_center_location_info = """
Oasis Wellness Center
(Located in the University Student Union)
18111 Nordhoff Street
Northridge, CA 91330-8272
"""
oasis_wellness_center_contact_info = """
Phone: (818) 677-7373
Email: oasis@csun.edu
"""
oasis_wellness_center_hours_info = """
Fall/Spring Hours:
Monday – Thursday: 8 a.m. – 8 p.m.
Friday: 9 a.m. – 4 p.m.
Saturday and Sunday: Closed

Summer Hours:
Monday – Friday: 10 a.m. – 2 p.m.
Saturday and Sunday: Closed
"""

reservations_and_event_services_full_description = """
Reservations and Event Services at the University Student Union at CSUN provides an ideal location for meeting and event planners in Southern California's San Fernando Valley. Our facilities can accommodate a wide range of events from intimate receptions to trade shows and conferences. The Reservations & Event Services office is a student training facility where staff receive hands-on training while providing professional meeting planning assistance.

Vision Statement: Reservations & Event Services will be recognized as a premier university-based meeting and event facility in the San Fernando Valley by consistently providing cost-conscious, reliable, and genuine service to our customers.

Mission Statement: To serve the CSUN community by providing high-quality event planning and support services in an attractive environment that emanates exceptional positive experiences.

Requesting a Space: All reservation requests are processed in order of receipt and are subject to room availability. Please allow up to three (3) business days to process the request. Reservation paperwork will be sent through email within that timeframe. Our reservation calendar opens in August for the next fiscal year (July through June of the next year).

Virtual Event Consultations and Tips: Our dedicated team is happy to help with all of your event planning needs, whether it's transitioning an event into a virtual experience or introducing a new event.

Who Can Make Reservations? We offer reservation services to recognized student clubs and organizations, CSUN departments, and private/off-campus individuals and companies.
"""
reservations_and_event_services_location_info = """
No location information available.
"""
reservations_and_event_services_contact_info = """
Phone: (818) 677-3644
Fax: (818) 677-4172
Building Manager: (818) 859-8255
Email: usuresrv@csun.edu
"""
reservations_and_event_services_hours_info = """
Office Hours: Monday – Friday, 10 a.m. – 4 p.m.
"""

veterans_resource_center_full_description = """
Welcome to the Veterans Resource Center!
Our mission is to assist CSUN students as they transition from military service to academic success. The VRC promotes the academic, personal, and professional development of student veterans, reservists, members of the National Guard, and their dependents through supportive services, resources, and community-building events.
"""
veterans_resource_center_location_info = """
Veterans Resource Center
(Located in the University Student Union between the Student Recreation Center and the USU Computer Lab)
18111 Nordhoff Street
Northridge, CA 91330-8272
"""
veterans_resource_center_contact_info = """
Phone: (818) 677-4672
Email: vrc@csun.edu
"""
veterans_resource_center_hours_info = """
Fall/Spring Hours:
Monday and Thursday: 9 a.m. – 6 p.m.
Tuesday and Wednesday: 9 a.m. – 7 p.m.
Friday: 10 a.m. – 2 p.m.

Summer Hours:
Monday – Friday: 10 a.m. – 2 p.m.
"""


# Define the data for other amenities
amenities_data = [
    {
        'name': 'Computer Lab',
        'link': 'https://www.csun.edu/usu/computer-lab',
        'date_and_time': computer_lab_hours_info,
        'description': computer_lab_full_description,
        'contact': computer_lab_contact_info,
        'location': computer_lab_location_info
    },
    {
        'name': 'Dream Center',
        'link': 'https://www.csun.edu/dreamcenter',
        'date_and_time': dream_center_hours_info,
        'description': dream_center_full_description,
        'contact': dream_center_contact_info,
        'location': dream_center_location_info
    },
    {
        'name': 'Pride Center',
        'link': 'https://www.csun.edu/pride',
        'date_and_time': pride_center_hours_info,
        'description': pride_center_full_description,
        'contact': pride_center_contact_info,
        'location': pride_center_location_info
    },
    {
        'name': 'Oasis Wellness Center',
        'link': 'https://www.csun.edu/oasis',
        'date_and_time': oasis_wellness_center_hours_info,
        'description': oasis_wellness_center_full_description,
        'contact': oasis_wellness_center_contact_info,
        'location': oasis_wellness_center_location_info
    },
    {
        'name': 'Reservations and Event Services',
        'link': 'https://www.csun.edu/usu/reservations',
        'date_and_time': reservations_and_event_services_hours_info,
        'description': reservations_and_event_services_full_description,
        'contact': reservations_and_event_services_contact_info,
        'location': reservations_and_event_services_location_info
    },
    {
        'name': 'Veterans Resource Center',
        'link': 'https://www.csun.edu/vrc',
        'date_and_time': veterans_resource_center_hours_info,
        'description': veterans_resource_center_full_description,
        'contact': veterans_resource_center_contact_info,
        'location': veterans_resource_center_location_info
    }
]

# Insert or update the data in the database
for amenity in amenities_data:
    try:
        update_query = """
        UPDATE amenities
        SET link = %s, date_and_time = %s, description = %s, contact = %s, location = %s
        WHERE name = %s;
        """
        # The order of values in the tuple must match the order of placeholders in the SQL query
        cursor.execute(update_query, (amenity['link'], amenity['date_and_time'], amenity['description'], amenity['contact'], amenity['location'], amenity['name']))
        connection.commit()
        print(f"Data updated successfully for {amenity['name']}.")
    except Error as e:
        print(f"Error while updating the database for {amenity['name']}:", e)
