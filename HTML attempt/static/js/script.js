let isRecording = false;
let mediaRecorder;
let audioChunks = [];
let timerInterval; // Holds the timer interval
let timerDisplay =  document.querySelector('.timer-display'); // Reference to display the timer in the title bar
let isPaused = false; // Tracks the pause state
let remainingTime = 0; // Tracks remaining time when paused

// Function to fetch and parse recipe from a URL
async function fetchRecipe() {
    const url = document.getElementById("urlEntry").value;

     // Clear the chat history whenever a recipe is parsed
     const conversationBox = document.getElementById("conversationText");
     conversationBox.value = ""; // Resets the chat history

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
        recordButton.classList.remove("inactive");
        recordButton.classList.add("active");

        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = event => audioChunks.push(event.data);
        mediaRecorder.start();
    } else {
        // Stop recording
        isRecording = false;
        recordButton.classList.remove("active");
        recordButton.classList.add("inactive");

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
        generateAudioForResponse(data.response);
    }
}

// allows user to press enter to submit instead of just the buttons
document.addEventListener('DOMContentLoaded', () => {
    // Set up "Enter" key event for URL entry
    const urlEntry = document.getElementById("urlEntry");
    urlEntry.addEventListener("keypress", function(event) {
        if (event.key === "Enter") {
            event.preventDefault(); // Prevents form submission if inside a form
            fetchRecipe();
        }
    });

    // Set up "Enter" key event for ChatGPT question entry
    const questionEntry = document.getElementById("questionEntry");
    questionEntry.addEventListener("keypress", function(event) {
        if (event.key === "Enter") {
            event.preventDefault(); // Prevents form submission if inside a form
            askQuestion();
            questionEntry.value = "";
        }
    });
});


// Function to open the timer popup
function openTimerPopup() {
    document.getElementById('timerBackdrop').style.display = 'flex';
}

// Function to close the timer popup
function closeTimerPopup() {
    document.getElementById('timerBackdrop').style.display = 'none';
}

// Function to start the timer and close the popup
function startTimer() {
    const hours = parseInt(document.getElementById('hoursInput').value) || 0;
    const minutes = parseInt(document.getElementById('minutesInput').value) || 0;
    const seconds = parseInt(document.getElementById('secondsInput').value) || 0;

    const totalSeconds = hours * 3600 + minutes * 60 + seconds;

    if (totalSeconds > 0) {
        updateTimerDisplay(totalSeconds); // Initialize display
        startCountdown(totalSeconds);
        
        // Reset to show pause icon and hide play icon
        const pauseIcon = document.getElementById('pauseIcon');
        const playIcon = document.getElementById('playIcon');
        pauseIcon.style.display = 'inline';
        playIcon.style.display = 'none';

        isPaused = false; // Ensure timer starts in running state

        // Show the pause and stop buttons
        document.getElementById('pauseButton').style.visibility = 'visible';
        document.getElementById('stopButton').style.visibility = 'visible';
    }

    closeTimerPopup(); // Close the popup after setting the timer
}



// Function to format and update the timer display
function updateTimerDisplay(timeLeft) {
    const hours = Math.floor(timeLeft / 3600);
    const minutes = Math.floor((timeLeft % 3600) / 60);
    const seconds = timeLeft % 60;
    timerDisplay.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

// Function to start a new timer with the specified duration
function startCountdown(duration) {
    // Clear any existing timer
    if (timerInterval) clearInterval(timerInterval);

    remainingTime = duration;
    isPaused = false; // Reset pause state
    updateTimerDisplay(remainingTime); // Update display immediately

    // Start a new countdown interval
    timerInterval = setInterval(() => {
        if (!isPaused) {
            remainingTime--;

            if (remainingTime < 0) {
                clearInterval(timerInterval);
                timerDisplay.textContent = "00:00:00"; // Reset display on timer end
            } else {
                updateTimerDisplay(remainingTime);
            }
        }
    }, 1000);
}

function togglePauseTimer() {
    isPaused = !isPaused; // Toggle pause state
    const pauseIcon = document.getElementById('pauseIcon');
    const playIcon = document.getElementById('playIcon');
    
    // Toggle visibility of play/pause icons
    if (isPaused) {
        // Show play icon (paused state)
        pauseIcon.style.display = 'none';
        playIcon.style.display = 'inline';
    } else {
        // Show pause icon (resumed state)
        pauseIcon.style.display = 'inline';
        playIcon.style.display = 'none';
    }
}

// Function to stop the timer and reset display
function stopTimer() {
    clearInterval(timerInterval);           // Clear the timer interval
    remainingTime = 0;                      // Reset the remaining time
    timerDisplay.textContent = "00:00:00";  // Reset the display to initial state

    // Reset to show pause icon and hide play icon
    document.getElementById('pauseIcon').style.display = 'inline';
    document.getElementById('playIcon').style.display = 'none';

    isPaused = false;                       // Reset pause state

    // Hide the pause and stop buttons
    document.getElementById('pauseButton').style.visibility = 'hidden';
    document.getElementById('stopButton').style.visibility = 'hidden';
}

// Initial setup: hide pause and stop buttons until a timer is started
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('pauseButton').style.visibility = 'hidden';
    document.getElementById('stopButton').style.visibility = 'hidden';
});

