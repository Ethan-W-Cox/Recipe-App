import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import scrolledtext, ttk
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

def display_recipe():
    url = url_entry.get()
    html = get_recipe_html(url)
    if html:
        ingredients, instructions = parse_recipe(html)
        ingredients_text.config(state=tk.NORMAL)  # Enable editing to update content
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
        ingredients_text.config(state=tk.DISABLED)  # Make the content read-only again
    else:
        conversation_text.config(state=tk.NORMAL)  # Enable editing to update content
        conversation_text.insert(tk.END, "Failed to retrieve the recipe. Please check the URL and your internet connection.\n")
        conversation_text.config(state=tk.DISABLED)  # Make the content read-only again

def ask_question():
    user_question = question_entry.get().strip()
    if user_question:
        question_entry.delete(0, tk.END)
        chatgpt_response = send_user_input_to_chatgpt(user_question)
        conversation_text.config(state=tk.NORMAL)  # Enable editing to update content
        conversation_text.insert(tk.END, f"\nUser Question:\n{user_question}\nChatGPT's Response:\n{chatgpt_response}\n")
        conversation_text.config(state=tk.DISABLED)  # Make the content read-only again

def create_gui():
    global url_entry, ingredients_text, conversation_text, question_entry

    window = tk.Tk()
    window.title("Recipe Parser and Cooking Assistant")
    window.geometry("900x600")
    window.configure(bg="#f0f0f0")  # Set background color

    # Create a PanedWindow for a split layout
    paned_window = ttk.PanedWindow(window, orient=tk.HORIZONTAL)
    paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Left Frame for Ingredients and Instructions
    left_frame = ttk.Frame(paned_window, padding=10)
    paned_window.add(left_frame, weight=1)

    ttk.Label(left_frame, text="Enter Recipe URL:", font=("Helvetica", 12)).pack(anchor="w", pady=5)
    url_entry = ttk.Entry(left_frame, width=50, font=("Helvetica", 11))
    url_entry.pack(fill=tk.X, pady=5)

    ttk.Button(left_frame, text="Parse Recipe", command=display_recipe).pack(pady=10)

    ingredients_text = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, width=50, height=20, font=("Helvetica", 11))
    ingredients_text.pack(fill=tk.BOTH, expand=True)
    ingredients_text.config(state=tk.DISABLED)  # Make read-only initially

    # Right Frame for ChatGPT conversation
    right_frame = ttk.Frame(paned_window, padding=10)
    paned_window.add(right_frame, weight=1)

    ttk.Label(right_frame, text="Ask ChatGPT a question about the recipe:", font=("Helvetica", 12)).pack(anchor="w", pady=5)
    question_entry = ttk.Entry(right_frame, width=50, font=("Helvetica", 11))
    question_entry.pack(fill=tk.X, pady=5)
    ttk.Button(right_frame, text="Ask", command=ask_question).pack(pady=10)

    conversation_text = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, width=50, height=20, font=("Helvetica", 11))
    conversation_text.pack(fill=tk.BOTH, expand=True)
    conversation_text.config(state=tk.DISABLED)  # Make read-only initially

    window.mainloop()

if __name__ == "__main__":
    create_gui()
