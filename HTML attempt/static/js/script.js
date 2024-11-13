async function fetchRecipe() {
    const url = document.getElementById("urlEntry").value;

    const response = await fetch('/get_recipe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url })
    });

    const data = await response.json();

    if (data.error) {
        alert(data.error);
    } else {
        document.getElementById("ingredientsText").value = "Ingredients:\n" + data.ingredients.join("\n");
        document.getElementById("instructionsText").value = "Instructions:\n" + data.instructions;  // Display instructions
    }
}

async function askQuestion() {
    const question = document.getElementById("questionEntry").value;

    const response = await fetch('/ask_question', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question })
    });

    const data = await response.json();

    if (data.error) {
        alert(data.error);
    } else {
        // Append question and response to conversation text area
        const conversationBox = document.getElementById("conversationText");
        conversationBox.value += `User: ${question}\nChatGPT: ${data.response}\n\n`;
        conversationBox.scrollTop = conversationBox.scrollHeight;  // Auto-scroll to the latest response
    }
}
