from flask import Flask, request, render_template, Response, jsonify, redirect, url_for
from src.elasticsearch.search_content import search_webpages
from elasticsearch import Elasticsearch
from urllib.parse import unquote
import json
import os

app = Flask(__name__)

es = Elasticsearch(["http://localhost:9200"], verify_certs=False)
INDEX_NAME = "my_index"
PAGE_SIZE = 15

PAGERANK_SCORES_FILE = os.path.abspath("../pagerank/pagerank_scores.json")
pagerank_scores = {}


def load_pagerank_scores():
    global pagerank_scores
    if os.path.exists(PAGERANK_SCORES_FILE):
        with open(PAGERANK_SCORES_FILE, "r", encoding="utf-8") as f:
            pagerank_scores = json.load(f)
    else:
        print("Warning: pagerank_scores.json file not found")
        pagerank_scores = {}


def get_pagerank_score(url):
    return pagerank_scores.get(url, 0.0)


@app.route("/autocomplete", methods=["GET"])
def autocomplete():
    query_term = request.args.get("q", "").strip()
    if not query_term:
        return jsonify([])

    query_body = {
        "query": {"prefix": {"title": query_term}},
        "size": 10,
        "_source": ["title"],
    }

    response = es.search(index=INDEX_NAME, body=query_body)
    hits = response.get("hits", {}).get("hits", [])

    suggestions = [
        hit["_source"].get("title", "") for hit in hits if "title" in hit["_source"]
    ]
    return jsonify(suggestions)


@app.route("/snapshot")
def snapshot():
    url = request.args.get("url")
    if not url:
        return "URL parameter is missing", 404

    decoded_url = unquote(url)
    query_body = {"query": {"term": {"url": decoded_url}}, "_source": ["raw_html"]}
    response = es.search(index=INDEX_NAME, body=query_body)
    hits_data = response.get("hits", {})
    hits = hits_data.get("hits", [])
    if hits:
        raw_html = hits[0]["_source"].get("raw_html", "No content available")
        return Response(raw_html, mimetype="text/html; charset=utf-8")
    else:
        return "No snapshot available for this URL", 404


def standard_search(es, query_term, index_name, results_size=1000):
    query_body = {
        "query": {
            "function_score": {
                "query": {
                    "multi_match": {
                        "query": query_term,
                        "fields": ["title", "content", "anchor_texts"],
                    }
                },
                "field_value_factor": {
                    "field": "pagerank_score",
                    "factor": 1.0,
                    "modifier": "log1p",
                    "missing": 1,
                },
                "boost_mode": "sum",
            }
        },
        "size": results_size,
    }
    return es.search(index=index_name, body=query_body)


def phrase_search(es, query_term, index_name, results_size=1000):
    query_body = {
        "query": {"match_phrase": {"content": {"query": query_term, "slop": 0}}},
        "size": results_size,
    }
    return es.search(index=index_name, body=query_body)


def document_search(es, query_term, index_name, results_size=1000):
    response = standard_search(es, query_term, index_name)
    hits_data = response.get("hits", {})
    hits = hits_data.get("hits", [])
    filtered_hits = []
    for hit in hits:
        attachments = hit["_source"].get("attachments", [])
        if any(
            att.endswith(".pdf")
            or att.endswith(".docx")
            or att.endswith(".xlsx")
            or att.endswith(".doc")
            for att in attachments
        ):
            filtered_hits.append(hit)
    return {"hits": {"hits": filtered_hits}}


def wildcard_search(es, query_term, index_name, results_size=1000):
    query_body = {
        "query": {
            "query_string": {
                "query": f"*{query_term}*",
                "fields": ["title^3", "content^2", "anchor_texts"],
                "default_operator": "AND",
            }
        },
        "size": results_size,
    }
    return es.search(index=index_name, body=query_body)


@app.route("/", methods=["GET"])
def home():
    return render_template("search.html", message=None)


@app.route("/history")
def history():
    return render_template("history.html")


@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        query_term = request.form.get("q", "").strip()
        query_type = request.form.get("type", "standard")
    else:
        query_term = request.args.get("q", "").strip()
        query_type = request.args.get("type", "standard")

    page = int(request.args.get("page", 1))

    if not query_term:
        return render_template("search.html", message="Please enter a search term")

    start = (page - 1) * PAGE_SIZE

    if query_type == "document":
        response = document_search(es, query_term, INDEX_NAME)
    elif query_type == "wildcard":
        response = wildcard_search(es, query_term, INDEX_NAME)
    elif query_type == "phrase":
        response = phrase_search(es, query_term, INDEX_NAME)
    else:
        response = standard_search(es, query_term, INDEX_NAME)

    hits_data = response.get("hits", {})
    total_data = hits_data.get("total", {})
    total_results = total_data.get("value", 0)
    hits = hits_data.get("hits", [])

    alpha = 0.7
    beta = 0.3

    results = [
        {
            "title": hit["_source"].get("title", ""),
            "url": hit["_source"].get("url", ""),
            "score": hit["_score"],
            "pagerank": get_pagerank_score(hit["_source"].get("url", "")),
            "final_score": alpha * hit["_score"]
            + beta * get_pagerank_score(hit["_source"].get("url", "")),
            "snippet": hit["_source"].get("content", "")[:200] + "...",
        }
        for hit in hits
    ]

    results.sort(key=lambda x: x["final_score"], reverse=True)

    return render_template(
        "results.html",
        query=query_term,
        query_type=query_type,
        results=results,
        total_results=total_results,
        page=page,
        page_size=PAGE_SIZE,
    )


@app.route("/api/search_content", methods=["GET"])
def search_content():
    query = request.args.get("q")
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400
    results = search_webpages(query)
    return jsonify({"results": results})


load_pagerank_scores()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
