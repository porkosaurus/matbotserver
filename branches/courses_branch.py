import torch
import numpy as np
import re
import mysql.connector
from transformers import RobertaTokenizer, RobertaModel
from anthropic import Anthropic
import os
# Load environment variables
from dotenv import load_dotenv
load_dotenv()

connection = mysql.connector.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', 'yzyIVYmySQL34'),
    database=os.getenv('DB_NAME', 'csun'),
    charset="utf8mb4"  
)
cursor = connection.cursor()

anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))


# Define your model class (QueryClassifier) - Replace with your actual model architecture
class QueryClassifier(torch.nn.Module):
    def __init__(self, n_classes):
        super(QueryClassifier, self).__init__()
        self.roberta = RobertaModel.from_pretrained('roberta-base')
        self.dropout = torch.nn.Dropout(p=0.1)
        self.fc = torch.nn.Linear(self.roberta.config.hidden_size, n_classes)
        self.softmax = torch.nn.Softmax(dim=1)

    def forward(self, input_ids, attention_mask):
        outputs = self.roberta(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.last_hidden_state[:, 0, :]
        x = self.dropout(pooled_output)
        logits = self.fc(x)
        probs = self.softmax(logits)
        return probs

# Load the model and tokenizer
def load_model(model_path, device):
    checkpoint = torch.load(model_path, map_location=device)
    loaded_model = QueryClassifier(n_classes=len(checkpoint['label_encoder'].classes_))
    loaded_model.load_state_dict(checkpoint['model_state_dict'])
    loaded_model.to(device)
    loaded_model.eval()
    return loaded_model, checkpoint['label_encoder']

# Function to classify query into top 3 categories
def classify_query_top_3(query, model, tokenizer, label_encoder, device):
    model.eval()
    tokens = tokenizer.encode_plus(query, max_length=128, truncation=True, padding='max_length', return_tensors='pt')
    input_ids = tokens['input_ids'].to(device)
    attention_mask = tokens['attention_mask'].to(device)

    with torch.no_grad():
        outputs = model(input_ids, attention_mask)
        probs = outputs.cpu().numpy()[0]
        top_3_indices = np.argsort(probs)[-3:][::-1]  # Get top 3 indices sorted by confidence in descending order
        top_3_labels = label_encoder.inverse_transform(top_3_indices)
        top_3_confidences = probs[top_3_indices]

        filtered_results = [(label, confidence) for label, confidence in zip(top_3_labels, np.round(top_3_confidences, 2)) if confidence > 0.00]

        return filtered_results

# Function to fix encoding issue
def fix_encoding_issue(text):
    if text is None:
        return ""
    try:
        return text.encode('utf-8').decode('utf-8')
    except UnicodeEncodeError:
        try:
            return text.encode('latin1').decode('utf-8')
        except UnicodeDecodeError:
            return text.encode('ascii', errors='replace').decode('ascii')

import re

def process_course_names(courses):
    processed_courses = []
    for course in courses:
        course = re.sub(r'^\d+\.\s*', '', course).strip()
        # Adjust the regex to capture department, course code, and the optional lab or section suffix
        match = re.match(r'^([A-Z]{2,4})\s*(\d{3}[A-Z]?(?:/[A-Z])?)(?:/L)?\.*\s*(.*)', course)
        if match:
            department = match.group(1)
            code = match.group(2)
            # Remove slashes and dashes in the course code, but leave the suffix intact
            course_code = f"{department} {code}"
            # Remove any slashes from the final course code if needed
            course_code = course_code.replace('/', '').replace('-', '')
            processed_courses.append(course_code)
        else:
            processed_courses.append(course)  # Append original if no match
    return processed_courses

#TODO : ADD STUDENT PERSONALIZATION
taken_courses = ['COMP 122/L', 'MATH 256', 'MATH 150A', 'MATH 150B', 'COMP 182/L', 'ENGL 113A', 'ENGL 113B']
major = "Computer Science"

# Function to answer course-related questions
def answer_course_question(question, context, cursor, connection, general_education, model, tokenizer, label_encoder, device, test_departments=None):
    if test_departments:
        # Use test departments instead of classifier
        top_department_names = test_departments
    else:
        # Your existing classifier code
        top_departments = classify_query_top_3(question, model, tokenizer, label_encoder, device)
        top_department_names = [str(dept.item()) if isinstance(dept, np.str_) else str(dept) for dept, _ in top_departments]

    
    top_department = top_department_names[0]

    # Create placeholders for the IN clause
    placeholders = ', '.join(['%s'] * len(top_department_names))

    # Modify the query to use the correct number of placeholders
    query = f"SELECT `department`, `concentration`, `description` FROM `degree_requirements` WHERE `department` IN ({placeholders})"
    try:
        # Execute the query with the list of department names
        cursor.execute(query, top_department_names)
        department_info = cursor.fetchall()        
        if not department_info:
            return f"I couldn't find any information about courses in the {', '.join(top_department_names)} department(s). Can you please check if the department name is correct or try asking about a different department?"
    
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return "I'm sorry, but I encountered an error while trying to retrieve course information. Please try again later or contact support if the problem persists."

    if department_info:
        # Format the department information
        department_summaries = []
        for dept, concentration, description in department_info:
            department_summaries.append(f"{dept} - {concentration}:\n{description}")
        
        department_summary = "\n\n".join(department_summaries)
    else:
        department_summary = "No requirements found."

    unique_course_names = set()
    for dept in top_department_names:
        cursor.execute("SELECT DISTINCT `course_name` FROM courses WHERE `department` = %s", (dept,))
        dept_courses = [row[0] for row in cursor.fetchall()]
        unique_course_names.update(dept_courses)

    unique_course_list = '\n'.join([f"{i + 1}. {course}" for i, course in enumerate(unique_course_names)])
    response = anthropic.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": f"""You are a smart robot tasked with providing a list of at most the top 20 courses based on a user's question. Your goal is to select courses that align with the user's request while following specific rules and constraints. Here are the inputs you will work with:

<question>
{question}
</question>

<unique_course_list>
{unique_course_list}
</unique_course_list>

<general_education>
{general_education}
</general_education>

<department_summary>
{department_summary}
</department_summary>

<context>
{context}
</context>

Instructions for formatting your response:
1. Provide a numbered list of up to 20 courses.
2. Use the exact format "1. Course Code" for each course (e.g., "1. CHEM 101").
3. Do not include any additional information or text before or after the course codes.
4. Do not say "Okay" or "Here is the list" or include any words beyond the list itself.

Rules and constraints for course selection:
1. Freshmen (first years) and sophomores (second years) are only allowed to take 100 and 200 level courses.
2. Juniors (third years) and seniors (fourth years) can take up to 400 level courses.
3. Graduate students can take higher-level courses.
4. If no age or year is mentioned, recommend 100 and 200 level courses.
5. Always provide a response with a list of 20 courses, regardless of the user's question.
6. Use the course code in your response (e.g., "PLI 342" for a course named "PLI 342- Introduction to Life").
7. Follow the guidelines provided in the department summary when applicable.
8. Do not alter or make up course names or codes.
9. Include no more than 5 general education courses in your response.
10. Do not include the category names for general education courses.

Example of a correct response for a Chemistry major in their first year:
1. CHEM 101
2. MATH 150A
3. CHEM 102
4. CHEM 101D
5. AAS 115
6. ART 100
7. CHEM 110
8. CHEM 110L
9. CHEM 235L
10. MATH 150B
11. CAS 151
12. PHYS 225
13. PHYS 220AL
14. MATH 250
15. DANC 139A
16. CHEM 321L
17. CHEM 122
18. CHEM 162
19. CHEM 107
20. CHEM 351

Now, based on the user's question, the provided course list, general education courses, department summary, and any relevant context from previous conversations, create a list of up to 20 courses following the instructions and rules above. Do not provide any explanation or additional text beyond the numbered list of course codes."""
            }
        ]
    )
    
    courses_response = response.content[0].text.strip()
    courses = courses_response.split('\n')
    processed_courses = process_course_names(courses)

    course_details_dict = {}
    for course_code in processed_courses[:20]:
        course_code_with_quote = f'"{course_code}'
        cursor.execute("SELECT * FROM courses WHERE `course_code` = %s", (course_code_with_quote,))
        course_fetched = cursor.fetchall()
        for detail in course_fetched:
            if course_code not in course_details_dict:
                try:
                    course_details_dict[course_code] = {
                        'course_code': fix_encoding_issue(detail[0]),
                        'course_name': fix_encoding_issue(detail[1]),
                        'department': fix_encoding_issue(detail[2]),
                        'units': detail[3],
                        'class_number': detail[4],
                        'location': fix_encoding_issue(detail[5]),
                        'location_name': fix_encoding_issue(detail[6]),
                        'day': fix_encoding_issue(detail[7]),
                        'time': fix_encoding_issue(detail[8]),
                        'description': fix_encoding_issue(detail[9]),
                        'sessions': []
                    }
                except Exception as e:
                    print(e)
            session_info = {
                'class_number': detail[4],
                'location': f"{fix_encoding_issue(detail[5])} {fix_encoding_issue(detail[6])}",
                'day': fix_encoding_issue(detail[7]),
                'time': fix_encoding_issue(detail[8])
            }
            course_details_dict[course_code]['sessions'].append(session_info)

    course_details_list = []
    for course_code, details in course_details_dict.items():
        try:
            sessions_info = '\n'.join([f"Class Number: {session['class_number']}, Location: {session['location']}, Day: {session['day']}, Time: {session['time']}" for session in details['sessions']])
            course_info = f"{details['course_name']} - {details['department']} department, {details['units']} units, Description: {details['description']}\nSessions:\n{sessions_info}"
            course_details_list.append(course_info)
        except Exception as e:
            print(e)
    course_details_list = '\n\n'.join(course_details_list)
    response = anthropic.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": f"""
