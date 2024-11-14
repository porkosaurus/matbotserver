from bs4 import BeautifulSoup
import requests
import mysql.connector
# Base URL
base_url = "https://catalog.csun.edu/"

db_connection = mysql.connector.connect(
    host="localhost", 
    user="connorjuman",  
    password="connorjuman", 
    database="course_info" 
)
cursor = db_connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS degree_programs_summary (
    id INT AUTO_INCREMENT PRIMARY KEY,
    program_name VARCHAR(255),
    department VARCHAR(255),
    program_summary TEXT
)
""")


# Function to scrape the department links and program links
def scrape_department_and_program_links(base_url):
    # Send a request to the departments page
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    # Get the HTML content of the base page
    response = requests.get(base_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all department links
    department_links = soup.find_all('a', class_='dept-item')
    print(department_links)

    # List to store program links
    program_links = []

    # Iterate over each department link to find program links
    for link in department_links:
        dept_link = link.get('href')
        if dept_link:
            # Modify the link to point to the programs page
            programs_link = dept_link.replace('overview', 'programs')
            # Get the HTML content of the programs page
            programs_response = requests.get(programs_link, headers=headers)
            programs_soup = BeautifulSoup(programs_response.content, 'html.parser')

            # Find all program links within the department
            program_sub_links = programs_soup.find_all('a', class_='csun-subhead')
            for program_link in program_sub_links:
                program_sub_link = program_link.get('href')
                if program_sub_link:
                    program_links.append(program_sub_link)
            print(program_links)
    return program_links

def scrape_program_requirements(program_link):
    # Send a request to the departments page
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(program_link, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    # Find all h4 elements with the specified color
    headers = soup.find_all('h4')
    for header in headers:
        # Initialize an empty list to store course links for this header
        course_links = []
        program_requirements = []
        # Initialize an empty string to store other info for this header
        other_info = ""

        # Find the next sibling that is a p tag
        next_p = header.find_next_sibling('p')
        while next_p:
            # Find all a tags within this p tag
            a_tags = next_p.find_all('a')
            for a_tag in a_tags:
                href = a_tag.get('href')
                link_text = a_tag.text
                course_links.append(href)
                program_requirements.append(link_text)


            # Update other_info with any text in the p tag that is not part of an a tag
            other_info += next_p.text

            # Move to the next p tag
            next_p = next_p.find_next_sibling('p')

        print("this is other info", other_info)
        print("this is program requirements", program_requirements)            

# Get the program links and print them
# program_links = scrape_department_and_program_links(base_url)
# print(program_links)

# Scrape the program requirements for the first program
# program_link = 'https://catalog.csun.edu/academics/ling/programs/ba-linguistics/'
# scrape_program_requirements(program_link)
        
program_name = "B.S. in Computer Science"
department = "Computer Science"
program_summary = """
Program: B.S. in Computer Science
Description: Provides a broad knowledge of computing and is designed for students interested in graduate work and software project development. Includes core courses and a senior electives package.

Requirements:
- Total Units: 120-123
- Core Courses: COMP 110/L, COMP 122/L, COMP 182/L, COMP 222, COMP 256/L, COMP 282, MATH 150A/B, MATH 262, PHIL 230
- Lower Division Science Electives: Choose one life science course (BIOL 106/L, BIOL 107/L, GEOL 110/112) and one physical science course (CHEM 101/D/L, GEOG 101/102, GEOG 103/105, GEOL 101/102, PHYS 220A/L)
- Upper Division Required Courses: COMP 310, COMP 322/L, COMP 324, COMP 333, COMP 380/L, COMP 482 or MATH 482, COMP 490/L, COMP 491/L, MATH 340
- Upper Division Electives: 15 units of 400- or 500-level CS courses (excluding specific courses)
- General Education: 48 units, with 18 units satisfied by major coursework

Special Requirements:
- Laptop Requirement: Must meet minimum specifications.
- Grade Requirements: Minimum of "C" for major courses and "C-" for others.

