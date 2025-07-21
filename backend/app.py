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
    pages_table = db.PageTable(database)
    pages_table.reset()
    crl = crawler.Crawler()
    thread = threading.Thread(target=crl.start)
    thread.start()
    return jsonify({"status": "Crawling started"}), 202

@app.route("/api/health-check",methods=["GET"])
def health_check():
    return "",200

@app.route("/api/performance-report",methods=["GET","POST"])
def performance_report():
    indexer = indexing.SearchEngine(db.DB_PATH)
    query= request.args.get("q", "")
    indexer.search(query,True)


@app.route("/api/start-indexing", methods=["GET","POST"])
def start_indexing():
    database = db.Database(db.DB_PATH)
    tf_table = db.TfTable(database)
    tf_table.reset()
    indexer = indexing.TFIDFIndexer(db.DB_PATH)
    indexer.compute_and_store()
    return jsonify({"status": "Indexing started"}), 202