You are an AI chatbot designed to assist students in finding the best courses for their academic journey. Your primary task is to recommend courses based on the information provided and the student's specific needs. Follow these instructions carefully:

Important rules and guidelines:
1. Always use the exact names and course codes as provided. Do not alter or make up any course names or codes.
2. Use course descriptions for context, but keep names and codes unchanged.
3. Always provide a recommendation, even if it's challenging to find a perfect match.
4. Respond in a conversational manner suitable for human interaction.
5. Use the general education courses and degree road map as guides based on the user's information.
6. Prioritize the degree road map when giving advice on specific courses for a declared major.
7. When mentioning General Education Courses, use specific examples from the provided list.
8. Recommend courses appropriate to the student's academic level (freshman, sophomore, junior, senior).
9. Only use the departments listed in the provided information.
10. Consider prerequisites and course numbers when making recommendations.
11. When providing course session details (time, date, and location), include information for only one session per course, unless explicitly asked for multiple sessions.
12. Ensure that recommended course dates and times do not clash, and provide only one session time per course unless multiple sessions are specifically requested.

Here is the information you will be working with:

<question>
{question}
</question>

<course_details>
{course_details_list}
</course_details>

<degree_road_map>
{department_summary}
</degree_road_map>

<general_education_courses>
{general_education}
</general_education_courses>

