from flask import Flask, render_template, request, jsonify, send_file
import tempfile
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from pathlib import Path
import whisper
import threading
import pvporcupine
import pyaudio
import struct
import os

app = Flask(__name__)
from secret import OPENAI_API_KEY
from secret import PICOVOICE_ACCESS_KEY
from config import CHATGPT_MESSAGES  # Import CHATGPT_MESSAGES from external config

client = OpenAI(api_key=OPENAI_API_KEY)
whisperModel = whisper.load_model("tiny.en")

PORCUPINE_ACCESS_KEY = PICOVOICE_ACCESS_KEY
KEYWORD_PATH = ["HTML attempt/Hey-chef_en_windows_v3_0_0.ppn"]



def porcupine_listener():
    porcupine = pvporcupine.create(access_key=PORCUPINE_ACCESS_KEY, keyword_paths=KEYWORD_PATH)
    pa = pyaudio.PyAudio()
    previousAudio = ""
    audio_stream = pa.open(
                    rate=porcupine.sample_rate,
                    channels=1,
                    format=pyaudio.paInt16,
                    input=True,
                    frames_per_buffer=porcupine.frame_length)
    
    try:
        while True:
            keyword = audio_stream.read(porcupine.frame_length)
            keyword = struct.unpack_from("h" * porcupine.frame_length, keyword)
            keyword_index = porcupine.process(keyword)
            if keyword_index == 0 and keyword != previousAudio:
                print("Wake word detected!")
                previousAudio = keyword
                # Trigger a response or set a flag here
                # Example: Send a signal or update a variable for the Flask app to use
    finally:
        audio_stream.close()
        pa.terminate()
        porcupine.delete()

# Start the listener thread
listener_thread = threading.Thread(target=porcupine_listener)
listener_thread.daemon = True
listener_thread.start()


# Home route to render the main HTML page
@app.route('/')
def index():
    return render_template('index.html')


# Route to transcribe audio and send the transcription to ChatGPT
@app.route('/transcribe_audio', methods=['POST'])
def transcribe_audio():
    audio_file = request.files['audio']

    # Save the audio to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio_file:
        audio_file.save(temp_audio_file.name)
        audio_path = temp_audio_file.name

    # Transcribe the audio using Whisper
    try:
        result = whisperModel.transcribe(audio_path)
        transcription = result["text"]
        return jsonify({"transcription": transcription})
    except Exception as e:
        return jsonify({"error": f"Error transcribing audio: {str(e)}"}), 500


#Route to generate TTS audio
# @app.route('/generate_audio', methods=['POST'])
@app.route('/generate_audio', methods=['POST'])
def generate_audio():
    data = request.get_json()
    text = data.get('text')

    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text
        )

        # Write audio to a temporary file
        temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_audio_file.write(response.content)
        temp_audio_file.close()

        # Return the audio file directly
        return send_file(temp_audio_file.name, mimetype="audio/mpeg")

    except Exception as e:
        return jsonify({"error": f"Error generating audio: {str(e)}"}), 500






# Route to fetch and parse recipe ingredients and instructions
@app.route('/get_recipe', methods=['POST'])
def get_recipe():
    data = request.get_json()
    url = data.get('url')

    # Fetch the recipe HTML with headers
    response_text = get_recipe_html(url)
    if not response_text:
        return jsonify({"error": "Error fetching the recipe URL"}), 500

    # Parse the recipe ingredients and instructions
    try:
        soup = BeautifulSoup(response_text, 'html.parser')
        
        # Extract ingredients
        ingredients = [i.get_text().strip() for i in soup.find_all('li', class_='wprm-recipe-ingredient')]
        
        # Extract instructions with fallback for different classes
        instructions_raw = "\n".join(i.get_text(separator='\n').strip() for i in soup.find_all('div', class_='wprm-recipe-instruction-text'))
        if not instructions_raw:  # Fallback in case the specific class is not found
            instructions_raw = "\n".join(i.get_text(separator='\n').strip() for i in soup.find_all('p'))

        # Send instructions to ChatGPT for formatting using CHATGPT_MESSAGES
        formatted_instructions = format_instructions_with_chatgpt(instructions_raw)

        return jsonify({
            "ingredients": ingredients,
            "instructions": formatted_instructions
        })

    except Exception as e:
        return jsonify({"error": f"Error parsing recipe: {str(e)}"}), 500

# Route to handle question sending to ChatGPT
@app.route('/ask_question', methods=['POST'])
def ask_question():
    data = request.get_json()
    question = data.get('question')

    try:
        # Send question to ChatGPT with the configured message setup
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=CHATGPT_MESSAGES + [{"role": "user", "content": question}],
            max_tokens=2048
        )
        answer = response.choices[0].message.content.strip()

        # If the response is numeric, treat it as a timer duration
        if question.lower().find("timer") != -1 and answer.isdigit():
            numeric_value = int(answer)
            print(f"Numeric value for timer duration from ChatGPT: {numeric_value}")  # Print statement
            return jsonify({"timer_duration": numeric_value})

        # Otherwise, return the ChatGPT response as a regular answer
        return jsonify({"response": answer})
    
    except Exception as e:
        return jsonify({"error": f"Error with ChatGPT request: {str(e)}"}), 500





def get_recipe_html(url):
    # Use a session and headers to mimic a real browser request
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }
    try:
        response = session.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None

def format_instructions_with_chatgpt(instructions):

    print(instructions)
    CHATGPT_MESSAGES.append({"role": "user", "content": instructions})
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=CHATGPT_MESSAGES,
            max_tokens=2048
        )
        message = completion.choices[0].message
        CHATGPT_MESSAGES.append(message)
        return message.content
    except Exception as e:
        print(f"Error formatting instructions with ChatGPT: {e}")
        return instructions  # Fallback to raw instructions if there's an error 
    



if __name__ == '__main__':
    app.run(debug=True)
