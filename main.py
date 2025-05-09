from flask import Flask, request, render_template, Response, jsonify, redirect, url_for
from src.elasticsearch.search_content import search_webpages
from src.config import es_config
from elasticsearch import Elasticsearch
from urllib.parse import unquote
import json
import os
import time

IDX_SEARCH_MAP = {
    "webpages_uiuc": "UIUC",
    "webpages_uiuc_grainger": "Grainger College",
    "webpages_uiuc_cs": "CS Department",
    "webpages_uiuc_ece": "ECE Department",
    "uiuc_professors": "Faculty"
}

app = Flask(__name__, 
    template_folder='static/templates',
    static_folder='static'
)

es = Elasticsearch(
    ["https://localhost:9200"], 
    basic_auth=("elastic", es_config.KEY),
    verify_certs=False,
    ssl_show_warn=False
)

def get_available_indices():
    """Get all available indices from Elasticsearch"""
    try:
        indices = es.indices.get_alias().keys()
        print(f"Available indices: {list(indices)}")  # Add debug info
        
        formatted_indices = {}
        for index in indices:
            if index.startswith('.'):
                continue
                
            if index in IDX_SEARCH_MAP:
                formatted_indices[index] = IDX_SEARCH_MAP[index]
            elif index.startswith("webpages_"):
                name = index.replace("webpages_", "").title()
                formatted_indices[index] = f"{name} Website"
            elif index == "uiuc_professors":
                formatted_indices[index] = "Faculty"
        return formatted_indices
    except Exception as e:
        print(f"Error getting indices: {str(e)}")
        return {}

INDICES = get_available_indices()
PAGE_SIZE = 15
PAGERANK_SCORES_FILE = os.path.join(os.path.dirname(__file__), "data", "pagerank", "pagerank_scores.json")
pagerank_scores = {}

def load_pagerank_scores():
    """Load PageRank scores from JSON file"""
    global pagerank_scores
    try:
        if os.path.exists(PAGERANK_SCORES_FILE):
            with open(PAGERANK_SCORES_FILE, "r", encoding="utf-8") as f:
                pagerank_scores = json.load(f)
            print(f"[INFO] Successfully loaded PageRank scores from {PAGERANK_SCORES_FILE}")
            print(f"[INFO] Loaded {len(pagerank_scores)} PageRank scores")
        else:
            print(f"[WARNING] PageRank scores file not found at {PAGERANK_SCORES_FILE}")
            pagerank_scores = {}
    except Exception as e:
        print(f"[ERROR] Failed to load PageRank scores: {str(e)}")
        pagerank_scores = {}

def get_pagerank_score(url):
    """Get PageRank score from Elasticsearch"""
    try:
        response = es.search(
            index="pagerank",
            body={
                "query": {
                    "term": {
                        "url": url
                    }
                },
                "_source": ["pagerank_score"]
            }
        )
        hits = response.get("hits", {}).get("hits", [])
        if hits:
            return hits[0]["_source"]["pagerank_score"]
        return 0.0
    except Exception as e:
        print(f"Error getting PageRank score: {str(e)}")
        return 0.0

@app.route("/autocomplete", methods=["GET"])
def autocomplete():
    """Handle autocomplete requests for search suggestions"""
    query_term = request.args.get("q", "").strip()
    if not query_term:
        return jsonify([])

    query_body = {
        "query": {"prefix": {"title": query_term}},
        "size": 10,
        "_source": ["title"],
    }

    response = es.search(index=list(INDICES), body=query_body)
    hits = response.get("hits", {}).get("hits", [])

    # Remove duplicate results
    suggestions = set()
    for hit in hits:
        if "title" in hit["_source"]:
            suggestions.add(hit["_source"]["title"])
    
    suggestions = list(suggestions)[:10]
    return jsonify(suggestions)

@app.route("/snapshot")
def snapshot():
    """Get cached snapshot of a webpage"""
    url = request.args.get("url")
    if not url:
        return "URL parameter is missing", 404

    decoded_url = unquote(url)
    query_body = {"query": {"term": {"url": decoded_url}}, "_source": ["raw_html"]}
    response = es.search(index=list(INDICES), body=query_body)
    hits_data = response.get("hits", {})
    hits = hits_data.get("hits", [])
    if hits:
        raw_html = hits[0]["_source"].get("raw_html", "No content available")
        return Response(raw_html, mimetype="text/html; charset=utf-8")
    else:
        return "No snapshot available for this URL", 404