<conversation_context>
{context}
</conversation_context>

Process and use the information as follows:
1. Carefully read the question to understand the student's needs and academic situation.
2. Review the course details list to identify relevant courses.
3. Consult the degree road map to ensure recommendations align with the student's academic progress.
4. Use the general education courses list to suggest specific courses for fulfilling GE requirements.
5. Consider the previous conversation context for any additional relevant information.

When formulating your response:
1. Start with a friendly greeting and acknowledge the student's question.
2. Provide course recommendations based on the student's needs and academic level.
3. Explain why you're recommending each course, referencing the course description or its relevance to their academic journey.
4. If applicable, mention how recommended courses fulfill general education requirements or fit into their degree road map.
5. Be mindful of course prerequisites and numbering when making recommendations.
6. If the question relates to a specific major, prioritize courses from the degree road map.
7. Offer additional advice or context that might be helpful to the student.

Remember:
- Do not alter or make up any course names or codes.
- Ensure recommendations are appropriate for the student's academic level.
- Use only the information provided in the input variables.
- Always provide a recommendation, even if it's not a perfect match.

Provide your response in a conversational tone, structuring it as follows:

[Your conversational response here, including course recommendations and explanations]
"""
            }
        ]
    )

    final_response = response.content[0].text
    print(final_response)
    return final_response



# Load the model, tokenizer, and label encoder
model_path = 'department_classifier_model.pth'
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# model, label_encoder = load_model(model_path, device)
tokenizer = RobertaTokenizer.from_pretrained('roberta-base')


general_education = """
GE A1 - Oral Communication. AAS 151, AFRS 151, CAS 151, CHS 151, COMS 151, QS 151
GE A2 - Written Communication. AAS 113B, AAS 114B, AAS 115, AFRS 113B, AFRS 114B, AFRS 115, CAS 113B, CAS 114B, CAS 115, CHS 113B, CHS 114B, CHS 115, ENGL 113B, ENGL 114B, ENGL 115, LING 113B, QS 113B, QS 114B, QS 115
GE A3 - Critical Thinking. AAS 201, AFRS 204, AIS 210, CHS 202, COMS 225, ENGL 215, GEH 111HON, HIST 202, JS 220, PHIL 100, PHIL 200, PHIL 230, QS 201, RS 204
GE B1 - Physical Science. ASTR 152, ASTR 154, CHEM 100, CHEM 101, CHEM 102, CHEM 103, CHEM 104, CHEM 110, GEOG 101, GEOG 101A, GEOG 103, GEOG 103A, GEOG 112, GEOL 101, GEOL 107, GEOL 110, GEOL 113, GEOL 117, GEOL 122, GEOL 125, PHYS 100A, PHYS 100B, PHYS 111, PHYS 220A, PHYS 220B, SCI 111, SUST 111
GE B2 - Life Science. ANTH 151, BIOL 100, BIOL 101, BIOL 106, BIOL 107, BIOL 218, BIOL 292, GEOL 110, GEOL 113, GEOL 125        
GE B3 - Science Laboratory Activity. ASTR 154L, BIOL 100L, BIOL 101L, BIOL 106L, BIOL 107L, BIOL 218L, BIOL 292L, CHEM 100L, CHEM 101L, CHEM 102L, CHEM 103L, CHEM 104L, CHEM 110L, GEOG 101AL, GEOG 103AL, GEOG 112L, GEOL 102, GEOL 107L, GEOL 112, GEOL 117L, GEOL 123, PHYS 100AL, PHYS 100BL, PHYS 220AL, PHYS 220BL, SCI 111L, SUST 111L
GE B4 - Mathematics and Quantitative Reasoning. COMP 102/L, MATH 102, MATH 103, MATH 105, MATH 106, MATH 131, MATH 140, MATH 140BUS, MATH 140SCI, MATH 141, MATH 150A, MATH 255A, PHIL 135
GE B5 - Scientific Inquiry and Quantitative Reasoning. ANTH 341, ASTR 352, BIOL 306, BIOL 323, BIOL 324, BIOL 325, BIOL 327, BIOL 341, BIOL 362, BIOL 366, BIOL 375, CM 336/L, EOH 353, FCS 315, FCS 323, FCS 324, GEH 333HON, GEOG 311, GEOG 316, GEOG 365, GEOG 366, GEOL 300, GEOL 324, GEOL 327, GEOL 344, HSCI 336, HSCI 337, HSCI 345, KIN 309, LING 303, LING 310, MATH 331, MSE 303, PHIL 325, PHYS 305, PHYS 331, QS 369, RS 366
GE C1 - Arts. AFRS 246, AFRS 280, AFRS 351, ANTH 232, ART 100/L, ART 110, ART 114, ART 124A, ART 140, ART 141, ART 305, CHS 111, CHS 310, COMS 104, COMS 305, CTVA 210, CTVA 215, CTVA 309, CTVA 323, DANC 139A, DANC 144A, DANC 236/L, DANC 380/L, ENGL 208, FCS 111, FLIT 151, FLIT 250, HUM 101, HUM 105, HUM 106, JS 300, KIN 139A, KIN 144A, KIN 236/L, KIN 380/L, LING 240, MUS 105, MUS 106HH, MUS 107, MUS 108, MUS 306, PHIL 314, TH 110, TH 111, TH 310
GE C2 - Humanities. AAS 220, AAS 321, AFRS 245, AFRS 343, AFRS 344, AFRS 346, AFRS 352, AIS 301, AIS 318, ANTH 222, ANTH 326, CAS 201, CHS 201, CHS 350, CHS 351, CHS 380, CHS 381, CHS 382, CLAS 315, CTVA 215, DH 320, ENGL 255, ENGL 258, ENGL 259, ENGL 275, ENGL 300, ENGL 316, ENGL 318, ENGL 322, ENGL 333, ENGL 364, FLIT 151, FLIT 331, FLIT 381, GWS 100, GWS 230, GWS 351, HIST 150, 
HIST 151, HIST 303, HIST 304, HUM 101, HUM 105, HUM 106, JS 100, JS 255, JS 300, JS 333, LING 200, PHIL 150, PHIL 165, PHIL 170, PHIL 180, PHIL 201, PHIL 202, PHIL 240, PHIL 250, PHIL 260, PHIL 265, PHIL 280, PHIL 314, PHIL 325, PHIL 330, PHIL 337, PHIL 349, PHIL 353, PHIL 354, QS 101, QS 303, RS 100, RS 101, RS 304, RS 307, RS 310, RS 356, RS 357, RS 361, RS 362, RS 370, SUST 240, TH 333
GE C3 - US History. AFRS 271, AFRS 272, AIS 250, CHS 245, ECON 175, HIST 270, HIST 271, HIST 370, HIST 371, JOUR 391, PHIL 317, RS 256       
GE D1 - Social Sciences. AAS 210, AAS 350, AFRS 201, AFRS 220, AFRS 221, AFRS 304, AFRS 361, AIS 222, ANTH 150, ANTH 151, ANTH 152, ANTH 153, ANTH 212, ANTH 250, ANTH 262, ANTH 302, ANTH 305, ANTH 319, ANTH 341, CADV 150, CADV 320, CAS 309, CAS 310, CAS 368, CAS 369, CHS 261, CHS 331, CHS 345, CHS 346, CHS 347, CHS 361, CHS 362, CHS 366, CJS 101, CJS 338, COMS 312, COMS 323, ECON 101, ECON 160, ECON 161, ECON 310, ECON 311, ECON 360, FCS 141, FCS 253, FCS 256, FCS 318, FCS 340, FCS 357, FLIT 325, GEH 333HON, GEOG 107, GEOG 150, GEOG 170, GEOG 301, GEOG 321, GEOG 330, GEOG 351, GEOG 370, GWS 110, GWS 220, GWS 222, GWS 300, GWS 320, GWS 340, GWS 351, GWS 370, HIST 110, HIST 111, HIST 341, HIST 342, HIST 350, HIST 380, HIST 389, HSCI 132, HSCI 345, HSCI 369, JOUR 365, JS 318, LING 230, LING 309, MKT 350, PHIL 305, PHIL 391, POLS 156, POLS 225, POLS 310, POLS 350, POLS 380, PSY 150, PSY 
312, PSY 352, PSY 365, RS 240, RTM 301, SOC 150, SOC 200, SOC 305, SOC 324, SUST 300, URBS 150, URBS 310, URBS 380
GE D3/D4 - Constitution of the United States/State and Local Government. AAS 347, AFRS 161, CHS 260, CHS 445, POLS 155, POLS 355, RS 255
GE D4 - California State and Local Government. POLS 403, POLS 490CA
GE E - Lifelong Learning. AAS 230, AAS 390/F, AFRS 337, AIS 301, ART 151, ART 201, BIOL 327, BIOL 375, BLAW 280, BLAW 368, BUS 104, CADV 310, CAS 270/F, CCE 200, CD 133, CD 361, CHS 270SOC/F, CHS 347, CHS 360, CHS 390, CJS 340, CM 336/L, COMP 100, COMP 300, COMS 150, COMS 251, COMS 323, COMS 360, CTVA 100, CTVA 323, DANC 142B, DANC 147, DANC 148, ENGL 306, ENGL 313, ENGL 315, ENT 101, EOH 101, EOH 353, FCS 120, FCS 171, FCS 207, FCS 260, FCS 315, FCS 323, FCS 324, FCS 330, FCS 340, FIN 102, FIN 302, FLIT 234, GEOG 206/L, GEOL 104, GWS 205/CS, HIST 366, HSCI 131, HSCI 170, HSCI 231, HSCI 336, HSCI 337, IS 212, JOUR 100, JOUR 390, JS 
390CS, KIN 115A, KIN 117, KIN 118, KIN 123A, KIN 124A, KIN 125A, KIN 126A, KIN 128, KIN 129A, KIN 130A, KIN 131A, KIN 132A, KIN 
133A, KIN 135A, KIN 142B, KIN 147, KIN 148, KIN 149, KIN 152A, KIN 153, KIN 172, KIN 177A, KIN 178A, KIN 179A, KIN 185A, KIN 195A, LING 310, ME 100, MSE 303, MUS 139A, PHIL 165, PHIL 180, PHIL 250, PHIL 260, PHIL 280, PHIL 305, PHIL 337, QS 302, RTM 251, RTM 278, RTM 301, RTM 310/L, RTM 352, RTM 353/L, SCI 100, SUST 310, TH 243, UNIV 100
GE F - Comparative Cultural Studies. AAS 100, AAS 340, AAS 345, AAS 360, AAS 362, AFRS 100, AFRS 226, AFRS 300, AFRS 320, AFRS 322, AFRS 324, AFRS 325, AFRS 366, AIS 101, AIS 304, AIS 318, AIS 333, ANTH 108, ANTH 308, ANTH 310, ANTH 315, ANTH 345, ARAB 101, ARAB 102, ARMN 101, ARMN 102, ARMN 310, ARMN 360, ART 112, ART 315, BLAW 391, CADV 320, CAS 100, CAS 102, CAS 311, CAS 365, CHIN 101, CHIN 102, CHS 100, CHS 101, CHS 102, CHS 246, CHS 333, CHS 364, CHS 365, CLAS 101L, COMS 356, COMS 360, DANC 384, ENGL 311, ENGL 318, ENGL 371, FLIT 150, FLIT 370, FLIT 371, FLIT 380, FREN 101, FREN 102, GEOG 318, GEOG 322, GEOG 324, GEOG 326, GEOG 334, GWS 100, GWS 110, GWS 300, GWS 351, HEBR 101, HEBR 102, HIST 161, HIST 185, HIST 192, HIST 210, HIST 349A, HIST 349B, HIST 369, ITAL 101, ITAL 102, ITAL 201, JAPN 101, JAPN 102, JAPN 201, JAPN 202, JAPN 204, JOUR 371, JOUR 372, JS 210, JS 306, JS 330, JS 335, JS 378, KIN 384, KIN 385, KOR 101, KOR 102, LING 250, LING 325, MSE 302, MUS 309, MUS 310, PERS 101, PERS 102, PHIL 333, PHIL 343, PHIL 344, PHIL 348, POLS 197, POLS 321, POLS 332, QS 101, QS 208, QS 301, QS 303, QS 304, RS 150, RS 306, RS 365, RS 378, RS 380, RS 385, RS 390, RTM 310/L, RTM 330, RUSS 101, RUSS 102, SOC 306, SOC 307, SOC 335, SPAN 101, SPAN 102, SPAN 103, 
SPAN 220A, SPAN 220B, SPED 200SL, TH 325, URBS 350
"""
model, label_encoder = load_model(model_path, device)
tokenizer = RobertaTokenizer.from_pretrained('roberta-base')
context = ""
# Test with Economics only
response1 = answer_course_question(
    "Give me a schedule for a first year first semester Economics major, I do not want any classes on Fridays, and be brief, include dates and times and locations as well. DO NOT HAVE CLASSES OVERLAPPING",
    context,
    cursor,
    connection,
    general_education,
    model,
    tokenizer,
    label_encoder,
    device,
)

test_questions = [
    # "Give me a schedule as a first year Economics student for this spring semester, include the location that the class is in so I can get there as well as dates and times for each course, and no classes on Friday, Give me specific GE's as well, I have not completed any GE's yet",
    # "Classes to learn about time crystals?",
    # "Classes to learn about Asian American History",
    # "What are the prerequisites for COMP 182/L AND COMP 256/L?",
    # "What are the prerequisites for the machine learning courses at CSUN?",
    # "What are some of the date and times for ACCT 380?",
    # "What are 400 level courses would you recommend, I am interested in machine learning",
    # "I play the guitar, but I don't know what to study, recommend to me some courses"
    ]



# Run the questions through the function
for question in test_questions:
    print(f"Question: {question}")
    response = answer_course_question(question, context, cursor, connection, general_education, model, tokenizer, label_encoder, device)
    print(f"Response:\n{response}\n")