Note: GEOL 110 and GEOL 112 can only be used to satisfy one requirement.
"""

# cursor.execute("""
#     INSERT INTO degree_programs_summary (program_name, department, program_summary)
#     VALUES (%s, %s, %s);
# """, (program_name, department, program_summary))


program_name = "B.S. in Accountancy"
department = "Accounting"
program_summary = """
Program: B.S. in Accountancy
Options: Professional Accountancy, Information Systems

Description:
The Accountancy program is demanding, competitive, and rigorous, focusing on developing critical thinking, problem-solving, communication, and decision-making skills. It provides an understanding of accounting theory, technical procedures, and professional standards and ethics. Admission is based on preparation and performance, with a high level of maturity, motivation, and self-discipline expected.

Requirements:
- Total Units: 120
- Core Courses: ACCT 220, ACCT 230, ACCT 350-352, ACCT 380, ACCT 440, ACCT 460, BUS 302, BUS 302L, BUS 497A/B, FIN 303, MGT 360, MKT 304, SOM 306, BLAW 308, IS 312, COMS 356, RS 361
- Lower Division Business Core: 27-28 units (ACCT 220, ACCT 230, BLAW 280, ECON 160, ECON 161, ENGL 205, IS 212, MATH 103, SOM 120 or MATH 140 or MATH 140BUS)
- Upper Division Business Core: 19 units (BUS 302, BUS 302L, BUS 497A/B, FIN 303, MGT 360, MKT 304, SOM 306)
- Professional Accountancy Option: 15 units (ACCT 441, ACCT 450, ACCT 475, select one from BLAW 368/JS 318/PHIL 305, select one from ACCT 465/ACCT 497A-Z/ACCT 542)
- Information Systems Option: 12 units (IS 431, IS 435, IS 441, IS 451)
- General Education: 48 units, with 21 units satisfied by major coursework

Special Requirements:
- Grade Requirements: Minimum of 'C' for major courses.
- CPA Licensure: A 3-unit accounting ethics course, such as ACCT 511, is required for CPA licensure.
"""

cursor.execute("""
    INSERT INTO degree_programs_summary (program_name, department, program_summary)
    VALUES (%s, %s, %s);
""", (program_name, department, program_summary))

program_name = "B.A. in Africana Studies"
department = "Africana Studies"
program_summary = """
Program: B.A. in Africana Studies
Options: African and African-American Social Sciences, African and African-American Humanities and Cultural Studies, African-American Urban Education

Description:
The Africana Studies (AFRS) major is a multidisciplinary academic major (45 units) designed for students who want to gain an understanding of the history, psychology, sociology, literature, culture, and education of African-Americans and other Africans in the diaspora and the continent. The three specific options within the major enable students to concentrate their efforts on certain aspects of this broad subject. These options are intended to enhance students’ preparation for both graduate school and employment. By carefully selecting General Education courses in consultation with an AFRS advisor, students majoring in AFRS also have the opportunity to complete a second major.

Credential Information:
Africana Studies majors interested in teaching social studies at the middle school or high school level may combine their major program with the Single Subject Social Science Subject Matter Program in the College of Social and Behavioral Sciences (CSBS) to meet requirements for entering a Single Subject Credential program.

Requirements:
- Total Units: 120
- Core Courses: AFRS 100, AFRS 168, AFRS 201, AFRS 220 or AFRS 221, AFRS 245 or AFRS 252, AFRS 271, AFRS 272
- African and African-American Social Sciences Option Courses: AFRS 301, AFRS 320 or AFRS 322, AFRS 350, AFRS 361, AFRS 392A-Z or AFRS 486SOC, AFRS 398, AFRS 498, plus one elective from a specified list
- African and African-American Humanities and Cultural Studies Option Courses: AFRS 226, AFRS 332 or AFRS 346, AFRS 344 or AFRS 451, AFRS 350, AFRS 366 or AFRS 382, AFRS 498, plus two electives from either the Humanities or Cultural Studies Track
- African-American Urban Education Option Courses: AFRS 350, AFRS 391 or AFRS 392, AFRS 397, AFRS 417, AFRS 420 or AFRS 421, AFRS 498, plus two electives from a specified list
- General Education: 48 units, with 12-15 units satisfied by major coursework

Special Requirements:
- Language: All students majoring in Africana Studies are encouraged to take foreign languages (French, Portuguese, Spanish, or Swahili recommended).
- Double Major: Students have the opportunity to complete a second major by carefully selecting General Education courses in consultation with an AFRS advisor.

Total Units in the Major/Option: 45
General Education Units: 33-36
Additional Units: 39-42
Total Units Required for the B.A. Degree: 120

"""

