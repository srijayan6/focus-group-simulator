import os
import json
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
from google import genai
from google.genai import types
from personas import PERSONAS, SYNTHESIS_INSTRUCTIONS

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("No API key found. Check that your .env file has GEMINI_API_KEY set.")

client = genai.Client(api_key=api_key)

app = Flask(__name__, static_folder="static", static_url_path="")


def call_gemini(system_instruction, user_text):
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=user_text,
        config=types.GenerateContentConfig(system_instruction=system_instruction)
    )
    return response.text.strip()


@app.route("/")
def home():
    return send_from_directory("static", "index.html")


@app.route("/api/run-focus-group", methods=["POST"])
def run_focus_group():
    data = request.get_json()
    concept = data.get("concept", "").strip()
    persona_ids = data.get("personas", [])

    if not concept:
        return jsonify({"error": "Missing concept"}), 400
    if len(persona_ids) < 3:
        return jsonify({"error": "Select at least 3 personas"}), 400

    chosen = [PERSONAS[pid] for pid in persona_ids if pid in PERSONAS]
    user_text = f'The idea being pitched: "{concept}"'

    # Fire all persona calls in parallel, not one after another
    with ThreadPoolExecutor(max_workers=len(chosen)) as executor:
        futures = {
            executor.submit(call_gemini, p["prompt"], user_text): p
            for p in chosen
        }
        reactions = []
        for future in futures:
            persona = futures[future]
            reaction_text = future.result()
            reactions.append({
                "id": persona["name"],
                "name": persona["name"],
                "tag": persona["tag"],
                "reaction": reaction_text
            })

    # Build the synthesis call from all reactions gathered above
    synth_input = f'The idea: "{concept}"\n\nIndependent reactions:\n' + "\n".join(
        f'- {r["name"]} ({r["tag"]}): {r["reaction"]}' for r in reactions
    )
    synth_raw = call_gemini(SYNTHESIS_INSTRUCTIONS, synth_input)

    try:
        cleaned = synth_raw.replace("```json", "").replace("```", "").strip()
        synthesis = json.loads(cleaned)
    except json.JSONDecodeError:
        synthesis = {"agreement": synth_raw, "tension": "", "blindSpot": ""}

    return jsonify({"reactions": reactions, "synthesis": synthesis})


if __name__ == "__main__":
    app.run(debug=True, port=5000)