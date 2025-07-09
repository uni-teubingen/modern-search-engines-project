from flask import Flask, jsonify, request
from flask_cors import CORS
from backend.db import init_db
import requests

init_db()
app = Flask(__name__)
CORS(app)

@app.route("/api/search/")
def search():
    query = request.args.get("q", "")

@app.route("/api/index/header")
def header():
    return jsonify({
        "text": "Das ist unser Modern Search Engine Projekt"
    })
app.run(host="0.0.0.0", port=5050)
