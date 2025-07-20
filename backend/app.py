from flask import Flask, jsonify, request
from flask_cors import CORS
import db
import crawler
import indexing
import threading

app = Flask(__name__)
CORS(app)
@app.route("/api/search", methods=["GET"])
def search():
    index = indexing.SearchEngine(db.DB_PATH)
    
    query= request.args.get("q", "")
    result  = index.search(query)
    return jsonify(result)

@app.route("/api/start-crawling", methods=["GET","POST"])
def start_crawling():
    database = db.Database(db.DB_PATH)
    database.drop_all()
    crl = crawler.Crawler()
    thread = threading.Thread(target=crl.start)
    thread.start()
    return jsonify({"status": "Crawling started"}), 202

@app.route("/api/health-check",methods=["GET"])
def health_check():
    return "",200


