# Testing speech to text

from openai import OpenAI
from secret import OPENAI_API_KEY
client = OpenAI(api_key=OPENAI_API_KEY)

audio_file = open("response.mp3", "rb")
transcription = client.audio.transcriptions.create(
  model="whisper-1", 
  file=audio_file, 
  response_format="text"
)
print(transcription)