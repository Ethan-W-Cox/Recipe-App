# YesChef
**Your AI-powered recipe assistant for hassle-free cooking.**

## Project Description
YesChef simplifies your cooking experience by parsing online recipes, answering your questions, and setting timers for you - all hands-free. Users provide a URL to a recipe. This recipe is then parsed to remove any unnecessary content that is often contained in online recipes and return only the ingredients and instructions. The user can then type or speak any question about the recipe and the answer will be spoken back to them. This response is powered by OpenAI's speech-to-text, text-to-speech, and 4o models. YesChef streamlines the process of deciphering an online recipe page and provides helpful advice and answers during the cooking process, making you the Chef de Cuisine of your kitchen. 

## Key Features
1. **Recipe Parsing**: Extracts and formats only the essential ingredients and instructions from online recipes.
2. **Interactive Assistant**: Ask questions about your recipe through voice or text commands, and receive detailed written and spoken responses.
3. **Built-In Timer**: Set timers effortlessly with text, voice commands, or manual input.
4. **Hands-Free Voice Control**: Say "Hey Chef" to ask a question, followed by "I'm done" to ask a question hands-free.

## Setup
To use YesChef, follow these steps:

1. **Download the Files**: Download the project files to your desired directory.

2. **Install Dependencies**: Make sure you have Python installed, along with the required dependencies (`PyQt5`, `pygame`, `requests`, etc.). 

3. **Run the Application**:
- Open a terminal, navigate to the directory containing the files, and run:
  ```
  python main.py
  ```

## User Guide

### Recipe Parsing:
1. Enter a recipe URL into the input box.
2. Click "Parse Recipe."
3. View a clean, decluttered list of ingredients and instructions.

### Interactive Assistance:
- **Text**: Type your question in the input box, and press "Enter." Or click the "Ask" button.
- **Voice**: Click the "Record" button and speak your question. Click it again when you are finished speaking

### Setting Timers:
- **Text**: Type "Set a timer for 5 minutes" and press "Enter."
- **Voice**: Click "Record," and say, "Set a timer for 5 minutes." Click the record button again to finish. Alternatively, use the wake word as described below.

### Wake Words:
- Use **"Hey Chef"** to activate the assistant.
- Use **"I'm done"** to finish your request. 

---

## Troubleshooting

### Microphone Access:
- Ensure your browser has granted microphone permissions.
- If access is denied, check browser or system settings.

### Common Errors:
- **"API Key Missing"**: Ensure `secret.py` contains valid API keys.
- **Parsing Issues**: Make sure the recipe URL is publicly accessible.

