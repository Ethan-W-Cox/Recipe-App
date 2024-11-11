from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import openai

app = Flask(__name__)
from secret import OPENAI_API_KEY

# Initialize OpenAI API
openai.api_key = OPENAI_API_KEY

# Home route to render the main HTML page
@app.route('/')
def index():
    return render_template('index.html')

# Route to fetch and parse recipe ingredients and instructions
@app.route('/get_recipe', methods=['POST'])
def get_recipe():
    data = request.get_json()
    url = data.get('url')

    # Fetch the recipe HTML
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        return jsonify({"error": f"Error fetching URL: {str(e)}"}), 500

    # Parse the recipe ingredients and instructions
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        ingredients = [i.get_text().strip() for i in soup.find_all('li', class_='wprm-recipe-ingredient')]
        instructions = "\n".join(i.get_text(separator='\n').strip() for i in soup.find_all('div', class_='wprm-recipe-instruction-text'))
        
        return jsonify({
            "ingredients": ingredients,
            "instructions": instructions
        })

    except Exception as e:
        return jsonify({"error": f"Error parsing recipe: {str(e)}"}), 500

# Route to handle question sending to ChatGPT
@app.route('/ask_question', methods=['POST'])
def ask_question():
    data = request.get_json()
    question = data.get('question')

    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=question,
            max_tokens=150
        )
        answer = response.choices[0].text.strip()

        return jsonify({"response": answer})

    except Exception as e:
        return jsonify({"error": f"Error with ChatGPT request: {str(e)}"}), 500

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


if __name__ == '__main__':
    app.run(debug=True)
