import mysql.connector
from anthropic import Anthropic
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection
connection = mysql.connector.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', 'yzyIVYmySQL34'),
    database=os.getenv('DB_NAME', 'sports'),
    charset="utf8mb4"
)
cursor = connection.cursor()

anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))


def get_all_sports_clubs():
    """Fetch all sports club names from the clubs table"""
    cursor.execute("SELECT club_name FROM clubs")
    clubs = [row[0] for row in cursor.fetchall()]
    return clubs

def get_club_recommendations(question, all_clubs):
    """Get club recommendations from Claude based on user's question"""
    anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    clubs_list = "\n".join([f"{i+1}. {club}" for i, club in enumerate(all_clubs)])
    
    response = anthropic.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""You are tasked with recommending sports clubs based on a student's interests. Here is the complete list of available clubs:

{clubs_list}

Based on this query: "{question}"

Please provide a numbered list of the top 1-5 most relevant clubs. Only include the club names exactly as they appear in the list, with no additional text or explanations. Format your response as:
1. [Club Name]
2. [Club Name]
etc.

Do not include any other text, introductions, or explanations."""
        }]
    )
    
    return response.content[0].text.strip()

def extract_club_names(recommendations):
    """Extract club names from the numbered list"""
    lines = recommendations.split('\n')
    club_names = []
    for line in lines:
        if line.strip():  # Skip empty lines
            # Remove the number and period, then strip whitespace
            club_name = line.split('. ', 1)[1].strip() if '. ' in line else line.strip()
            club_names.append(club_name)
    return club_names

def get_club_details(club_names):
    """Fetch full details for the recommended clubs"""
    club_details = []
    for name in club_names:
        cursor.execute("SELECT * FROM clubs WHERE club_name = %s", (name,))
        details = cursor.fetchone()
        if details:
            club_details.append({
                'id': details[0],
                'name': details[1],
                'link': details[2],
                'description': details[3],
                'contact': details[4]
            })
    return club_details

def create_advisor_response(question, club_details):
    """Generate a friendly advisor-like response with club recommendations"""
    club_details_text = "\n\n".join([
        f"Name: {club['name']}\nLink: {club['link']}\nDescription: {club['description']}\nContact: {club['contact']}"
        for club in club_details
    ])
    
    response = anthropic.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1500,
        messages=[{
            "role": "user",
            "content": f"""You are a friendly student advisor helping a student find sports clubs that match their interests. The student asked: "{question}"

Here are the details of the recommended clubs:

{club_details_text}

Please provide a warm, encouraging response that:
1. Acknowledges their interests
2. Introduces the recommended clubs naturally in conversation
3. Highlights key aspects of each club that align with their interests
4. Includes relevant contact information and links
5. Encourages them to reach out to the clubs
6. Offers to help if they have more questions

Keep the tone friendly and supportive, like a helpful advisor having a conversation with a student."""
        }]
    )
    
    return response.content[0].text

def answer_sports_question(question):
    """Main function to handle the complete club recommendation process"""
    # Get all available clubs
    all_clubs = get_all_sports_clubs()
    
    # Get initial recommendations from Claude
    recommendations = get_club_recommendations(question, all_clubs)
    
    # Extract club names from recommendations
    club_names = extract_club_names(recommendations)
    
    # Get full details for recommended clubs
    club_details = get_club_details(club_names)
    
    # Generate friendly advisor response
    final_response = create_advisor_response(question, club_details)
    
    return final_response

# Example usage:
response = answer_sports_question("I'm interested in joining a sports club that focuses on outdoor activities and environmental conservation.")
print(response)