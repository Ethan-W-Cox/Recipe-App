from pathlib import Path
from openai import OpenAI
from secret import OPENAI_API_KEY
client = OpenAI(api_key = OPENAI_API_KEY)


speech_file_path = Path(__file__).parent / "test.mp3"
response = client.audio.speech.create(
  model="tts-1",
  voice="alloy",
  input="Donut Donut Donut Donut Donut Donut Donut Donut Donut"
)

# Write the audio content to a file
with open(speech_file_path, "wb") as audio_file:
    audio_file.write(response.content)

print(f"Audio saved to {speech_file_path}")