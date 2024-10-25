import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import scrolledtext, ttk
from pathlib import Path
import pygame
from openai import OpenAI
from secret import OPENAI_API_KEY    
from config import CHATGPT_MESSAGES  # Import CHATGPT_MESSAGES from external config

client = OpenAI(api_key=OPENAI_API_KEY)

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
    user_question = question_entry.get().strip()
    if user_question:
        question_entry.delete(0, tk.END)
        chatgpt_response = send_user_input_to_chatgpt(user_question)
        
        # Display the response in the GUI
        conversation_text.config(state=tk.NORMAL)
        conversation_text.insert(tk.END, f"\nUser Question:\n{user_question}\nChatGPT's Response:\n{chatgpt_response}\n")
        conversation_text.config(state=tk.DISABLED)

        # Generate audio from ChatGPT's response
        generate_and_play_audio(chatgpt_response)

import os

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


def display_recipe():
    url = url_entry.get()
    html = get_recipe_html(url)
    if html:
        ingredients, instructions = parse_recipe(html)
        ingredients_text.config(state=tk.NORMAL)
        ingredients_text.delete(1.0, tk.END)

        if ingredients:
            ingredients_text.insert(tk.END, "Ingredients:\n" + "\n".join(ingredients) + "\n\n")
        else:
            ingredients_text.insert(tk.END, "No ingredients found.\n\n")
        
        # Send ingredients and instructions to ChatGPT for processing
        user_input = f"Ingredients:\n{'\n'.join(ingredients)}\n\nInstructions:\n{instructions}"
        chatgpt_response = send_user_input_to_chatgpt(user_input)
        
        # Insert ChatGPT's breakdown of the instructions
        ingredients_text.insert(tk.END, f"Instructions:\n{chatgpt_response}\n")
        ingredients_text.config(state=tk.DISABLED)
    else:
        conversation_text.config(state=tk.NORMAL)
        conversation_text.insert(tk.END, "Failed to retrieve the recipe. Please check the URL and your internet connection.\n")
        conversation_text.config(state=tk.DISABLED)

def create_gui():
    global url_entry, ingredients_text, conversation_text, question_entry

    window = tk.Tk()
    window.title("Recipe Parser and Cooking Assistant")
    window.geometry("1000x650")
    window.configure(bg="#f0f0f0")  # Light grey background

    style = ttk.Style()
    style.configure('TFrame', background='#f0f0f0')  # Match frame background to window
    style.configure('TLabel', background='#f0f0f0', font=('Helvetica', 12))
    style.configure('TButton', font=('Helvetica', 12), padding=6)

    # Create PanedWindow for layout
    paned_window = ttk.PanedWindow(window, orient=tk.HORIZONTAL)
    paned_window.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # Left Frame for Ingredients and Instructions
    left_frame = ttk.Frame(paned_window, padding=10)
    paned_window.add(left_frame, weight=1)

    ttk.Label(left_frame, text="Enter Recipe URL:").grid(row=0, column=0, sticky="w", pady=5)
    url_entry = ttk.Entry(left_frame, width=60, font=("Helvetica", 11))
    url_entry.grid(row=1, column=0, pady=5, sticky="ew")

    parse_button = tk.Button(left_frame, text="Parse Recipe", command=display_recipe,
                             font=("Helvetica", 12), relief=tk.RAISED)
    parse_button.grid(row=2, column=0, pady=10)

    ingredients_text = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, width=60, height=20,
                                                 font=("Helvetica", 11), relief=tk.GROOVE, bd=2)
    ingredients_text.grid(row=3, column=0, pady=10, sticky="nsew")
    ingredients_text.config(state=tk.DISABLED)

    # Right Frame for ChatGPT conversation
    right_frame = ttk.Frame(paned_window, padding=10)
    paned_window.add(right_frame, weight=1)

    ttk.Label(right_frame, text="Ask ChatGPT a question about the recipe:").grid(row=0, column=0, sticky="w", pady=5)
    question_entry = ttk.Entry(right_frame, width=60, font=("Helvetica", 11))
    question_entry.grid(row=1, column=0, pady=5, sticky="ew")

    ask_button = tk.Button(right_frame, text="Ask", command=ask_question,
                           font=("Helvetica", 12), relief=tk.RAISED)
    ask_button.grid(row=2, column=0, pady=10)

    conversation_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, width=60, height=20,
                                                  font=("Helvetica", 11), relief=tk.GROOVE, bd=2)
    conversation_text.grid(row=3, column=0, pady=10, sticky="nsew")
    conversation_text.config(state=tk.DISABLED)

    # Adjust column and row weights for better resizing
    left_frame.columnconfigure(0, weight=1)
    left_frame.rowconfigure(3, weight=1)
    right_frame.columnconfigure(0, weight=1)
    right_frame.rowconfigure(3, weight=1)

    window.mainloop()

if __name__ == "__main__":
    # Initialize pygame mixer once at the start of the program
    pygame.init()
    create_gui()