cursor.execute("""
    INSERT INTO degree_programs_summary (program_name, department, program_summary)
    VALUES (%s, %s, %s);
""", (program_name, department, program_summary))

program_name = "B.A. in Anthropology"
department = "Anthropology"
program_summary = """
Program: B.A. in Anthropology

Description:
Anthropology involves the study of people, their origins, their biological variations and characteristics, their languages and cultural patterns, their social structures and institutions, and their adaptation to their environment. The major is designed to contribute to a student's liberal education and to prepare the student for graduate work, teaching, or other professional pursuits. The minor complements a wide variety of other majors by exposing students to key issues in multiculturalism, human diversity, and anthropological methodology.

Social Science Subject Matter Program for the Single Subject Credential:
Anthropology majors interested in teaching social studies at the middle school or high school level may combine their major program with the Single Subject Social Science Subject Matter Program to meet requirements for entering a Single Subject Credential Program.

Requirements:
- Total Units: 120
- Foundations (12 units): ANTH 151, ANTH 152, ANTH 153, ANTH 303
- Peoples and Places (3 units): Choose one from ANTH 306, ANTH 307, ANTH 338, ANTH 345, ANTH 351, ANTH 352, ANTH 353, ANTH 356
- Method and Theory (3 units): Choose one from ANTH 473, ANTH 474, ANTH 475, ANTH 519, ANTH 574, ANTH 575
- Seminar (3 units): Choose one from ANTH 490A-E, ANTH 516, ANTH 521, ANTH 560
- Breadth Electives (12 units): Choose one course from each subdiscipline (Cultural Anthropology, Biological Anthropology, Archaeology, Applied Anthropology)
- Additional Electives (12 units): Choose four additional 3-unit upper division courses in Anthropology
- General Education: 48 units, with 9 units satisfied by major coursework

Special Requirements:
- Optional Program: Students may devise an Anthropology major program that reflects specialized or interdisciplinary interests with at least 42 semester units, of which 36 or more are upper division.

Total Units in the Major: 45
General Education Units: 39
Additional Units: 36
Total Units Required for the B.A. Degree: 120
"""

cursor.execute("""
    INSERT INTO degree_programs_summary (program_name, department, program_summary)
    VALUES (%s, %s, %s);
""", (program_name, department, program_summary))

