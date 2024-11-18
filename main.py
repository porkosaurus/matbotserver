import os
from tempfile import NamedTemporaryFile
import json
from openai import OpenAI
import time as time_module
# import spacy
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from format import format_answer_with_openai
# from model1 import answer_query_with_assistant, answer_general_question, answer_map_question, answer_query_model1
from model2 import answer_query_model2
# from branches.degrees_branch import answer_degree_question
# from branches.map_branch import answer_map_question
from branches.general_branch import answer_general_question
from branches.courses_branch import answer_course_question
# from branches.amenities_branch import answer_amenities_question
from branches.events_branch import answer_events_question
from branches.clubs_branch import answer_clubs_question
from branches.sports_branch import answer_sports_question
from branches.category_branch import answer_category_question
from google.cloud import translate_v2 as translate
from google.cloud import texttospeech
from google.cloud import speech
# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# # Initialize the Google Cloud Translate client
translate_client = translate.Client()

# Initialize the Flask application
app = Flask(__name__)
CORS(app, origins=["https://matbot-csun.netlify.app", "http://localhost:3000"])
claude_api_key = os.getenv('ANTHROPIC_API_KEY')

@app.route('/chatbot', methods=['POST'])
def chatbot():
    data = request.json
    question = data.get('question')
    context = data.get('context', '')
    selected_model = data.get('model', 'model2')

    if selected_model == 'model1':
        base_answer = answer_query_model2(question, context)
    elif selected_model == 'model2':
        base_answer = answer_query_model2(question, context)
    else:
        base_answer = "Invalid model selected"

    # Store the base answer and the formatted answer
    # (You can modify this part to store the answers in a database or file, if needed)

    return jsonify({'base_answer': base_answer, 'formatted_answer': base_answer})



# @app.route('/translate', methods=['POST'])
# def translate():
#     data = request.json
#     text = data.get('text')
#     target_language = data.get('target_language')

#     translation = translate_client.translate(text, target_language=target_language)
#     formatted_translation = format_answer_with_openai(translation['translatedText'])

#     return jsonify({'translated_text': formatted_translation})


# @app.route('/read_aloud', methods=['POST'])
# def read_aloud():
#     print("audio request received")
#     data = request.json
#     text = data.get('text')
#     language = data.get('language')

#     # Create a Text-to-Speech client
#     client = texttospeech.TextToSpeechClient()

#     # Set the text input
#     text_input = texttospeech.SynthesisInput(text=text)

#     # Configure the voice settings
#     voice = texttospeech.VoiceSelectionParams(
#         language_code=language,
#         ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
#     )

#     # Set the audio configuration
#     audio_config = texttospeech.AudioConfig(
#         audio_encoding=texttospeech.AudioEncoding.MP3
#     )

#     # Perform the text-to-speech request
#     response = client.synthesize_speech(
#         input=text_input, voice=voice, audio_config=audio_config
#     )
#     print("audio response sent")

#     # Return the audio content as a response
#     return response.audio_content, 200, {'Content-Type': 'audio/mp3'}

# @app.route('/speech_to_text', methods=['POST'])
# def speech_to_text():
#     # Get the audio file from the request
#     audio_file = request.files['audio']
#     print("Received audio file:", audio_file)  # Check if the audio file is received

#     # Create a Speech-to-Text client
#     client = speech.SpeechClient()

#     # Load the audio file into memory
#     audio_content = audio_file.read()
#     print("Audio content size:", len(audio_content)) 


#     # Configure the audio and recognition settings
#     audio = speech.RecognitionAudio(content=audio_content)
#     config = speech.RecognitionConfig(
#         encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
#         sample_rate_hertz=48000,  # Update this value based on your audio file
#         language_code='en-US'
#     )

#     # Perform speech recognition
#     response = client.recognize(config=config, audio=audio)
#     print("Speech recognition response:", response)  # Check the response
#     print("Results:", response.results)  # Check the results
#     # Extract the transcription results
#     transcriptions = [result.alternatives[0].transcript for result in response.results]
#     print("Transcriptions:", transcriptions)  # Check the transcriptions
#     # Return the transcriptions as a JSON response
#     return jsonify({'transcriptions': transcriptions})

@app.route('/hello', methods=['GET'])
def hello():
    return '<h1>Hello, World!</h1>'


# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)