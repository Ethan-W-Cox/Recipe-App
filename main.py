import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import scrolledtext
import re



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
    
    ingredients_section = soup.find_all('li', class_='wprm-recipe-ingredient')
    instructions_section = soup.find_all('div', class_='wprm-recipe-instruction-text')

    ingredients = [ingredient.get_text().strip() for ingredient in ingredients_section]
    instructions_raw = [instruction.get_text(separator='\n').strip() for instruction in instructions_section]
    instructions_text = "\n".join(instructions_raw)
    
    instructions_text = re.sub(r'(?<!\n\n)(?=\d\.)', '\n', instructions_text)
    
    return ingredients, instructions_text

def display_recipe():
    url = url_entry.get()
    html = get_recipe_html(url)
    if html:
        ingredients, instructions = parse_recipe(html)
        result_text.delete(1.0, tk.END)

        if ingredients:
            result_text.insert(tk.END, "Ingredients:\n")
            result_text.insert(tk.END, "\n".join(ingredients))
        else:
            result_text.insert(tk.END, "No ingredients found.\n")

        if instructions:
            result_text.insert(tk.END, "\n\nInstructions:\n")
            result_text.insert(tk.END, instructions)
        else:
            result_text.insert(tk.END, "No instructions found.\n")
    else:
        result_text.insert(tk.END, "Failed to retrieve the recipe. Please check the URL and your internet connection.")

def send_sms():
    url = url_entry.get()
    html = get_recipe_html(url)
    if html:
        ingredients, instructions = parse_recipe(html)
        recipe_text = f"Ingredients:\n{'\n'.join(ingredients)}\n\nInstructions:\n{instructions}"
        

    else:
        print("Failed to retrieve the recipe. Cannot send SMS.")

def create_gui():
    global url_entry, result_text

    window = tk.Tk()
    window.title("Recipe Parser")

    url_label = tk.Label(window, text="Enter Recipe URL:")
    url_label.pack()

    url_entry = tk.Entry(window, width=50)
    url_entry.pack()

    parse_button = tk.Button(window, text="Parse Recipe", command=display_recipe)
    parse_button.pack()

    result_text = scrolledtext.ScrolledText(window, wrap=tk.WORD, width=60, height=20)
    result_text.pack()

    send_sms_button = tk.Button(window, text="Send Recipe to Phone", command=send_sms)
    send_sms_button.pack()

    window.mainloop()

if __name__ == "__main__":
    create_gui()