program_name = "B.A. in Art"
department = "Art and Design"
program_summary = """
Program: B.A. in Art

Description:
The Department of Art and Design offers a curriculum designed for students wishing a liberal arts education in art and design. Emerging artists have numerous opportunities available to them for expressing their creativity and obtaining employment after graduation. Students may explore several areas of art making and choose the field that best fits their interests and talents. The curriculum up to the B.A. degree is designed for students interested in a liberal arts program with an emphasis in art, specialized study in art, preparation for graduate study in art, preparation for academic and professional fields, and/or art teaching credential preparation.

Program Requirements:
- Total Units: 120
- Lower Division Core Foundation Requirements (15 units): ART 124A, ART 140, ART 141, plus two courses from ART 110, ART 112, ART 114
- Lower Division Courses by Area of Concentration (minimum of 9 units): 100- and 200-level courses in consultation with a department advisor
- Upper Division Core Requirements (12 units): ART 307 or another 300-level course in student's selected area of concentration, ART 438/L or specific courses depending on the area of concentration, plus one course from ART 318, ART 448, and one course from 300-, 400-, and 500-level Art History
- Upper Division Courses by Area of Concentration (21 units): A minimum of 21 units of upper division courses in one or more areas of concentration
- General Education: 48 units, with 3 units satisfied by major coursework

Areas of Concentration:
- Animation: ART 124B, ART 263, ART 363B, ART 364, plus select from ART 463 or ART 465
- Art Education: Select at least one of ART 124B, ART 148, or ART 200; ART 478/L, ART 482, ART 483/L, ART 490
- Art History: Select from ART 110, ART 112 or ART 114; ART 510; plus five additional 400- or 500-level courses
- Ceramics: ART 235, ART 267, ART 366, ART 367, ART 467
- Drawing: ART 124B, ART 148, ART 324A, ART 330
- Graphic Design: ART 243, ART 244, ART 313, ART 343, ART 344, ART 444
- Illustration: ART 124B, ART 222, ART 322A, ART 322B, ART 322C, ART 422
- Interdisciplinary: ART 124B, ART 148, ART 488, ART 494
- Painting: ART 124B, ART 227, ART 326, ART 327, ART 429
- Photo/Video: ART 250, ART 350, ART 351, ART 353, ART 357, ART 450, ART 455A, ART 455B, ART 455C
- Printmaking: ART 124B, ART 237, ART 437; select from ART 337A, ART 337B, ART 337C, ART 337D
- Sculpture: ART 124B, ART 235, ART 335, ART 339, ART 435, ART 439

Credential Information:
An approved Subject Matter Program preparing students for a Single Subject Teaching Credential in Art (K-12) is available. The program provides students with a strong foundation in and understanding of visual art, as well as coursework and field experiences necessary to teach visual art to the diverse public school student populations in the PK-12 schools of California.

Total Units in the Major: 57
General Education Units: 45
Additional Units: 18
Total Units Required for the B.A. Degree: 120
"""

cursor.execute("""
    INSERT INTO degree_programs_summary (program_name, department, program_summary)
    VALUES (%s, %s, %s);
""", (program_name, department, program_summary))

program_name = "B.A. in Asian American Studies"
department = "Asian American Studies"
program_summary = """
Program: B.A. in Asian American Studies
Options: Standard Major, Double Major

Description:
The Asian American Studies department provides an interdisciplinary liberal arts program designed to develop student skills in critical analysis, writing, communication, and reasoning, while retrieving, documenting, and analyzing the literary, artistic, economic, social, political, and historical experiences of Asians in the United States. The department offers a Bachelor of Arts major with two options and a minor in Asian American Studies.

Requirements:
- Total Units: 120
- Core Courses (21 units): AAS 100 or AAS 345, AAS 201, AAS 210, AAS 220 or AAS 230, AAS 311, AAS 360, AAS 390/F
- Area Courses for Standard Major Option (18 units): Select courses from Cultural and Literary Studies, Ethnic and Comparative Experiences, Gender and Sexuality Studies, Law, Policy and Institutions, and Social Relations and Family
- Area Courses for Double Major Option (6 units): Select any two courses from the above categories
- Advanced Seminar/Special Topics Course (3 units): Select one from AAS 495, AAS 497
- General Education: 48 units, with 15 units satisfied by major coursework for the Standard Major Option and 9 units for the Double Major Option

Special Requirements:
- Double Major: The Double Major Option is designed for students who choose to double major in Asian American Studies as their second field of study.

Total Units in the Major/Option: 42 for Standard Major, 30 for Double Major
General Education Units: 33
Additional Units: 45
Total Units Required for the B.A. Degree: 120

"""

cursor.execute("""
    INSERT INTO degree_programs_summary (program_name, department, program_summary)
    VALUES (%s, %s, %s);
""", (program_name, department, program_summary))

# Commit the changes and close the connection
db_connection.commit()
cursor.close()
db_connection.close()




