import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load the GEMINI_API_KEY from your .env file
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("No API key found. Check that your .env file has GEMINI_API_KEY set.")

client = genai.Client(api_key=api_key)

system_instruction = (
    "You are a real person reacting honestly to a new product idea. "
    "You are budget-conscious and compare every price to cheaper alternatives you already know about. "
    "React in first person, 3-4 sentences, as if speaking out loud."
)

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="The idea being pitched: A $15/month app that plans weekly meals based on what's already in your fridge.",
    config=types.GenerateContentConfig(
        system_instruction=system_instruction
    )
)

print(response.text)