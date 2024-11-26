let isRecording = false;
let mediaRecorder;
let audioChunks = [];
let timerInterval; // Holds the timer interval
let timerDisplay =  document.querySelector('.timer-display'); // Reference to display the timer in the title bar
let isPaused = false; // Tracks the pause state
let remainingTime = 0; // Tracks remaining time when paused

// Create a global audio object for the alarm
const alarmSound = new Audio('/static/audio/alarm.mp3');
alarmSound.loop = true; // Loop the alarm sound continuously

// Function to fetch and parse recipe from a URL
async function fetchRecipe() {
    const url = document.getElementById("urlEntry").value;

    // Get references to the text areas
    const ingredientsBox = document.getElementById("ingredientsText");
    const instructionsBox = document.getElementById("instructionsText");

    // Clear the chat history whenever a recipe is parsed
    const conversationBox = document.getElementById("conversationText");
    conversationBox.value = ""; // Resets the chat history

    // Remove any text currently in instructions/ingredients
    ingredientsBox.value = "";
    instructionsBox.value = "";

    // Add loading animation
    ingredientsBox.classList.add("loading");
    instructionsBox.classList.add("loading");

    try {
        const response = await fetch('/get_recipe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });

        const data = await response.json();

        if (data.error) {
            // Handle the error case
            alert(data.error);
        } else {
            // Populate the ingredients and instructions boxes
            ingredientsBox.value = data.ingredients;
            instructionsBox.value = data.instructions;
        }
    } catch (error) {
        console.error("Error fetching recipe:", error);
        alert("An unexpected error occurred while parsing the recipe.");
    } finally {
        // Remove the loading animation regardless of success or error
        ingredientsBox.classList.remove("loading");
        instructionsBox.classList.remove("loading");
    }
}


async function askQuestion() {
    const question = document.getElementById("questionEntry").value;

    if (!question.trim()) return; // Prevent empty messages

    const conversationBox = document.getElementById("conversationText");

    // Add user's message to the chatbox
    const userMessage = document.createElement("div");
    userMessage.className = "message user-message";
    userMessage.textContent = question; // Display just the question text
    conversationBox.appendChild(userMessage);

    // Clear the input field after submission
    document.getElementById("questionEntry").value = "";

    try {
        // Send the question to the server
        const response = await fetch('/ask_question', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: question })
        });

        const data = await response.json();

        // Add ChatGPT's response to the chatbox
        const chatMessage = document.createElement("div");
        chatMessage.className = "message chatgpt-message";

        if (data.error) {
            chatMessage.textContent = "Sorry, there was an error processing your request.";
        } else if (data.timer_duration) {
            // If a timer duration is returned, start the timer and display a message
            startCountdown(data.timer_duration);

            // Format and display the timer duration message
            const hours = Math.floor(data.timer_duration / 3600);
            const minutes = Math.floor((data.timer_duration % 3600) / 60);
            const seconds = data.timer_duration % 60;

            // Create a human-readable duration string
            const durationMessage = 
            `${hours > 0 ? `${hours} hour${hours > 1 ? 's' : ''} ` : ''}` +
            `${minutes > 0 ? `${minutes} minute${minutes > 1 ? 's' : ''} ` : ''}` +
            `${seconds > 0 ? `${seconds} second${seconds > 1 ? 's' : ''}` : ''}`;

            const timerMessage = `Timer started for ${durationMessage.trim()}.`;
            chatMessage.textContent = timerMessage;

            // Generate audio for the timer message
            generateAudioForResponse(timerMessage);
        } else if (data.response) {
            // Normal ChatGPT response
            chatMessage.textContent = data.response;
            generateAudioForResponse(data.response);
        } else {
            chatMessage.textContent = "Sorry, I couldn't understand that.";
        }

        conversationBox.appendChild(chatMessage);
    } catch (error) {
        // Handle errors in communication
        const errorMessage = document.createElement("div");
        errorMessage.className = "message chatgpt-message";
        errorMessage.textContent = "An error occurred while communicating with the server.";
        conversationBox.appendChild(errorMessage);
        console.error("Error:", error);
    }

    // Auto-scroll to the latest message
    conversationBox.scrollTop = conversationBox.scrollHeight;
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

            const audio = new Audio(audioUrl);
            await audio.play();

            audio.onended = () => {
                console.log("Audio playback finished.");
                URL.revokeObjectURL(audioUrl);
            };
        } else {
            // Log HTML error response if JSON parsing fails
            const errorText = await audioResponse.text();
            console.error("Error generating audio:", errorText);
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
        const transcription = data.transcription;

        // Display transcription in chatbox
        const conversationBox = document.getElementById("conversationText");
        conversationBox.value += `User: ${transcription}\n`;
        conversationBox.scrollTop = conversationBox.scrollHeight;

        // Send transcription to ChatGPT
        const response = await fetch('/ask_question', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: transcription })
        });

        const chatData = await response.json();

        if (chatData.timer_duration) {
            startCountdown(chatData.timer_duration);
        } else if (chatData.response) {
            conversationBox.value += `ChatGPT: ${chatData.response}\n\n`;

            // Trigger TTS for spoken responses
            generateAudioForResponse(chatData.response);
        } else {
            conversationBox.value += `ChatGPT: Sorry, I couldn't understand that.\n\n`;
        }
        conversationBox.scrollTop = conversationBox.scrollHeight;
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

    // Make the timer control buttons visible at the start
    document.getElementById('pauseButton').style.visibility = 'visible';
    document.getElementById('stopButton').style.visibility = 'visible';

    // Convert duration to hours, minutes, and seconds for a human-readable message
    const hours = Math.floor(duration / 3600);
    const minutes = Math.floor((duration % 3600) / 60);
    const seconds = duration % 60;
    let durationText = 'Timer started for ';

    // Construct the message
    if (hours > 0) durationText += `${hours} hour${hours > 1 ? 's' : ''} `;
    if (minutes > 0) durationText += `${minutes} minute${minutes > 1 ? 's' : ''} `;
    if (seconds > 0) durationText += `${seconds} second${seconds > 1 ? 's' : ''}.`;

    // Display the same message in the chat box and speak it
    const conversationBox = document.getElementById("conversationText");
    conversationBox.value += `${durationText}\n\n`;
    generateAudioForResponse(durationText); // Speak the message

    // Start a new countdown interval
    timerInterval = setInterval(() => {
        if (!isPaused) {
            remainingTime--;

            if (remainingTime < 0) {
                clearInterval(timerInterval);
                timerDisplay.textContent = "00:00:00"; // Reset display on timer end
                alarmSound.play();

                // Hide the pause button when the timer ends
                document.getElementById('pauseButton').style.visibility = 'hidden';
                //document.getElementById('stopButton').style.visibility = 'hidden';
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
    alarmSound.pause();

    // Hide the timer control buttons when the timer is stopped
    document.getElementById('pauseButton').style.visibility = 'hidden';
    document.getElementById('stopButton').style.visibility = 'hidden';

    isPaused = false;                       // Reset pause state
    document.getElementById('pauseIcon').style.display = 'inline'; // Show pause icon
    document.getElementById('playIcon').style.display = 'none';    // Hide play icon
}

// Initial setup: hide pause and stop buttons until a timer is started
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('pauseButton').style.visibility = 'hidden';
    document.getElementById('stopButton').style.visibility = 'hidden';
});

