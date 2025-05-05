from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")
index_name = "professors"

def search_professors(query):
    body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["fullName^3", "department", "tags"]
            }
        },
        "size": 10
    }
    response = es.search(index=index_name, body=body)
    results = []
    for hit in response["hits"]["hits"]:
        src = hit["_source"]
        results.append({
            "fullName": src["fullName"],
            "department": src["department"],
            "avgRating": src["avgRating"],
            "tags": src.get("tags", []),
            "score": hit["_score"]
        })
    return results