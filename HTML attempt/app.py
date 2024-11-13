from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
from openai import OpenAI

app = Flask(__name__)
from secret import OPENAI_API_KEY
from config import CHATGPT_MESSAGES  # Import CHATGPT_MESSAGES from external config

client = OpenAI(api_key=OPENAI_API_KEY)

# Home route to render the main HTML page
@app.route('/')
def index():
    return render_template('index.html')

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

        # Debugging output
        print("Formatted Instructions:", formatted_instructions)

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
