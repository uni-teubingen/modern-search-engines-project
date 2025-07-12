from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from crawler import crawl as start_crawl
import threading

app = Flask(__name__)
CORS(app)

@app.route("/api/search", methods=["GET"])
def search():
    query = request.args.get("q", "")

    dummy_results = [
        {
            "title": f"Ergebnis 1 zu '{query}'",
            "url": "https://www.tuebingen.de/",
            "snippet": "Dies ist ein Beispiel-Snippet für die Suchmaschine TüBing."
        },
        {
            "title": f"Ergebnis 2 zu '{query}'",
            "url": "https://www.tuebingen.de/tourismus",
            "snippet": "Noch ein weiteres tolles Suchergebnis zur Stadt Tübingen."
        },
        {
            "title": "Schloss Hohentübingen",
            "url": "https://www.schloss-tuebingen.de/",
            "snippet": "Besuchen Sie das Schloss Hohentübingen und genießen Sie die Aussicht."
        }
    ]

    return jsonify(dummy_results)

@app.route("/api/start-crawling", methods=["GET","POST"])
def start_crawling():
    thread = threading.Thread(target=start_crawl)
    thread.start()
    return jsonify({"status": "Crawling started"}), 202

app.run(host="0.0.0.0", port=5050)
