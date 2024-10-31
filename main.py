from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QLabel, QPushButton, QLineEdit, QTextEdit, QVBoxLayout, QHBoxLayout, QScrollArea, QWidget
from PyQt5.QtGui import QIcon  # Import QIcon for setting the window icon
import requests
import ctypes
from bs4 import BeautifulSoup
from pathlib import Path
import pygame
import sounddevice as sd
from scipy.io.wavfile import write
from openai import OpenAI
from secret import OPENAI_API_KEY    
from config import CHATGPT_MESSAGES  # Import CHATGPT_MESSAGES from external config
import os
import threading

client = OpenAI(api_key=OPENAI_API_KEY)

# Constants
AUDIO_FILE_PATH = Path(__file__).parent / "user_question.wav"
is_recording = False  # Track recording state
recording_thread = None  # Reference to the recording thread

def get_recipe_html(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None

def parse_recipe(html):
    soup = BeautifulSoup(html, 'html.parser')
    ingredients = [i.get_text().strip() for i in soup.find_all('li', class_='wprm-recipe-ingredient')]
    instructions = "\n".join(i.get_text(separator='\n').strip() for i in soup.find_all('div', class_='wprm-recipe-instruction-text'))
    return ingredients, instructions

def send_user_input_to_chatgpt(user_input):
    CHATGPT_MESSAGES.append({"role": "user", "content": user_input})
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
        return f"Error with ChatGPT request: {str(e)}"

def ask_question():
    user_question = question_entry.text().strip()
    if user_question:
        question_entry.clear()
        chatgpt_response = send_user_input_to_chatgpt(user_question)
        
        # Display the response in the GUI
        conversation_text.append(f"\nUser:\n{user_question}\nResponse:\n{chatgpt_response}\n")

        # Generate audio from ChatGPT's response
        generate_and_play_audio(chatgpt_response)

def generate_and_play_audio(response_text):
    try:
        # Generate TTS from response
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=response_text
        )

        # Save the audio to a temporary file
        speech_file_path = Path(__file__).parent / "response.mp3"

        # Ensure pygame mixer is properly reset
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.quit()

        # Remove the existing file if it still exists (to prevent permission issues)
        if os.path.exists(speech_file_path):
            os.remove(speech_file_path)

        with open(speech_file_path, "wb") as audio_file:
            audio_file.write(response.content)
        print(f"Audio saved to {speech_file_path}")

        # Reinitialize pygame mixer and play the audio
        pygame.mixer.init()
        pygame.mixer.music.load(speech_file_path)
        pygame.mixer.music.play()

    except Exception as e:
        print(f"Error generating or playing audio: {str(e)}")

def toggle_record_audio():
    global is_recording, recording_thread

    if not is_recording:
        # Start recording
        record_button.setText("Stop Recording")
        recording_thread = threading.Thread(target=start_recording)
        recording_thread.start()
    else:
        # Stop recording
        record_button.setText("Record Voice Question")
        is_recording = False  # This will allow the recording to stop

def start_recording():
    global is_recording, audio_data, fs

    fs = 22050  # Sample rate
    duration = 60  # Set a maximum duration to prevent runaway recording (60 seconds)
    is_recording = True
    print("Recording...")

    audio_data = sd.rec(int(duration * fs), samplerate=fs, channels=2, dtype='int16')
    while is_recording:
        sd.sleep(100)  # Keep recording in 100 ms chunks until stopped

    # Stop recording after the user presses the button again
    print("Recording stopped.")
    write(AUDIO_FILE_PATH, fs, audio_data)  # Save the recorded audio to a WAV file
    print(f"Audio recorded and saved to {AUDIO_FILE_PATH}")

    # Transcribe the recorded audio and handle the response
    transcribe_audio_and_ask_question()

def transcribe_audio_and_ask_question():
    """Transcribe the recorded audio file and send the question to ChatGPT."""
    try:
        with open(AUDIO_FILE_PATH, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        print(f"Transcription: {transcription}")

        # Send the transcribed text to ChatGPT
        chatgpt_response = send_user_input_to_chatgpt(transcription)

        # Display the transcription and response in the conversation text area
        conversation_text.append(f"\nUser (Voice Input):\n{transcription}\nChatGPT's Response:\n{chatgpt_response}\n")

        # Generate and play audio of the response
        generate_and_play_audio(chatgpt_response)
    except Exception as e:
        print(f"Error transcribing audio: {str(e)}")

def display_recipe():
    url = url_entry.text()
    html = get_recipe_html(url)
    if html:
        ingredients, instructions = parse_recipe(html)
        ingredients_text.clear()

        if ingredients:
            ingredients_text.append("Ingredients:\n" + "\n".join(ingredients) + "\n\n")
        else:
            ingredients_text.append("No ingredients found.\n\n")
        
        # Send ingredients and instructions to ChatGPT for processing
        user_input = f"Ingredients:\n{', '.join(ingredients)}\n\nInstructions:\n{instructions}"
        chatgpt_response = send_user_input_to_chatgpt(user_input)
        
        # Insert ChatGPT's breakdown of the instructions
        ingredients_text.append(f"Instructions:\n{chatgpt_response}\n")
    else:
        conversation_text.append("Failed to retrieve the recipe. Please check the URL and your internet connection.\n")


# Function to set up the GUI
def create_gui():
    global url_entry, ingredients_text, conversation_text, question_entry, record_button

    app = QtWidgets.QApplication([])
    app.setWindowIcon(QIcon("recipe_book_icon.ico"))  # Set taskbar icon

    # Use ctypes to change the taskbar icon
    app_id = "com.example.recipeassistant"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id) # I don't understand this at all but it changes the icon in the taskbar so that's cool
    
    window = QtWidgets.QWidget()
    window.setWindowTitle("Recipe Parser and Cooking Assistant")
    window.setWindowIcon(QIcon("recipe_book_icon.ico"))  # Set window icon
    window.setGeometry(100, 100, 1000, 750)

    main_layout = QVBoxLayout()

    # URL Entry and Parse Button
    url_layout = QHBoxLayout()
    url_entry = QLineEdit()
    url_entry.setPlaceholderText("Enter Recipe URL")
    parse_button = QPushButton("Parse Recipe")
    parse_button.clicked.connect(display_recipe)
    url_layout.addWidget(url_entry)
    url_layout.addWidget(parse_button)

    main_layout.addLayout(url_layout)

    # Ingredients and Instructions Text
    ingredients_text = QTextEdit()
    ingredients_text.setReadOnly(True)
    main_layout.addWidget(ingredients_text)

    # Question Entry and Ask Button
    question_layout = QHBoxLayout()
    question_entry = QLineEdit()
    question_entry.setPlaceholderText("Ask ChatGPT a question about the recipe")
    ask_button = QPushButton("Ask")
    ask_button.clicked.connect(ask_question)
    question_layout.addWidget(question_entry)
    question_layout.addWidget(ask_button)

    main_layout.addLayout(question_layout)

    # Record Button
    record_button = QPushButton("Record Voice Question")
    record_button.clicked.connect(toggle_record_audio)
    main_layout.addWidget(record_button)

    # Conversation Text
    conversation_text = QTextEdit()
    conversation_text.setReadOnly(True)
    main_layout.addWidget(conversation_text)

    window.setLayout(main_layout)
    window.show()
    app.exec_()


# Main loop
if __name__ == "__main__":
    # Initialize pygame mixer once at the start of the program
    pygame.init()
    create_gui()
