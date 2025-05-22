# server.py
from flask import Flask, request, jsonify
import json
import os



app = Flask(__name__)
SCORE_FILE = "highscores.json"

from flask_cors import CORS
CORS(app)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)



# Highscores laden
def load_scores():
    if os.path.exists(SCORE_FILE):
        with open(SCORE_FILE, "r") as f:
            return json.load(f)
    return []

# Highscores speichern
def save_scores(scores):
    with open(SCORE_FILE, "w") as f:
        json.dump(scores, f, indent=2)

@app.route("/submit_score", methods=["POST"])
def submit_score():
    data = request.get_json()
    if not data or "name" not in data or "score" not in data:
        return jsonify({"error": "Invalid data"}), 400

    scores = load_scores()
    scores.append({"name": data["name"], "score": data["score"]})
    scores = sorted(scores, key=lambda x: x["score"], reverse=True)[:10]  # Top 10
    save_scores(scores)

    return jsonify({"status": "ok", "highscores": scores})

@app.route("/highscores", methods=["GET"])
def get_highscores():
    return jsonify(load_scores())

if __name__ == "__main__":
    app.run(debug=True)
