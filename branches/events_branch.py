from anthropic import Anthropic
from ..events.academics import get_academics_information
from ..events.athletics import get_athletics_information
from ..events.emp import get_emp_information
from ..events.fut_stu import get_fut_stu_information
from ..events.stu import get_stu_information
from ..events.usu import get_usu_information
import os
from dotenv import load_dotenv

# Initialize the Anthropic client
anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

def answer_events_question(question, context):
    # First LLM request
    response = anthropic.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=100,
        messages=[
            {"role": "user", "content": f"""You are an assistant. Your task is to categorize the user's query into one of the following categories: Academics, Athletics, Employee, Future Student, Current Student, or University Student Union (USU). Respond with just one of these categories and nothing else.

            Question: {question}

            Provide your response:"""}
        ]
    )

    category = response.content[0].text.strip()

    # Call the corresponding function based on the category
    if category == "Academics":
        additional_info = get_academics_information()
    elif category == "Athletics":
        additional_info = get_athletics_information()
    elif category == "Employee":
        additional_info = get_emp_information()
    elif category == "Future Student":
        additional_info = get_fut_stu_information()
    elif category == "Current Student":
        additional_info = get_stu_information()
    elif category == "University Student Union":
        additional_info = get_usu_information()
    else:
        additional_info = "No relevant information found."

    # Prepare the information for the second LLM request
    description_text = f"{category}:\n{additional_info}"

    response = anthropic.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": f"""You are a helpful student advisor at a university providing event recommendations based on the event list provided. Be conversational but provide some options for the student, come across as a human.

            Question: {question}

            Suggested Events:
            {description_text}

            Provide your response:"""}
        ]
    )

    print(response.content[0].text)

    return response.content[0].text
