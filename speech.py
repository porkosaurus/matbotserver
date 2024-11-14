# from google.cloud import texttospeech
# import os
# # Create a Text-to-Speech client
# client = texttospeech.TextToSpeechClient()

# # Set the text input
# text_input = texttospeech.SynthesisInput(text="Hello, world!")

# # Configure the voice settings
# voice = texttospeech.VoiceSelectionParams(
#     language_code="en-US",
#     ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
# )

# # Set the audio configuration
# audio_config = texttospeech.AudioConfig(
#     audio_encoding=texttospeech.AudioEncoding.MP3
# )

# # Perform the text-to-speech request
# response = client.synthesize_speech(
#     input=text_input, voice=voice, audio_config=audio_config
# )

# # Save the audio to a file
# with open("output.mp3", "wb") as out:
#     out.write(response.audio_content)
#     print("Audio content written to 'output.mp3'")