def calculate_search_time(func):
    """Decorator to calculate search time"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        search_time = end_time - start_time
        if isinstance(result, dict):
            result['search_time'] = search_time
        return result
    return wrapper

@calculate_search_time
def standard_search(es, query_term, results_size=1000):
    """Perform standard search across all indices"""
    query_body = {
        "query": {
            "multi_match": {
                "query": query_term,
                "fields": ["title", "content", "anchor_texts"]
            }
        },
        "size": results_size
    }
    response = es.search(index=list(INDICES), body=query_body)
    return dict(response)

@calculate_search_time
def phrase_search(es, query_term, results_size=1000):
    """Perform phrase search for exact matches"""
    query_body = {
        "query": {"match_phrase": {"content": {"query": query_term, "slop": 0}}},
        "size": results_size,
    }
    response = es.search(index=list(INDICES), body=query_body)
    return dict(response)

@calculate_search_time
def index_search(es, query_term, target_indices, results_size=1000):
    """Search within specific indices"""
    query_body = {
        "query": {
            "multi_match": {
                "query": query_term,
                "fields": ["title", "content", "anchor_texts"],
            }
        },
        "size": results_size,
    }
    response = es.search(index=target_indices, body=query_body)
    return dict(response)

@calculate_search_time
def wildcard_search(es, query_term, results_size=1000):
    """Perform wildcard search with pattern matching"""
    query_body = {
        "query": {
            "query_string": {
                "query": query_term,
                "fields": ["title^3", "content^2", "anchor_texts"],
                "default_operator": "AND",
                "analyze_wildcard": True
            }
        },
        "size": results_size,
    }
    response = es.search(index=list(INDICES), body=query_body)
    return dict(response)

@calculate_search_time
def execute_search(es, query_body, indices):
    """Execute search and return results"""
    response = es.search(index=indices, body=query_body)
    return dict(response)

@app.route("/", methods=["GET"])
def home():
    """Render home page with search form"""
    global INDICES
    INDICES = get_available_indices()
    return render_template("search.html", message=None, indices=INDICES)

@app.route("/history")
def history():
    """Render search history page"""
    return render_template("history.html")

@app.route("/search", methods=["GET", "POST"])
def search():
    """Handle search requests and return results"""
    if request.method == "POST":
        query_term = request.form.get("q", "").strip()
        query_type = request.form.get("type", "standard")
        selected_indices = request.form.getlist("selected_indices")
    else:
        query_term = request.args.get("q", "").strip()
        query_type = request.args.get("type", "standard")
        selected_indices = request.args.getlist("selected_indices")

    page = int(request.args.get("page", 1))

    if not query_term:
        return render_template("search.html", message="Please enter a search term")

    start = (page - 1) * PAGE_SIZE

    # Base query structure with scoring
    query_body = {
        "track_scores": True,
        "query": {
            "function_score": {
                "query": {
                    "multi_match": {
                        "query": query_term,
                        "fields": ["title^3", "content^2", "anchor_texts"],
                        "type": "best_fields",
                        "tie_breaker": 0.3
                    }
                },
                "functions": [
                    {
                        "filter": {"match_all": {}},
                        "script_score": {
                            "script": {
                                "source": """
                                double es_score = _score;
                                double pagerank = 0.0;
                                
                                try {
                                    def pagerank_doc = doc['pagerank_score'];
                                    if (pagerank_doc != null) {
                                        pagerank = pagerank_doc.value;
                                    }
                                } catch (Exception e) {}
                                
                                double weighted_pr = pagerank * 100.0;
                                double final_score = (weighted_pr * 0.1 + es_score * 0.9);
                                
                                return final_score;
                                """
                            }
                        }
                    }
                ],
                "boost_mode": "replace"
            }
        },
        "size": PAGE_SIZE,
        "from": start
    }

    # Add collapse field only for non-professor searches
    if query_type != "professor":
        query_body["collapse"] = {
            "field": "url",
            "inner_hits": {
                "name": "most_relevant",
                "size": 1,
                "sort": [{"_score": "desc"}]
            }
        }

    # Execute search based on query type
    if query_type == "professor":
        # Professor search using professors index
        query_body["query"]["function_score"]["query"] = {
            "multi_match": {
                "query": query_term,
                "fields": ["fullName^3", "department^2"],
                "type": "best_fields",
                "tie_breaker": 0.3
            }
        }
        response = execute_search(es, query_body, ["uiuc_professors"])
    elif query_type == "index":
        if not selected_indices:
            return render_template("search.html", message="Please select at least one index")
        response = execute_search(es, query_body, selected_indices)
    elif query_type == "wildcard":
        query_body["query"]["function_score"]["query"] = {
            "query_string": {
                "query": query_term,
                "fields": ["title^3", "content^2", "anchor_texts"],
                "default_operator": "AND",
                "analyze_wildcard": True
            }
        }
        response = execute_search(es, query_body, list(INDICES))
    else:
        response = execute_search(es, query_body, list(INDICES))

    if not response:
        return render_template("search.html", message="Search error, please try again")

    hits_data = response.get("hits", {})
    total_data = hits_data.get("total", {})
    total_results = total_data.get("value", 0)
    hits = hits_data.get("hits", [])
    search_time = response.get('search_time', 0)

    # Calculate total pages and adjust if needed
    total_pages = (total_results + PAGE_SIZE - 1) // PAGE_SIZE
    if page > total_pages:
        page = total_pages
        start = (page - 1) * PAGE_SIZE
        # Re-execute search with corrected page number
        query_body["from"] = start
        response = execute_search(es, query_body, list(INDICES))
        hits_data = response.get("hits", {})
        hits = hits_data.get("hits", [])

    # Process results based on search type
    if query_type == "professor":
        # Check for duplicate professor names
        seen_names = set()
        results = []
        for hit in hits:
            name = hit["_source"].get("fullName", "")
            if name not in seen_names:
                seen_names.add(name)
                results.append({
                    "title": name,
                    "department": hit["_source"].get("department", ""),
                    "rating": hit["_source"].get("avgRating", 0.0),
                    "reviews": hit["_source"].get("numRatings", 0),
                    "difficulty": hit["_source"].get("avgDifficulty", 0.0),
                    "would_take_again": "No Data" if hit["_source"].get("wouldTakeAgainPercent", 0.0) == -1 
                                      else hit["_source"].get("wouldTakeAgainPercent", 0.0) / 100.0,
                    "final_score": hit["_score"],
                    "tags": hit["_source"].get("tags", [])
                })
    else:
        # Check for duplicate URLs
        seen_urls = set()
        results = []
        for hit in hits:
            url = hit["_source"].get("url", "")
            if url not in seen_urls:
                seen_urls.add(url)
                result = {
                    "title": hit["_source"].get("title", ""),
                    "url": url,
                    "relevance_score": hit["_score"],
                    "pagerank": pagerank_scores.get(url, 0.0),
                    "final_score": hit["_score"],
                    "snippet": hit["_source"].get("content", "")[:200] + "...",
                    "index": hit["_index"],
                    "index_name": INDICES.get(hit["_index"], hit["_index"])
                }
                pr_score = result["pagerank"]
                es_score = result["relevance_score"]
                weighted_pr = pr_score * 100.0
                result["final_score"] = (weighted_pr * 0.1 + es_score * 0.9)
                results.append(result)

    results.sort(key=lambda x: x["final_score"], reverse=True)

    # Select template based on search type
    template = "rmp_results.html" if query_type == "professor" else "results.html"

    return render_template(
        template,
        query=query_term,
        query_type=query_type,
        results=results,
        total_results=total_results,
        page=page,
        page_size=PAGE_SIZE,
        indices=INDICES,
        selected_indices=selected_indices,
        search_time=search_time
    )

@app.route("/api/search_content", methods=["GET"])
def search_content():
    """API endpoint for content search"""
    query = request.args.get("q")
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400
    results = search_webpages(query)
    return jsonify({"results": results})

@app.route("/api/indices", methods=["GET"])
def get_indices():
    """API endpoint to get available indices"""
    indices = get_available_indices()
    return jsonify(indices)

load_pagerank_scores()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
