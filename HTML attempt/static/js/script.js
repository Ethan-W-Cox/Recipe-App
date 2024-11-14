let isRecording = false;
let mediaRecorder;
let audioChunks = [];

// Function to fetch and parse recipe from a URL
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

// Function to send a question to ChatGPT and display the response
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

        // Generate audio for the response
        //generateAudioForResponse(data.response); // Uncomment to enable TTS playback
    }
}

// Function to request TTS audio from the server and play it
async function generateAudioForResponse(responseText) {
    try {
        const audioResponse = await fetch('/generate_audio', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: responseText })
        });

        if (audioResponse.ok) {
            const audioBlob = await audioResponse.blob();
            const audioUrl = URL.createObjectURL(audioBlob);

            console.log("Playing audio from URL:", audioUrl);

            // Play the audio using an HTML audio element
            const audio = new Audio(audioUrl);
            await audio.play();  // Await ensures any errors in playback are caught

            audio.onended = () => {
                console.log("Audio playback finished.");
                URL.revokeObjectURL(audioUrl);  // Clean up URL to release memory
            };
        } else {
            const errorData = await audioResponse.json();
            console.error("Error generating audio:", errorData);
        }
    } catch (error) {
        console.error("Error fetching audio:", error);
    }
}

// Function to toggle recording audio with the microphone
async function toggleRecording() {
    const recordButton = document.getElementById("recordButton");

    if (!isRecording) {
        // Start recording
        isRecording = true;
        recordButton.innerHTML = '<img src="mic_icon_active.png" alt="Stop Recording" width="20" height="20">';

        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = event => audioChunks.push(event.data);
        
        mediaRecorder.start();
    } else {
        // Stop recording
        isRecording = false;
        recordButton.innerHTML = '<img src="mic_icon.png" alt="Record" width="20" height="20">';

        mediaRecorder.stop();
        
        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            await sendAudioForTranscription(audioBlob);
        };
    }
}

// Function to send recorded audio to the server for transcription
async function sendAudioForTranscription(audioBlob) {
    const formData = new FormData();
    formData.append("audio", audioBlob);

    const response = await fetch('/transcribe_audio', {
        method: 'POST',
        body: formData
    });

    const data = await response.json();

    if (data.error) {
        alert(data.error);
    } else {
        // Send transcription to ChatGPT as if it was a regular text question
        askQuestionWithText(data.transcription);
    }
}

// Sends the transcribed text as if it were a regular text input
async function askQuestionWithText(text) {
    const response = await fetch('/ask_question', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: text })
    });

    const data = await response.json();

    if (data.error) {
        alert(data.error);
    } else {
        const conversationBox = document.getElementById("conversationText");
        conversationBox.value += `User: ${text}\nChatGPT: ${data.response}\n\n`;
        conversationBox.scrollTop = conversationBox.scrollHeight;

        // Uncomment to enable TTS playback for the response
        //generateAudioForResponse(data.response);
    }
}
