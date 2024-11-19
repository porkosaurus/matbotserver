import os
import torch
import numpy as np
from torch import nn
from transformers import RobertaTokenizer, RobertaModel
import mysql.connector
from mysql.connector import Error
# from branches.degrees_branch import answer_degree_question
# from branches.map_branch import answer_map_question
from branches.dining_branch import answer_dining_question
from branches.general_branch import answer_general_question
from branches.courses_branch import answer_course_question
from branches.events_branch import answer_events_question
from branches.clubs_branch import answer_clubs_question
# from branches.sports_branch import answer_sports_question
from branches.category_branch import answer_category_question
import re
from anthropic import Anthropic
import os
from dotenv import load_dotenv

# Import the general_education and research_files from separate files
from general_education_data import general_education
from research_files_data import research_files

# Load environment variables
load_dotenv()

connection = mysql.connector.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME', 'csun'),
    charset="utf8mb4"  
)
cursor = connection.cursor()

anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Original QueryClassifier for general queries
class QueryClassifier(nn.Module):
    def __init__(self, n_classes):
        super(QueryClassifier, self).__init__()
        self.roberta = RobertaModel.from_pretrained('roberta-base')
        self.dropout = nn.Dropout(p=0.1)
        self.fc = nn.Linear(self.roberta.config.hidden_size, n_classes)
    
    def forward(self, input_ids, attention_mask):
        outputs = self.roberta(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.last_hidden_state[:, 0, :]
        x = self.dropout(pooled_output)
        return self.fc(x)

# QueryClassifier for course-specific queries
class CourseQueryClassifier(nn.Module):
    def __init__(self, n_classes):
        super(CourseQueryClassifier, self).__init__()
        self.roberta = RobertaModel.from_pretrained('roberta-base')
        self.dropout = nn.Dropout(p=0.1)
        self.fc = nn.Linear(self.roberta.config.hidden_size, n_classes)
        self.softmax = nn.Softmax(dim=1)

    def forward(self, input_ids, attention_mask):
        outputs = self.roberta(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.last_hidden_state[:, 0, :]
        x = self.dropout(pooled_output)
        logits = self.fc(x)
        probs = self.softmax(logits)
        return probs

# Function to load the general query model
def load_model(model_path, device):
    checkpoint = torch.load(model_path, map_location=device)
    loaded_model = QueryClassifier(n_classes=len(checkpoint['label_encoder'].classes_))
    loaded_model.load_state_dict(checkpoint['model_state_dict'])
    loaded_model.to(device)
    loaded_model.eval()
    return loaded_model, checkpoint['label_encoder']

# Function to load the course query model
def load_course_model(model_path, device):
    checkpoint = torch.load(model_path, map_location=device)
    loaded_model = CourseQueryClassifier(n_classes=len(checkpoint['label_encoder'].classes_))
    loaded_model.load_state_dict(checkpoint['model_state_dict'])
    loaded_model.to(device)
    loaded_model.eval()
    return loaded_model, checkpoint['label_encoder']

# Function to classify general queries
def classify_query(query, model, tokenizer, label_encoder, device):
    model.eval()
    tokens = tokenizer.encode_plus(query, max_length=128, truncation=True, padding='max_length', return_tensors='pt')
    input_ids = tokens['input_ids'].to(device)
    attention_mask = tokens['attention_mask'].to(device)

    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        probs = torch.softmax(outputs, dim=1)
        probs = probs.cpu().numpy()[0]
        predicted_label = np.argmax(probs)
        confidence = probs[predicted_label]
        return label_encoder.inverse_transform([predicted_label])[0], confidence

# Function to classify course queries into top 3 categories
def classify_query_top_3(query, model, tokenizer, label_encoder, device):
    model.eval()
    tokens = tokenizer.encode_plus(query, max_length=128, truncation=True, padding='max_length', return_tensors='pt')
    input_ids = tokens['input_ids'].to(device)
    attention_mask = tokens['attention_mask'].to(device)

    with torch.no_grad():
        outputs = model(input_ids, attention_mask)
        probs = outputs.cpu().numpy()[0]
        top_3_indices = np.argsort(probs)[-3:][::-1]
        top_3_labels = label_encoder.inverse_transform(top_3_indices)
        top_3_confidences = probs[top_3_indices]

        filtered_results = [(label, confidence) for label, confidence in zip(top_3_labels, np.round(top_3_confidences, 2)) if confidence > 0.00]

        return filtered_results

# Function to fix encoding issues
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

# Function to process course names
def process_course_names(courses):
    processed_courses = []
    for course in courses:
        course = re.sub(r'^\d+\.\s*', '', course).strip()
        match = re.match(r'^([A-Z]{2,4})\s*(\d{3}[A-Z]?(?:/[A-Z])?)(?:/L)?\.*\s*(.*)', course)
        if match:
            department = match.group(1)
            code = match.group(2)
            course_code = f"{department} {code}"
            course_code = course_code.replace('/', '').replace('-', '')
            processed_courses.append(course_code)
        else:
            processed_courses.append(course)
    return processed_courses

# Main query answering function
def answer_query_model2(query, context=""):
    # Classify the query
    response_text, confidence = classify_query(query, loaded_model, tokenizer, loaded_label_encoder, device)
    print(f"Classification Confidence: {confidence}")
    print({response_text})
    if confidence < 0.7:
        return answer_general_question(query, context)

    # Call the appropriate function based on the context
    if response_text in ["1", "courses"]:
        return answer_course_question(query, context, cursor, connection, general_education, course_model, tokenizer, course_label_encoder, device)
    # elif response_text in ["2", "Degree Requirements"]:
    #     return answer_degree_question(query, context, cursor, connection, general_education)
    elif response_text in ["3", "sports"]:
        return answer_events_question(query, context)
    elif response_text in ["4", "clubs"]:
        return answer_clubs_question(query, context)
    elif response_text in ["5", "events"]:
        return answer_events_question(query, context)
    elif response_text in ["6", "Research Projects"]:
        return answer_category_question(query, context, "Research Projects.txt")
    elif response_text in ["8", "map"]:
        return answer_map_question()
    elif response_text in ["dining"]:
        return answer_dining_question(query, context)
    elif response_text in ["9", "tutoring"]:
        return answer_general_question(query, context)
    elif response_text in research_files:
        print("this is found", response_text)
        return answer_category_question(query, context, response_text)
    else:
        return "I'm sorry, I couldn't determine the context of your query. Please try again with more specific information."

# Load the general query model and tokenizer
model_save_path = 'query_classifier_model.pth'
device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
tokenizer = RobertaTokenizer.from_pretrained('roberta-base')
loaded_model, loaded_label_encoder = load_model(model_save_path, device)

# Load the course query model and tokenizer
# course_model_path = 'course_classifier_model_v2.pth'
course_model_path = 'department_classifier_model.pth'
course_model, course_label_encoder = load_course_model(course_model_path, device)

def interactive_chatbot():
    print("Welcome to the CSUN Chatbot! Type 'exit' to end the conversation.")
    while True:
        query = input("You: ").strip()
        if query.lower() == 'exit':
            print("Thank you for using the CSUN Chatbot. Goodbye!")
            break
        
        answer = answer_query_model2(query)
        print(f"Chatbot: {answer}")

if __name__ == '__main__':
    interactive_chatbot()



# Example usage
queries = [
    "What subjects are offered at the SMART Lab?",
    "Who is the vice president for Information Technology?",
    "What is Shake Smart?",
    "What is ARCS and MMC?",
    "How many undergraduate majors are there?",
    "What is the most popular majors at CSUN?",
    "What is Tseng College exactly?",
    "What should I do if I am denied from CSUN?",
    "What is the Fulbright Fellowship Program?",
    "Where are the gender neutral bathrooms on campus?",
    "What is the DREAM Center?",
    "Tell me about sports events coming up",
    "Need to charge my phone ASAP, where should I go?",
    "Anywhere on Campus that I can get a check up?",
]