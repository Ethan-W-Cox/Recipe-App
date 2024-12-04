from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QLabel, QPushButton, QLineEdit, QTextEdit, QVBoxLayout, QHBoxLayout, QScrollArea, QWidget, QSplitter
from PyQt5.QtGui import QIcon, QPalette, QColor
from PyQt5.QtCore import Qt

import tempfile
from pathlib import Path
import requests
import ctypes
from bs4 import BeautifulSoup
import pygame
from openai import OpenAI
from secret import OPENAI_API_KEY    
from config import CHATGPT_MESSAGES  # Import CHATGPT_MESSAGES from external config
import threading
import time
import sounddevice as sd
from scipy.io.wavfile import write
import whisper  # Import the local Whisper model

from titlebar import CustomTitleBar  # Import the custom title bar from the separate file

client = OpenAI(api_key=OPENAI_API_KEY)

# Constants
whisperModel = whisper.load_model("tiny")  # You can use "tiny", "base", "small", "medium", or "large"
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
        
        # Display the response in the GUI immediately
        conversation_text.append(f"\nUser:\n{user_question}\nResponse:\n{chatgpt_response}\n")

        # Generate audio from ChatGPT's response
        audio_path = generate_audio(chatgpt_response)
        
        # Play the audio after the text is displayed
        if audio_path:
            play_audio(audio_path)

def generate_audio(response_text):
    try:
        # Generate TTS from response
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=response_text
        )

        # Use a temporary file for the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio_file:
            temp_audio_path = Path(temp_audio_file.name)
            temp_audio_file.write(response.content)
        
        print(f"Audio saved to {temp_audio_path}")

        return temp_audio_path

    except Exception as e:
        print(f"Error generating audio: {str(e)}")
        return None

def play_audio(audio_path):
    def play():
        try:
            # Ensure pygame mixer is properly reset
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
                pygame.mixer.quit()

            # Reinitialize pygame mixer and play the audio
            pygame.mixer.init()
            pygame.mixer.music.load(str(audio_path))
            pygame.mixer.music.play()

            # Wait until the audio finishes playing
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)  # Wait in intervals of 10ms

            # Stop the mixer to release the file
            pygame.mixer.music.stop()
            pygame.mixer.quit()

            # Wait for a moment to ensure pygame releases the file handle
            time.sleep(0.1)

            # Clean up the temporary file after the audio is played
            audio_path.unlink()  # Remove the temporary file
            print(f"Temporary audio file {audio_path} deleted successfully")

        except Exception as e:
            print(f"Error playing audio: {str(e)}")

    # Use a separate thread to play the audio so that it doesn't block the GUI
    audio_thread = threading.Thread(target=play)
    audio_thread.start()

def toggle_record_audio():
    global is_recording, recording_thread

    if not is_recording:
        # Start recording
        record_button.setText("Stop Recording")
        is_recording = True
        recording_thread = threading.Thread(target=start_recording)
        recording_thread.start()
    else:
        # Stop recording
        record_button.setText("Record")
        is_recording = False  # This will allow the recording to stop

def start_recording():
    global is_recording, audio_data, fs

    fs = 48000  # Sample rate
    duration = 15  # Set a maximum duration to prevent runaway recording (15 seconds)
    input_device_index = 6  # Set the input device index (replace with your preferred input device)

    try:
        print("Recording...")
        audio_data = sd.rec(int(duration * fs), samplerate=fs, channels=2, dtype='int16', device=input_device_index)
        
        while is_recording:
            sd.sleep(100)  # Keep recording in 100 ms chunks until stopped

        # Stop recording after the user presses the button again
        sd.stop()  # Ensure recording stops properly
        print("Recording stopped.")

        write(AUDIO_FILE_PATH, fs, audio_data)  # Save the recorded audio to a WAV file
        print(f"Audio recorded and saved to {AUDIO_FILE_PATH}")

        # Transcribe the recorded audio and handle the response
        transcribe_audio_and_ask_question()

    except Exception as e:
        print(f"Error starting recording: {str(e)}")

