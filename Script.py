import os
import json
import random
import pyttsx3
import azure.cognitiveservices.speech as speechsdk
from flask import Flask, request, jsonify, render_template
from flask.wrappers import Response
from ping import ping
from response import recognize_human_voice_analyze, recognize_ai_voice_analyze
import regex as re
import asyncio

url = "http://127.0.0.1:8080"
Model_version = "openai-whisper-large-v3-1"
openai_Model_ID = "azureml://registries/azureml/models/openai-whisper-large-v3/versions/1"
Endpoint_URL = "https://project-codeiam-iam.eastus2.inference.ml.azure.com/score"
Swagger_URL = "https://project-codeiam-iam.eastus2.inference.ml.azure.com/swagger.json"
service_endpoint_key = "nGaqiz6lHpbPIvfmCM4gtWdAclggH4Xj"
SUBSCRIPTION_KEY = "7e23ef5547644534b78b21fc8c15aa7b"
REGION = "eastus2"
path_to_audio_file_or_audio_stream = "sentinels-main/testuser.wav"

app = Flask(__name__)
app.secret_key = "super secret key"

# Initialize the text-to-speech engine
engine = pyttsx3.init()
ai_number = 0

# Initialize the speech config for Azure Open AI speech service
speech_config = speechsdk.SpeechConfig(subscription=SUBSCRIPTION_KEY, region=REGION)

@app.route('/')
def index():
    return render_template('generate.html')

@app.route('/ping')
def index_ping():
    return ping(url)

# Function to generate a random number for AI-generated voice
def generate_random_number():
    return random.randint(1, 10000)

# Function to generate AI-generated voice using Azure Open AI speech service
def ai_voice(number):
    engine.setProperty('rate', 200)
    engine.say(f"Your number is {number}")
    engine.runAndWait()

# Function to recognize human voice using Azure Open AI speech service
async def recognize_human_voice():
    audio_input = speechsdk.AudioConfig(filename=path_to_audio_file_or_audio_stream)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)

    result = await speech_recognizer.recognize_once_async()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print(f"Recognized: {result.text}")
        return result.text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized")
        return None

# Function to recognize AI-generated voice using Azure Open AI speech service
async def recognize_ai_voice():
    audio_input = speechsdk.AudioConfig(filename=path_to_audio_file_or_audio_stream)
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_input)

    result = await speech_synthesizer.speak_text_async("This is an AI-generated voice.")

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("AI-generated voice recognized")
        return result.audio_data
    else:
        print("AI-generated voice not recognized")
        return None
    
@app.route('/voice/analyze', methods=['POST'])
def voiceanalyze():
    try:
        if request.method == 'POST':
            file = request.files[path_to_audio_file_or_audio_stream]
            content_type = file.content_type
            if content_type != "audio/wav":
                raise Response(response=json.dumps({"message": "Invalid file type. Please upload a .wav file."}), status=400, mimetype="application/json")

            # Check if the uploaded file is a valid .wav file
            if not file.filename.endswith('.wav'):
                raise Response(response=json.dumps({"message": "Invalid file type. Please upload a .wav file."}), status=400, mimetype="application/json")

            # Recognize human voice
            human_voice = asyncio.run(recognize_human_voice_analyze(file.read()))
            if human_voice is None:
                raise Response(response=json.dumps({"message": "No speech recognized"}), status=400, mimetype="application/json")

            # Recognize AI-generated voice
            ai_voice = asyncio.run(recognize_ai_voice_analyze(file.read()))
            if ai_voice is not None:
                data = {"message": "AI-generated voice detected", "text": ai_voice}
                return jsonify(data)

            pattern = r"expected pattern"

            if re.search(pattern, human_voice):
                # Proceed accordingly if the recognized text matches the expected pattern
                data = {"message": "Pattern matched", "text": human_voice}
                return jsonify(data)
            else:
                data = {"message": "Pattern not matched", "text": human_voice}
                return jsonify(data)
    except Exception as e:
        error_message = str(e)
        return jsonify({"error": error_message})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))