def transcribe_audio_and_ask_question():
    """Transcribe the recorded audio file using the local Whisper model and send the question to ChatGPT."""
    try:
        # Load the Whisper model

        # Transcribe the audio file
        result = whisperModel.transcribe(audio="user_question.wav", fp16=False)
        transcription = result["text"]
        print(f"Transcription: {transcription}")

        # Send the transcribed text to ChatGPT
        chatgpt_response = send_user_input_to_chatgpt(transcription)

        # Display the transcription and response in the conversation text area
        conversation_text.append(f"\nUser (Voice Input):\n{transcription}\nChatGPT's Response:\n{chatgpt_response}\n")

        # Generate audio from ChatGPT's response
        audio_path = generate_audio(chatgpt_response)
        
        # Play the audio after the text is displayed
        if audio_path:
            play_audio(audio_path)

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
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    
    # Set dark mode palette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(45, 45, 45))  # Darker background
    palette.setColor(QPalette.WindowText, QColor(255, 255, 255))  # Light text color
    palette.setColor(QPalette.Base, QColor(30, 30, 30))  # Input fields background
    palette.setColor(QPalette.Text, QColor(255, 255, 255))  # Input fields text color
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))  # Light button text color
    app.setPalette(palette)

    # Stylesheet for rounded corners
    rounded_stylesheet = """
        QLineEdit, QTextEdit, QPushButton {
            border-radius: 10px;
            border: 1px solid #aaa;
            padding: 8px;
            color: #ffffff;  /* Text color */
            background-color: #333333;  /* Background color for better contrast */
        }
        QPushButton:hover {
            background-color: #666;
        }
        QPushButton:pressed {
            background-color: #888;
        }
    """

    app.setStyleSheet(rounded_stylesheet)

    # Main window setup
    window = QtWidgets.QWidget()
    window.setWindowTitle("YesChef")
    window.setWindowFlags(Qt.FramelessWindowHint)  # Remove default title bar
    window.setGeometry(100, 100, 1000, 750)

    # Main layout
    main_layout = QVBoxLayout()
    main_layout.setContentsMargins(20, 20, 20, 20)
    main_layout.setSpacing(10)  # Set spacing between elements
    
    # Custom Title Bar
    title_bar = CustomTitleBar(window)
    main_layout.addWidget(title_bar)

    # URL Entry and Parse Button at the top of the page
    url_layout = QHBoxLayout()
    url_layout.setContentsMargins(10, 10, 10, 10)  # Set margins for the URL layout (left, top, right, bottom)
    url_layout.setSpacing(10)  # Set spacing between the entry and button
    url_entry = QLineEdit()
    url_entry.setPlaceholderText("Enter Recipe URL")
    url_entry.setMinimumHeight(35)
    
    parse_button = QPushButton("Parse Recipe")
    parse_button.clicked.connect(display_recipe)
    url_layout.addWidget(url_entry)
    url_layout.addWidget(parse_button)

    main_layout.addLayout(url_layout)  # Add the URL entry layout to the main layout

    # Splitter to divide left and right sections
    splitter = QSplitter(QtCore.Qt.Horizontal)

    # Left layout for Ingredients
    ingredients_layout = QVBoxLayout()
    ingredients_text = QTextEdit()
    ingredients_text.setReadOnly(True)
    ingredients_text.setTextColor(QColor("white"))
    ingredients_text.setFontPointSize(20)
    ingredients_layout.addWidget(ingredients_text)
    left_widget = QWidget()
    left_widget.setLayout(ingredients_layout)

    # Right layout for ChatGPT interaction
    right_layout = QVBoxLayout()

    # Conversation Text
    conversation_text = QTextEdit()
    conversation_text.setReadOnly(True)
    conversation_text.setTextColor(QColor("white"))
    conversation_text.setFontPointSize(20)
    right_layout.addWidget(conversation_text)

    # Question Entry, Ask Button, and Record Button
    bottom_layout = QHBoxLayout()
    question_entry = QLineEdit()
    question_entry.setPlaceholderText("Ask ChatGPT a question about the recipe")
    ask_button = QPushButton("Ask")
    ask_button.clicked.connect(ask_question)  # Updated to call ask_question function
    record_button = QPushButton("Record")
    record_button.clicked.connect(toggle_record_audio)  # Toggle recording on button click
    bottom_layout.addWidget(question_entry)
    bottom_layout.addWidget(ask_button)
    bottom_layout.addWidget(record_button)

    right_layout.addLayout(bottom_layout)

    # Set splitter widgets
    right_widget = QWidget()
    right_widget.setLayout(right_layout)
    splitter.addWidget(left_widget)
    splitter.addWidget(right_widget)

    # Add splitter to main layout
    main_layout.addWidget(splitter)

    # Set main window layout
    window.setLayout(main_layout)
    window.show()

    app.exec_()

# Main loop
if __name__ == "__main__":
    create_gui()
